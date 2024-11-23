import os
import subprocess
import logging as lg
lg.basicConfig(level=lg.INFO, format="%(levelname)s: %(message)s")
import shutil
from dotenv import load_dotenv
from src.agent import EnhancementAgent
from src.tools import run_linters, run_formatter
from src.utils import commit_changes, compare_codebases
from termcolor import colored

load_dotenv()

def main():
    out = enhance()
    
    try:
        # Change back to the original directory
        os.chdir(out["original_dir"])
        
        print(colored("\n--- Enhancement Process Completed ---", "magenta"))
        print(colored(f"Total enhancement cycles: {out['cycle_count']}", "yellow"))
        print(colored(f"Final total cost: ${out['total_cost']:.4f}", "yellow"))
        print(colored(f"Temporary codebase location: {out['temp_codebase_dir']}", "cyan"))
        if os.path.exists(out['test_codebase_dir']):
            print(colored(f"Test codebase location: {out['test_codebase_dir']}", "cyan"))
    except Exception as e:
        if out == False:
            print(colored("Exiting without implementing any changes.", "red"))
        else:
            lg.error(f"Error in main: {e}")
def enhance():
    # Get the parent directory of the current project
    project_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create temporary directories
    temp_dir_name = "SelfEnhancer_temp"
    test_dir_name = "SelfEnhancer_test"
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
    lg.info(f"Files in the directory: {os.listdir()}")

    # Initialize the agent
    agent = EnhancementAgent()

    cycle_count = 0
    while True:
        cycle_count += 1
        print(colored(f"\n--- Starting Enhancement Cycle {cycle_count} ---\n", "magenta"))

        # 0. Gather ideas for possible enhancements
        old_codebase = agent.get_current_codebase()
        enhancement_ideas = agent.generate_enhancement_ideas(old_codebase)

        # 1. Evaluate and rank ideas
        ranked_ideas = agent.evaluate_ideas(enhancement_ideas)

        if not ranked_ideas:
            print("No more improvements found. Exiting enhancement loop.")
            break
        
        print(colored(f"{len(ranked_ideas)} ranked ideas found:\n", "yellow"))
        for i, idea in enumerate(ranked_ideas):
            print(colored(f"{i+1}. {idea}\n", "yellow"))

        # Process each ranked idea
        for i, idea in enumerate(ranked_ideas):
            user_input = input(colored(f"\nShould I implement improvement idea No {i+1} of {len(ranked_ideas)}:\n\n {idea} \n\n (y/n): ", "cyan")).lower()
            if user_input != "y":
                print("Skipping this idea.")
                continue

            print(colored(f"\nIMPLEMENTING IDEA", "cyan"))

            # 2. Implement the idea
            implementation_steps = agent.plan_implementation(idea)
            step_count = 0
            size_surrounding_code = 5
            already_applied_changes = []
            while step_count < len(implementation_steps):
                step_count += 1
                old_codebase = agent.get_current_codebase()
                step = implementation_steps[step_count - 1]
                print(colored(f"\nImplementing step: {step}\n", "cyan"))
                suggested_implementation = agent.suggest_implementation(step, already_applied_changes)
                final_implementation = agent.review_step(step, suggested_implementation, already_applied_changes)

                print(colored(f"\n Changes for step {step}:\n\n {final_implementation} \n\n", "cyan"))
                user_input = input(colored(f"\nShould I apply the changes (y), reload the implementation (r), discard (d) or exit (e)? ", "cyan")).lower()
                if user_input == "y":
                    agent._apply_changes(final_implementation)
                    already_applied_changes.append(final_implementation)
                elif user_input == "r":
                    print(colored(f"\nReloading implementation for step {step}\n", "red"))
                    step_count -= 1
                elif user_input == "e":
                    print("Exiting implementation loop.")
                    return False
                else:
                    print("Discarding changes.")


        # Display cost information
        total_tokens = agent.total_input_tokens + agent.total_output_tokens
        total_cost = agent.total_cost

        print(colored(f"\n--- Enhancement Idea Complete ---", "magenta"))
        print(colored(f"Total input tokens: {agent.total_input_tokens}", "yellow"))
        print(colored(f"Total output tokens: {agent.total_output_tokens}", "yellow"))
        print(colored(f"Total tokens used: {total_tokens}", "yellow"))
        print(colored(f"Total cost: ${total_cost:.4f}", "yellow"))

        # Commit changes to temp codebase
        new_codebase = agent.get_current_codebase()
        diff = compare_codebases(old_codebase, new_codebase)
        commit_message = f"Enhanced codebase with {idea}"
        commit_changes(commit_message)

        # Display changes and ask for approval
        print(colored("\nChanges made:", "yellow"))
        print(diff)

        while True:
            user_input = input(colored(f"\nDo you want to test (t) the changes currently in\n\n{temp_codebase_dir}\n\ninside of\n\n{test_codebase_dir}\n\n, overwrite the original codebase (o), discard (d) or exit (e)? ", "cyan")).lower()
            if user_input == "e":
                print("Exiting implementation loop.")
                return False

            if user_input in ['t', 'o', 'd', 'e']:
                break
            print("Invalid option. Please choose 't', 'o', 'd' or 'e'.")

        if user_input == 't':
            # Copy the temporary directory to the test directory
            shutil.copytree(temp_codebase_dir, test_codebase_dir)
            
            # Copy .git from original directory to test directory
            shutil.copytree(os.path.join(original_dir, '.git'), os.path.join(test_codebase_dir, '.git'))
            
            # Change to test directory and create/switch to 'enhanced' branch
            os.chdir(test_codebase_dir)
            
            print(colored(f"Changes applied in a test directory: {test_codebase_dir}", "green"))
            
            # Ask if user wants to make test directory the new home for future improvements
            make_original = input(colored("Make test directory the new 'original_dir'? (y/n): ", "cyan")).lower() == 'y'
            if make_original:
                shutil.rmtree(original_dir)
                shutil.copytree(test_codebase_dir, original_dir)
                print(colored("Test directory is now the new original.", "green"))
            
            # Change back to temp directory for further enhancements
            os.chdir(temp_codebase_dir)

        elif user_input == 'o':
            # Copy the temporary directory back to the original location
            shutil.rmtree(original_dir)
            shutil.copytree(temp_codebase_dir, original_dir)
            print(colored("Changes applied to the original codebase.", "green"))

        elif user_input == 'd':
            print(colored("Changes discarded.", "red"))
            # Revert changes in the temporary directory
            subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=temp_codebase_dir)
        else: #'e'
            print("Exiting enhancement loop.")
            return False

        # Update old_codebase for the next iteration
        old_codebase = agent.get_current_codebase()

        # Ask if the user wants to continue with the next idea or start a new cycle
        user_input = input(colored("\nContinue finding new ideas? (y/n): ", "cyan")).lower()
        if user_input != "y":
            print("Exiting enhancement loop.")
            break

    out = {
        "cycle_count": cycle_count,
        "total_cost": total_cost,
        "original_dir": original_dir,
        "temp_codebase_dir": temp_codebase_dir,
        "test_codebase_dir": test_codebase_dir,
    }
    return out

if __name__ == "__main__":
    enhance()
