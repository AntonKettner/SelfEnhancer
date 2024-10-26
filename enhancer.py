import os
import subprocess
import logging as lg
lg.basicConfig(level=lg.INFO, format="%(levelname)s: %(message)s")
import shutil
from dotenv import load_dotenv
from src.agent import CodeAgent
from src.controlling_agent import ControllingAgent
from src.tools import run_linters, run_formatter
from src.utils import commit_changes, compare_codebases
from termcolor import colored

load_dotenv()

def enhance():
    # Get the parent directory of the current project
    project_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create temporary directories
    temp_dir_name = "self_enhancer_temp"
    test_dir_name = "self_enhancer_test"
    temp_codebase_dir = os.path.join(project_parent_dir, temp_dir_name)
    test_codebase_dir = os.path.join(project_parent_dir, test_dir_name)
    
    # Remove the temporary directories if they already exist
    for dir_path in [temp_codebase_dir, test_codebase_dir]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    # Copy the entire codebase to the temporary directory
    original_dir = os.getcwd()
    shutil.copytree(original_dir, temp_codebase_dir, ignore=shutil.ignore_patterns('.git'))
    
    # Change working directory to the temporary codebase
    os.chdir(temp_codebase_dir)
    lg.info(f"Changed working directory to {temp_codebase_dir}")
    # list the files in the directory
    lg.info(f"Files in the directory: {os.listdir()}")

    # Initialize the agents
    code_agent = CodeAgent()
    controlling_agent = ControllingAgent()

    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            print(
                colored(f"\n--- Starting Enhancement Cycle {cycle_count} ---\n", "magenta")
            )

            # 0. Gather ideas for possible enhancements
            old_codebase = code_agent.get_current_codebase()
            enhancement_ideas = code_agent.generate_enhancement_ideas(old_codebase)

            # 1. Evaluate and rank ideas
            ranked_ideas = controlling_agent.evaluate_ideas(enhancement_ideas)

            if not ranked_ideas:
                print("No more improvements found. Exiting enhancement loop.")
                break
            
            print(colored(f"{len(ranked_ideas)} ranked ideas found:\n", "cyan"))
            for i, idea in enumerate(ranked_ideas):
                print(colored(f"{i+1}. {idea}\n", "cyan"))

            # Process each ranked idea
            for idea in ranked_ideas:

                # Ask if the user wants to implement the idea
                user_input = input(
                    colored(f"\nImplement improvement:\n\n{idea}? (y/n): ", "cyan")
                ).lower()
                if user_input != "y":
                    print("Skipping this idea.")
                    continue

                print(colored(f"\nImplementing idea: {idea}\n", "cyan"))

                # 2. Implement the idea
                implementation_steps = code_agent.plan_implementation(idea)
                for step in implementation_steps:
                    print(colored(f"\nImplementing step: {step}\n", "cyan"))
                    suggested_implementation = code_agent.suggest_implementation(step)
                    final_implementation = controlling_agent.review_step(step, suggested_implementation)
                    
                    # Apply the changes here
                    #! CURRENTLY CHANGES THE WRONG FILES -> in original codebase
                    code_agent._apply_changes(final_implementation)

            #! -------------implement Linting-------------

            #     # 3. Lint and format files
            #     issues = run_linters()
            #     formatted_code = run_formatter()

            #     if issues or formatted_code:
            #         code_agent.apply_linting_suggestions(issues, formatted_code)

            # if issues or formatted_code:

                # Display cost information
                total_input_tokens = code_agent.total_input_tokens + controlling_agent.total_input_tokens
                total_output_tokens = code_agent.total_output_tokens + controlling_agent.total_output_tokens
                total_tokens = total_input_tokens + total_output_tokens
                total_cost = code_agent.total_cost + controlling_agent.total_cost

                print(colored(f"\n--- Enhancement Idea Complete ---", "magenta"))
                print(colored(f"Total input tokens: {total_input_tokens}", "yellow"))
                print(colored(f"Total output tokens: {total_output_tokens}", "yellow"))
                print(colored(f"Total tokens used: {total_tokens}", "yellow"))
                print(colored(f"Total cost: ${total_cost:.4f}", "yellow"))


                # Commit changes to temp codebase
                new_codebase = code_agent.get_current_codebase()
                diff = compare_codebases(old_codebase, new_codebase)
                commit_message = f"Enhanced codebase with {idea}"
                commit_changes(commit_message)

                # Display changes and ask for approval
                print(colored("\nChanges made:", "yellow"))
                print(diff)

                while True:
                    user_input = input(colored("\nChoose an option (test/overwrite/discard): ", "cyan")).lower()
                    if user_input in ['test', 'overwrite', 'discard']:
                        break
                    print("Invalid option. Please choose 'test', 'overwrite', or 'discard'.")

                if user_input == 'test':
                    # Copy the temporary directory to the test directory
                    shutil.copytree(temp_codebase_dir, test_codebase_dir)
                    
                    # Copy .git from original directory to test directory
                    shutil.copytree(os.path.join(original_dir, '.git'), os.path.join(test_codebase_dir, '.git'))
                    
                    # Change to test directory and create/switch to 'enhanced' branch
                    os.chdir(test_codebase_dir)
                    # subprocess.run(["git", "checkout", "-b", "enhanced"])
                    
                    print(colored(f"Changes applied in a test directory: {test_codebase_dir}", "green"))
                    # print(colored("New 'enhanced' branch created in the test directory.", "green"))
                    
                    # Ask if user wants to make test directory the new home for future improvements
                    make_original = input(colored("Make test directory the new 'original_dir'? (y/n): ", "cyan")).lower() == 'y'
                    if make_original:
                        shutil.rmtree(original_dir)
                        shutil.copytree(test_codebase_dir, original_dir)
                        print(colored("Test directory is now the new original.", "green"))
                    
                    # Change back to temp directory for further enhancements
                    os.chdir(temp_codebase_dir)

                elif user_input == 'overwrite':
                    # Copy the temporary directory back to the original location
                    shutil.rmtree(original_dir)
                    shutil.copytree(temp_codebase_dir, original_dir)
                    print(colored("Changes applied to the original codebase.", "green"))

                else:  # discard
                    print(colored("Changes discarded.", "red"))
                    # Revert changes in the temporary directory
                    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=temp_codebase_dir)

                # Update old_codebase for the next iteration
                old_codebase = code_agent.get_current_codebase()

                # Ask if the user wants to continue with the next idea or start a new cycle
                user_input = input(colored("\nContinue with the next idea/cycle? (y/n): ", "cyan")).lower()
                if user_input != "y":
                    print("Exiting enhancement loop.")
                    break

    finally:
        # Change back to the original directory
        os.chdir(original_dir)
        
        # Optionally, you can keep the temp directory for inspection
        # If you want to remove it, uncomment the following line:
        # shutil.rmtree(temp_codebase_dir)

    print(colored("\n--- Enhancement Process Completed ---", "magenta"))
    print(colored(f"Total enhancement cycles: {cycle_count}", "yellow"))
    print(colored(f"Final total cost: ${total_cost:.4f}", "yellow"))
    print(colored(f"Temporary codebase location: {temp_codebase_dir}", "cyan"))
    if os.path.exists(test_codebase_dir):
        print(colored(f"Test codebase location: {test_codebase_dir}", "cyan"))

if __name__ == "__main__":
    enhance()
