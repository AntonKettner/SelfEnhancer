import sys
from io import StringIO
import os
from threading import Thread
import queue
import traceback
from app_src.config import get_api_key

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

def capture_output(queue, upload_path, app):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    output_capture = OutputCapture(queue)
    sys.stdout = output_capture
    sys.stderr = output_capture

    try:
        # Create application context for database access
        with app.app_context():
            # Set OpenAI API key from database
            api_key = get_api_key()
            if not api_key:
                queue.put("Error: OpenAI API key not configured")
                return

            os.environ['OPENAI_API_KEY'] = api_key
            os.environ['DATA_PATH'] = upload_path
            
            queue.put("Initializing Enhancement process...\n")
            from enhancer import Enhancement
            enhancement = Enhancement()
            
            queue.put("Generating improvement ideas...\n")
            enhancement.ideas, enhancement.usage = enhancement.generate_improvement_ideas()
            
            # Format the output
            output = "\nIDEAS FOR CODEBASE ENHANCEMENT:\n\n"
            for index, idea in enumerate(enhancement.ideas):
                output += f"{index+1}: {idea}\n\n"
            output += f"\nAPI Usage:\n{enhancement.usage}"
            
            queue.put(output)

    except Exception as e:
        error_msg = f"Error: {str(e)}\n"
        error_msg += f"Traceback:\n{traceback.format_exc()}\n"
        queue.put(error_msg)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        output_capture.flush()
