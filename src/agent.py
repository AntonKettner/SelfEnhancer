import os
import glob
import time
from dotenv import load_dotenv
from openai import OpenAI
from data.prompts import IMPROVEMENT_PROMPT
import json
from termcolor import colored
from src.utils import calculate_cost, pretty_print_conversation


class CodeAgent:
    def __init__(self, base_dir=None):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.plan = None
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0
        self.base_dir = base_dir or os.getcwd()

    def write_plan(self, issues, formatted_code):
        self.plan = IMPROVEMENT_PROMPT.format(
            issues=issues, formatted_code=formatted_code
        )

    def apply_suggestions(self):
        with open(__file__, "a") as f:
            f.write(self.suggestions)

    def get_current_codebase(self):
        codebase = {}
        for file_path in glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True):
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
            prompt += f"File: {file_path}\n{content}\n\n"
        return prompt

    def generate_enhancement_ideas(self, codebase):
        base_prompt = (
            "Analyze the following codebase and suggest 3 potential enhancements:\n\n"
        )

        processed_codebase = self.process_codebase(codebase)

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides code improvement ideas.",
            },
            {"role": "user", "content": base_prompt + processed_codebase},
        ]

        pretty_print_conversation(messages)

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=1000
        )

        pretty_print_conversation(
            [{"role": "assistant", "content": response.choices[0].message.content}]
        )

        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        self.total_cost += calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            "gpt-3.5-turbo",
        )

        return response.choices[0].message.content

    def plan_implementation(self, idea):
        prompt = f"Create a step-by-step plan to implement the following enhancement:\n{idea}"
        system_prompt = f"""You are lead developer of a project. You are given an enhancement idea and you need to create a step-by-step plan to implement it.
        You need to provide 2-3 steps, NO SUBSTEPS following the format: \n\n1. Step 1\n\n2. Step 2\n\n3. Step 3....
        Differentiate between THINKING steps / PLANNING steps and actual IMPLEMENTATION steps.
        """
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": prompt},
        ]

        pretty_print_conversation(messages)

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=1000
        )

        pretty_print_conversation(
            [{"role": "assistant", "content": response.choices[0].message.content}]
        )

        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        self.total_cost += calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            "gpt-3.5-turbo",
        )

        implementation_steps = self._parse_implementation_steps(
            response.choices[0].message.content
        )
        return implementation_steps

    def suggest_implementation(self, step):
        codebase = self.get_current_codebase()

        prompt = f"""
        CURRENT CODEBASE:
        {self.process_codebase(codebase)}

        
        output THE CHANGES TO THE CODEBASE DUE TO {step}
        
        ONLY if the step is a THINKING STEP/PLANNING STEP/REVIEWING STEP OR SOMETHING OF THAT SORT (!!!), YOUR OUTPUT: FILE:hints.txt
        YOU SHOULD TELL ME THE CHANGES TO ABOVE MENTIONED CODEBASE AFTER THIS:\n\n
        """

        system_prompt = f"""
        INSTRUCTIONS:
        1. Output only the changes TO THE ENTIRE CODEBASE needed to IMPLEMENT THE STEP.
        2. Use the following format for each change:
        FILE:filename.ending
        CHANGE:line_number:new_code
        ADD:line_number:new_code
        3. For multiple lines, use multiple CHANGE or ADD entries.
        4. To delete a line, use CHANGE:line_number:
        5. To insert a new line without modifying existing ones, use ADD:line_number:new_code
        6. To keep a line unchanged, simply don't mention it.
        7. STAY CLOSE TO THE CODEBASE, COVER AS MUCH OF THE CODEBASE AS POSSIBLE

        EXAMPLE:
        FILE:main.py
        ADD:9:# New comment
        CHANGE:10:def modified_function():
        ADD:11:    print("This is a new line")
        CHANGE:12:    return True
        CHANGE:13:
        
        OUTPUT THE CHANGES TO THE CODEBASE IN THE USER PROMPT DUE TO {step}"""

        messages = [
            {
                "role": "system",
                "content": f"You are a code modification assistant. {system_prompt}",
            },
            {"role": "user", "content": prompt},
        ]

        pretty_print_conversation(messages)

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=4096
        )

        changes = response.choices[0].message.content

        pretty_print_conversation(
            [{"role": "assistant", "content": changes}]
        )

        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        self.total_cost += calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            "gpt-3.5-turbo",
        )

        # self._apply_changes(changes)
        return changes

    def apply_linting_suggestions(self, issues, formatted_code):
        for file_path, content in formatted_code.items():
            with open(file_path, "w") as file:
                file.write(content)

        for issue in issues:
            self._fix_linting_issue(issue)

    def _apply_changes(self, changes):
        current_file = None
        file_changes = {}

        for line in changes.split("\n"):
            if line.startswith("FILE:"):
                current_file = line.split(":", 1)[1].strip()
                if current_file not in file_changes:
                    file_changes[current_file] = []
            elif line.startswith("CHANGE:") or line.startswith("ADD:"):
                if current_file is None:
                    continue
                action, line_info, new_code = line.split(":", 2)
                if '-' in line_info:
                    start, end = map(int, line_info.split('-'))
                    file_changes[current_file].append((start, end, action, new_code))
                else:
                    line_number = int(line_info)
                    file_changes[current_file].append((line_number, line_number, action, new_code))
        try:
            for file_path, changes in file_changes.items():
                full_file_path = os.path.join(self.base_dir, file_path)
                print(colored(f"Applying changes to {full_file_path}", "cyan"))
                time.sleep(3)
                try:
                    with open(full_file_path, "r") as file:
                        lines = file.readlines()
                except FileNotFoundError:
                    lines = []

                # Sort changes by line number, with deletions first
                changes.sort(key=lambda x: (x[0], x[2] != 'CHANGE' or x[3].strip() != ''))

                line_offset = 0
                for start, end, action, new_code in changes:
                    adjusted_start = start + line_offset
                    adjusted_end = end + line_offset

                    if action == "CHANGE" and new_code.strip() == "":
                        # Delete lines
                        del lines[adjusted_start - 1:adjusted_end]
                        line_offset -= (end - start + 1)
                    elif action == "CHANGE":
                        # Replace lines
                        lines[adjusted_start - 1:adjusted_end] = [new_code + "\n"]
                        line_offset += len(new_code.split("\n")) - (end - start + 1)
                    elif action == "ADD":
                        # Add new line
                        lines.insert(adjusted_start - 1, new_code + "\n")
                        line_offset += 1

                with open(full_file_path, "w") as file:
                    file.writelines(lines)
        except Exception as e:
            print(colored(f"Error applying changes: {e}", "red"))

        print(colored("Changes applied successfully.", "green"))

    def _fix_linting_issue(self, issue):
        # Implement logic to fix a single linting issue
        # This is a placeholder and should be expanded based on your linting tool's output format
        pass

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
