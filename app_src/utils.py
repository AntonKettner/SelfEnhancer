import sys
from io import StringIO
import os
import shutil
import time
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
        if "\n" in text:
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
        # Get metrics from app context
        metrics = app.extensions["prometheus_metrics"]
        api_latency = metrics.histogram(
            "openai_api_latency_seconds",
            "Time spent waiting for OpenAI API",
            buckets=[0.5, 1, 2, 5, 10, 30, 60],
        )
        api_errors = metrics.counter("openai_api_errors", "Number of OpenAI API errors")

        api_key = get_api_key()
        if not api_key:
            queue.put("Error: OpenAI API key not configured")
            api_errors.inc()
            return

        os.environ["OPENAI_API_KEY"] = api_key
        queue.put("Initializing Enhancement process...\n")

        try:
            enhancement = Enhancement()
            queue.put("Generating improvement ideas...\n")

            # Measure API latency
            start_time = time.time()
            try:
                enhancement.ideas, enhancement.usage = enhancement.generate_improvement_ideas()
                api_latency.observe(time.time() - start_time)
            except Exception as e:
                api_errors.inc()
                raise

            output = "\nIDEAS FOR CODEBASE ENHANCEMENT:\n\n"
            for index, idea in enumerate(enhancement.ideas):
                output += f"{index+1}: {idea}\n\n"
            output += f"\nAPI Usage:\n{enhancement.usage}"
            queue.put(output)

        except Exception as e:
            error_msg = f"Error in enhancement process: {str(e)}\n"
            queue.put(error_msg)
            import traceback

            trace = traceback.format_exc()
            queue.put(f"Traceback:\n{trace}\n")

            # Send error to Sentry if available
            if "sentry_sdk" in sys.modules:
                import sentry_sdk

                sentry_sdk.capture_exception(e)

            raise  # Re-raise to trigger error metrics in routes.py

        finally:
            # Clean up the temporary upload directory
            upload_dir = os.environ.get("DATA_PATH")
            if upload_dir and os.path.exists(upload_dir):
                try:
                    shutil.rmtree(upload_dir)
                except Exception as e:
                    cleanup_error = f"Error cleaning up upload directory: {str(e)}\n"
                    queue.put(cleanup_error)
                    if "sentry_sdk" in sys.modules:
                        import sentry_sdk

                        sentry_sdk.capture_message(cleanup_error, level="error")

    except Exception as e:
        error_msg = f"Error in output capture: {str(e)}\n"
        queue.put(error_msg)
        import traceback

        trace = traceback.format_exc()
        queue.put(f"Traceback:\n{trace}\n")

        # Send error to Sentry if available
        if "sentry_sdk" in sys.modules:
            import sentry_sdk

            sentry_sdk.capture_exception(e)

        raise  # Re-raise to trigger error metrics in routes.py

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        output_capture.flush()


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
