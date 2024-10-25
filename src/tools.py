import subprocess


def run_linters():
    # Example with flake8
    result = subprocess.run(["flake8", "--statistics"], capture_output=True, text=True)
    return result.stdout


def run_formatter():
    # Example with black
    result = subprocess.run(["black", "."], capture_output=True, text=True)
    return result.stdout if "reformatted" in result.stdout else None
