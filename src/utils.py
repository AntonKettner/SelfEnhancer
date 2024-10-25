import subprocess


def commit_changes(message):
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", message])
