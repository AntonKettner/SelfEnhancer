from flask import Blueprint, render_template, request, jsonify, Response, redirect, url_for, current_app
from flask_login import login_required, current_user
import os
import tempfile
from werkzeug.utils import secure_filename
import zipfile
from threading import Thread
import queue
from .auth import get_api_key
from .utils import capture_output, allowed_file
from config.settings import UPLOADS_PATH

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    api_key = get_api_key()
    return render_template('dashboard.html', 
                         is_admin=current_user.is_admin,
                         api_key_configured=bool(api_key))

@main_bp.route('/upload-codebase', methods=['POST'])
@login_required
def upload_codebase():
    if 'codebase' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['codebase']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, {'zip', 'py', 'txt', 'md'}):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Create a unique temporary directory for this upload
        temp_dir = tempfile.mkdtemp(dir=UPLOADS_PATH)
        filename = secure_filename(file.filename)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        # If it's a zip file, extract it
        if filename.endswith('.zip'):
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            os.environ['DATA_PATH'] = extract_dir
        else:
            # For single files, use the temp directory as DATA_PATH
            os.environ['DATA_PATH'] = temp_dir

        return jsonify({'message': 'File uploaded successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/run-enhancement')
@login_required
def run_enhancement():
    def generate():
        output_queue = queue.Queue()
        thread = Thread(target=capture_output, args=(output_queue, current_app._get_current_object()))
        thread.start()
        
        while True:
            try:
                output = output_queue.get(timeout=1)
                if not output.endswith('\n'):
                    output += '\n'
                yield f"data: {output}\n\n"
            except queue.Empty:
                if not thread.is_alive():
                    break
                yield "data: Processing...\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
