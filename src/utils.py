import subprocess
import difflib
import json
from termcolor import colored


def commit_changes(message):
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", message])


def compare_codebases(old_codebase, new_codebase):
    diff = []
    for file_path in set(old_codebase.keys()) | set(new_codebase.keys()):
        old_content = old_codebase.get(file_path, '')
        new_content = new_codebase.get(file_path, '')
        
        if old_content != new_content:
            file_diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                n=3
            )
            diff.extend(file_diff)
    
    return ''.join(diff)


def calculate_cost(input_tokens, output_tokens, model):
    # Updated pricing as of the latest information
    prices = {
        "gpt-3.5-turbo": {
            "input": 0.0015 / 1000,   # $0.0015 per 1K input tokens
            "output": 0.002 / 1000,   # $0.002 per 1K output tokens
        },
        "gpt-4": {
            "input": 0.03 / 1000,     # $0.03 per 1K input tokens
            "output": 0.06 / 1000,    # $0.06 per 1K output tokens
        },
        "gpt-4-32k": {
            "input": 0.06 / 1000,     # $0.06 per 1K input tokens
            "output": 0.12 / 1000,    # $0.12 per 1K output tokens
        },
        "gpt-4-1106-preview": {
            "input": 0.01 / 1000,     # $0.01 per 1K input tokens
            "output": 0.03 / 1000,    # $0.03 per 1K output tokens
        },
        "gpt-4-vision-preview": {
            "input": 0.01 / 1000,     # $0.01 per 1K input tokens
            "output": 0.03 / 1000,    # $0.03 per 1K output tokens
        },
        "gpt-4o-mini": {
            "input": 0.15 / 1000000,     # $0.01 per 1M input tokens
            "output": 0.6 / 1000000,    # $0.03 per 1M output tokens
        },
    }
    
    if model not in prices:
        raise ValueError(f"Unknown model: {model}")
    
    input_cost = input_tokens * prices[model]["input"]
    output_cost = output_tokens * prices[model]["output"]
    return input_cost + output_cost


def pretty_print_conversation(messages):
    for message in messages:
        role = message["role"]
        content = message["content"]

        if role == "system":
            print(colored(f"System: {content}", "yellow"))
        elif role == "user":
            print(colored(f"User: {content}", "green"))
        elif role == "assistant":
            print(colored(f"Assistant: {content}", "cyan"))
        else:
            print(colored(f"{role.capitalize()}: {content}", "white"))
        
        print()  # Add a blank line for readability
