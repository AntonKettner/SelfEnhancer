from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    Response,
    redirect,
    url_for,
    current_app,
)
from flask_login import login_required, current_user
import os
import tempfile
from werkzeug.utils import secure_filename
import zipfile
from threading import Thread, Event
import queue
import time
from .auth import get_api_key
from .utils import capture_output, allowed_file
from config.settings import UPLOADS_PATH

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    from flask import session

    api_key = get_api_key()
    return render_template(
        "dashboard.html",
        is_admin=current_user.is_admin,
        api_key_configured=bool(api_key) or session.get("is_test_user", False),
    )


@main_bp.route("/upload-codebase", methods=["POST"])
@login_required
def upload_codebase():
    from flask import session

    if "codebase" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # Handle test user API key
    if session.get("is_test_user"):
        api_key = request.form.get("api_key")
        if not api_key:
            return jsonify({"error": "API key is required for test users"}), 400
        session["test_api_key"] = api_key  # Store API key in session

    file = request.files["codebase"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, {"zip", "py", "txt", "md"}):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        # Create a unique temporary directory for this upload
        temp_dir = tempfile.mkdtemp(dir=UPLOADS_PATH)
        filename = secure_filename(file.filename)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        # If it's a zip file, extract it
        if filename.endswith(".zip"):
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            os.environ["DATA_PATH"] = extract_dir
        else:
            # For single files, use the temp directory as DATA_PATH
            os.environ["DATA_PATH"] = temp_dir

        return jsonify({"message": "File uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/run-enhancement")
@login_required
def run_enhancement():
    from flask import copy_current_request_context

    output_queue = queue.Queue()
    done_event = Event()
    start_time = time.time()
    error_occurred = False

    # Get app before entering the thread
    app = current_app._get_current_object()

    # Initialize metrics variables
    metrics_enabled = False
    enhancement_total = None
    enhancement_errors = None
    enhancement_duration = None

    # Safely get metrics if available
    try:
        if hasattr(app, "extensions") and "prometheus_metrics" in app.extensions:
            metrics = app.extensions["prometheus_metrics"]
            enhancement_total = metrics.counter("enhancement_total")
            enhancement_errors = metrics.counter("enhancement_errors")
            enhancement_duration = metrics.histogram("enhancement_duration_seconds")
            enhancement_total.inc()
            metrics_enabled = True
    except Exception as e:
        # Log metrics error but continue processing
        print(f"Metrics initialization error: {str(e)}")
        metrics_enabled = False

    @copy_current_request_context
    def process_enhancement():
        nonlocal error_occurred
        try:
            capture_output(output_queue, app)
        except Exception as e:
            error_occurred = True
            if metrics:
                enhancement_errors.inc()
            raise
        finally:
            done_event.set()
            if metrics:
                duration = time.time() - start_time
                enhancement_duration.observe(duration)

    def generate():
        # Start processing in a thread
        thread = Thread(target=process_enhancement)
        thread.daemon = True
        thread.start()

        try:
            while not done_event.is_set() or not output_queue.empty():
                try:
                    output = output_queue.get(timeout=0.1)
                    if output:
                        if not output.endswith("\n"):
                            output += "\n"
                        yield f"data: {output}\n\n"
                except queue.Empty:
                    yield "data: Processing...\n\n"
                    time.sleep(0.1)

            # Final check for any remaining messages
            while not output_queue.empty():
                try:
                    output = output_queue.get_nowait()
                    if output:
                        if not output.endswith("\n"):
                            output += "\n"
                        yield f"data: {output}\n\n"
                except queue.Empty:
                    break

        except Exception as e:
            if metrics:
                enhancement_errors.inc()
            yield f"data: Error: {str(e)}\n\n"

    # Use stream_with_context to maintain request context
    from flask import stream_with_context

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
