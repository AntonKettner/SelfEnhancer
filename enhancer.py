import os
import subprocess
from dotenv import load_dotenv
from src.agent import CodeAgent
from src.tools import run_linters, run_formatter
from src.utils import commit_changes

load_dotenv()


def enhance():
    # Initialize the agent
    agent = CodeAgent()

    # Run self-assessment via external tools
    issues = run_linters()
    formatted_code = run_formatter()

    # Generate an improvement plan
    if issues or formatted_code:
        agent.write_plan(issues, formatted_code)

        # Use LLMs to generate suggestions and improvements
        agent.consult_llm()

        # Implement improvements based on feedback
        agent.apply_suggestions()

        # Commit the changes
        commit_changes("Self-enhancement: Code improvements and formatting")

        # Optionally, push to a remote repository
        subprocess.run(["git", "push"])


if __name__ == "__main__":
    enhance()
