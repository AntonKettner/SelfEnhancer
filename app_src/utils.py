import sys
from io import StringIO
import os
import shutil
from threading import Thread
import queue
from .auth import get_api_key
from enhancer import Enhancement

class OutputCapture:
    def __init__(self, queue):
        self.queue = queue
        self.buffer = StringIO()

    def write(self, text):
        self.buffer.write(text)
        if '\n' in text:
            self.flush()

    def flush(self):
        text = self.buffer.getvalue()
        if text:
            self.queue.put(text)
            self.buffer = StringIO()

def capture_output(queue, app):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    output_capture = OutputCapture(queue)
    sys.stdout = output_capture
    sys.stderr = output_capture

    try:
        with app.app_context():
            api_key = get_api_key()
            if not api_key:
                queue.put("Error: OpenAI API key not configured")
                return

            os.environ['OPENAI_API_KEY'] = api_key
            
            queue.put("Initializing Enhancement process...\n")
            enhancement = Enhancement()
            
            queue.put("Generating improvement ideas...\n")
            enhancement.ideas, enhancement.usage = enhancement.generate_improvement_ideas()
            
            output = "\nIDEAS FOR CODEBASE ENHANCEMENT:\n\n"
            for index, idea in enumerate(enhancement.ideas):
                output += f"{index+1}: {idea}\n\n"
            output += f"\nAPI Usage:\n{enhancement.usage}"
            
            queue.put(output)

            # Clean up the temporary upload directory
            upload_dir = os.environ.get('DATA_PATH')
            if upload_dir and os.path.exists(upload_dir):
                try:
                    shutil.rmtree(upload_dir)
                except Exception as e:
                    print(f"Error cleaning up upload directory: {e}")

    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\n"
        error_msg += f"Traceback:\n{traceback.format_exc()}\n"
        queue.put(error_msg)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        output_capture.flush()

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
