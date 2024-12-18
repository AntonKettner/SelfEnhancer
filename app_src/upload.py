from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
import shutil
import tempfile
import zipfile
from app_src.config import allowed_file

upload = Blueprint('upload', __name__)

@upload.route('/upload-codebase', methods=['POST'])
@login_required
def upload_codebase():
    if 'codebase' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['codebase']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Create a unique temporary directory for this upload
        upload_folder = current_app.config['UPLOAD_FOLDER']
        temp_dir = tempfile.mkdtemp(dir=upload_folder)
        filename = secure_filename(file.filename)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        # If it's a zip file, extract it
        if filename.endswith('.zip'):
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            upload_path = extract_dir
        else:
            upload_path = temp_dir

        # Store the upload path in the session for cleanup later
        session['upload_path'] = upload_path
        return jsonify({'message': 'File uploaded successfully'}), 200

    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500
