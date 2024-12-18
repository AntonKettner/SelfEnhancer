from flask import Blueprint, Response, session, current_app
from flask_login import login_required
import os
import shutil
import queue
from threading import Thread
from app_src.utils import capture_output

enhancement = Blueprint('enhancement', __name__)

@enhancement.route('/run-enhancement')
@login_required
def run_enhancement():
    upload_path = session.get('upload_path')
    if not upload_path:
        return Response("data: Error: No uploaded files found\n\n", mimetype='text/event-stream')

    def generate():
        output_queue = queue.Queue()
        thread = Thread(target=capture_output, args=(output_queue, upload_path, current_app))
        thread.start()
        
        try:
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
        finally:
            # Only clean up after the enhancement process is complete
            if os.path.exists(upload_path):
                parent_dir = os.path.dirname(upload_path)
                if parent_dir.startswith(current_app.config['UPLOAD_FOLDER']):
                    shutil.rmtree(parent_dir)
            session.pop('upload_path', None)
    
    return Response(generate(), mimetype='text/event-stream')
