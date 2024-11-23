import os
import time
import glob
from dotenv import load_dotenv
from openai import OpenAI
from termcolor import colored
from src.utils import calculate_cost, pretty_print_conversation
from data.prompts import *

def call_agent(client, messages, model="gpt-4o-mini", max_tokens=1000):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens
    )

    pretty_print_conversation([{"role": "assistant", "content": response.choices[0].message.content}])

    return response.choices[0].message.content, response.usage

class EnhancementAgent:
    def __init__(self, base_dir=None):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0
        self.base_dir = base_dir or os.getcwd()

    def get_current_codebase(self):
        codebase = {}
        for extension in ['*.py', '*.txt', '*.md']:
            for file_path in glob.glob(os.path.join(self.base_dir, "**", extension), recursive=True):
                # print(file_path)
                # time.sleep(1)
                with open(file_path, "r") as file:
                    content = file.read()
                    numbered_content = f"FILE:{os.path.relpath(file_path, self.base_dir)}\n"
                    for i, line in enumerate(content.split("\n"), 1):
                        numbered_content += f":{i}:{line}\n"
                    codebase[os.path.relpath(file_path, self.base_dir)] = numbered_content
        return codebase

    def process_codebase(self, codebase):
        prompt = ""
        for file_path, content in codebase.items():
            truncated_content = self._truncate_content(content)
            prompt += f"File: {file_path}\n{truncated_content}\n\n"
        return prompt

    def generate_enhancement_ideas(self, codebase):
        processed_codebase = self.process_codebase(codebase)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": GENERATE_IDEAS_PROMPT.format(codebase=processed_codebase)}
        ]

        pretty_print_conversation(messages)
        content, usage = call_agent(self.client, messages)
        self._update_usage(usage)
        return content

    def evaluate_ideas(self, ideas):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": EVALUATE_IDEAS_PROMPT.format(ideas=ideas)}
        ]

        pretty_print_conversation(messages)
        content, usage = call_agent(self.client, messages)
        self._update_usage(usage)
        return self._parse_best_idea(content)

    def plan_implementation(self, idea):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": PLAN_IMPLEMENTATION_PROMPT.format(idea=idea)}
        ]

        pretty_print_conversation(messages)
        content, usage = call_agent(self.client, messages)
        self._update_usage(usage)
        return self._parse_implementation_steps(content)

    def suggest_implementation(self, step, applied_changes):
        codebase = self.get_current_codebase()
        processed_codebase = self.process_codebase(codebase)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_IMPLEMENTER.format(
                step=step,
                applied_changes=applied_changes
            )},
            {"role": "user", "content": USER_IMPLEMENTATION_PROMPT.format(codebase=processed_codebase, step=step)}
        ]

        pretty_print_conversation(messages)
        content, usage = call_agent(self.client, messages, max_tokens=4096)
        self._update_usage(usage)
        return content

    def review_step(self, step, implementation, applied_changes):
        max_loop_count = 5
        loop_count = 0
        review_history = []

        while loop_count < max_loop_count:
            loop_count += 1
            
            messages = [
                {"role": "system", "content": REVIEW_SYSTEM_PROMPT.format(
                    step=step,
                    loop_count=loop_count,
                    max_loop_count=max_loop_count,
                    review_history=self._format_review_history(review_history),
                    instructions=SYSTEM_PROMPT_IMPLEMENTER.format(step=step, applied_changes=applied_changes)
                )},
                {"role": "user", "content": f"IMPLEMENTATION TO REVIEW:\n{implementation}"}
            ]

            pretty_print_conversation(messages)
            review, usage = call_agent(self.client, messages, max_tokens=4096)
            self._update_usage(usage)

            if review.strip().lower() == 'true':
                print(f"Implementation satisfactory after {loop_count} iterations.")
                return implementation

            review_history.append(review)
            implementation = self._apply_suggestions(implementation, review)

        print(f"Maximum iterations ({max_loop_count}) reached. Returning last implementation.")
        return implementation

    def _apply_suggestions(self, implementation, review):
        messages = [
            {"role": "system", "content": APPLY_SUGGESTIONS_SYSTEM_PROMPT},
            {"role": "user", "content": APPLY_SUGGESTIONS_USER_PROMPT.format(implementation=implementation, review=review)}
        ]

        pretty_print_conversation(messages)
        content, usage = call_agent(self.client, messages, max_tokens=4096)
        self._update_usage(usage)
        return content

    def _apply_changes(self, changes):
        """Apply changes to files based on the formatted change instructions."""
        current_file = None
        current_changes = []
        
        # Parse the changes string into a structured format
        for line in changes.strip().split('\n'):
            if line.startswith('FILE:'):
                if current_file and current_changes:
                    self._execute_file_changes(current_file, current_changes)
                current_file = line.replace('FILE:', '').strip()
                current_changes = []
            elif line.startswith(('CHANGE:', 'ADD:', 'DELETE:')):
                if current_file is None:
                    continue
                current_changes.append(line)
        
        # Apply any remaining changes
        if current_file and current_changes:
            self._execute_file_changes(current_file, current_changes)

    def _execute_file_changes(self, file_path, changes):
        """Execute the parsed changes for a specific file."""
        full_path = os.path.join(self.base_dir, file_path)
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Read existing file or create empty file
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                lines = f.readlines()
        else:
            print(colored(f"Creating new file: {full_path}", "green"))
            lines = []
        
        # Process each change
        for change in changes:
            try:
                action, line_info, content = change.split(':', 2)
                content = content.strip()
                
                if '-' in line_info:
                    # Range of lines
                    start, end = map(int, line_info.split('-'))
                else:
                    # Single line
                    start = end = int(line_info)
                
                if action == 'DELETE' or (action == 'CHANGE' and not content):
                    # Remove the specified lines
                    while end >= start and end > 0 and start <= len(lines):
                        if start - 1 < len(lines):
                            lines.pop(start - 1)
                        end -= 1
                
                elif action == 'CHANGE':
                    # Replace the specified lines
                    new_lines = [line + '\n' for line in content.split('\n')]
                    if start <= len(lines):
                        lines[start-1:end] = new_lines
                    else:
                        # Extend lines if needed
                        lines.extend([''] * (start - len(lines) - 1))
                        lines.extend(new_lines)
                
                elif action == 'ADD':
                    # Insert new lines at the specified position
                    new_lines = [line + '\n' for line in content.split('\n')]
                    if start <= len(lines):
                        lines[start-1:start-1] = new_lines
                    else:
                        # Extend lines if needed
                        lines.extend([''] * (start - len(lines) - 1))
                        lines.extend(new_lines)
            
            except Exception as e:
                print(colored(f"Error processing change '{change}': {str(e)}", "red"))
                continue
        
        # Write the modified content back to the file
        try:
            with open(full_path, 'w') as f:
                f.writelines(lines)
            print(colored(f"Successfully applied changes to {file_path}", "green"))
        except Exception as e:
            print(colored(f"Error writing to {file_path}: {str(e)}", "red"))

    def _parse_best_idea(self, evaluation):
        ranked_ideas = []
        remaining_eval = evaluation

        for i in range(1, 10):  # Assuming we won't have more than 9 ranked ideas
            start = remaining_eval.find(f"{i}.")
            if start == -1:
                break

            next_idea = remaining_eval.find(f"{i+1}.")
            if next_idea == -1:
                idea = remaining_eval[start:].strip()
            else:
                idea = remaining_eval[start:next_idea].strip()

            ranked_ideas.append(idea)
            remaining_eval = remaining_eval[next_idea:]

        return ranked_ideas

    def _parse_implementation_steps(self, implementation_plan):
        steps = []
        remaining_plan = implementation_plan

        for i in range(1, 20):  # Assuming we won't have more than 19 steps
            start = remaining_plan.find(f"{i}.")
            if start == -1:
                break

            next_step = remaining_plan.find(f"{i+1}.")
            if next_step == -1:
                step = remaining_plan[start:].strip()
            else:
                step = remaining_plan[start:next_step].strip()

            steps.append(step)
            remaining_plan = remaining_plan[next_step:]

        return steps

    def _format_review_history(self, review_history):
        if not review_history:
            return "No previous reviews."
        return "\n\n".join([f"Review {i+1}:\n{review}" for i, review in enumerate(review_history)])

    def _update_usage(self, usage):
        self.total_input_tokens += usage.prompt_tokens
        self.total_output_tokens += usage.completion_tokens
        self.total_cost += calculate_cost(usage.prompt_tokens, usage.completion_tokens, "gpt-4o-mini")

    def _truncate_content(self, content, max_lines=10, max_chars=500):
        lines = content.split('\n')
        if len(lines) > max_lines:
            truncated_lines = lines[:max_lines]
            truncated_lines.append("... (content truncated)")
        else:
            truncated_lines = lines

        truncated_content = '\n'.join(truncated_lines)
        if len(truncated_content) > max_chars:
            truncated_content = truncated_content[:max_chars] + "... (content truncated)"

        return truncated_content
