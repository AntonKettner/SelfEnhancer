__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import glob
import tiktoken
import traceback

from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback

from termcolor import colored
from src.create_database import generate_RAG_DB
from src.query_data import query_RAG_DB
from config.settings import *
from data.prompts import *

class Enhancement:
    def __init__(self):
        self.data_path = os.environ.get('DATA_PATH')
        if not self.data_path:
            raise ValueError("DATA_PATH environment variable not set")
            
        print(colored(f"Initializing Enhancement with DATA_PATH: {self.data_path}", "green"))
        try:
            self.codebase = self.get_codebase(self.data_path)
            self.structure = self.generate_structure_tree(self.data_path)
            print(colored("Generating RAG DB...", "green"))
            self.db = generate_RAG_DB(self.data_path)
        except Exception as e:
            print(colored(f"Error during initialization: {str(e)}", "red"))
            print(colored(f"Traceback: {traceback.format_exc()}", "red"))
            raise

    def update_rag_db(self):
        print(colored(f"Creating RAG DB at path: {self.data_path}", "green"))
        try:
            self.db = generate_RAG_DB(self.data_path)
        except Exception as e:
            print(colored(f"Error updating RAG DB: {str(e)}", "red"))
            raise

    def count_tokens(self, prompt):
        try:
            print(colored(f"Counting tokens for model: {LLM_MODEL}", "green"))
            encoding_model = tiktoken.encoding_name_for_model(LLM_MODEL)
            encoding = tiktoken.get_encoding(encoding_model)
            tokens = encoding.encode(prompt)
            token_count = len(tokens)
            print(colored(f"Token count: {token_count}", "green"))
            return token_count
        except Exception as e:
            print(colored(f"Error counting tokens: {str(e)}", "red"))
            raise

    def get_codebase(self, path):
        print(colored(f"Getting codebase from path: {path}", "green"))
        codebase = {}
        try:
            for extension in RAG_FILETYPES:
                glob_pattern = os.path.join(path, f"**/*.{extension}")
                print(colored(f"Searching for files with pattern: {glob_pattern}", "green"))
                for file_path in glob.glob(glob_pattern, recursive=True):
                    try:
                        with open(file_path, "r") as file:
                            content = file.read()
                            rel_path = os.path.relpath(file_path, path)
                            numbered_content = f"FILE:{rel_path}\n"
                            for i, line in enumerate(content.split("\n"), 1):
                                numbered_content += f":{i}:{line}\n"
                            codebase[rel_path] = numbered_content
                            print(colored(f"Processed file: {rel_path}", "green"))
                    except Exception as e:
                        print(colored(f"Error processing file {file_path}: {str(e)}", "yellow"))
                        continue
            return codebase
        except Exception as e:
            print(colored(f"Error getting codebase: {str(e)}", "red"))
            raise

    def process_codebase(self, codebase):
        print(colored("Processing codebase...", "green"))
        try:
            prompt = ""
            for file_path, content in codebase.items():
                prompt += f"File: {file_path}\n{content}\n\n"
            return prompt
        except Exception as e:
            print(colored(f"Error processing codebase: {str(e)}", "red"))
            raise

    def update_usage(self, added_usage):
        try:
            if hasattr(self, "usage"):
                self.usage.total_tokens += added_usage.total_tokens
                self.usage.prompt_tokens += added_usage.prompt_tokens
                self.usage.completion_tokens += added_usage.completion_tokens
                self.usage.total_cost += added_usage.total_cost
            else:
                self.usage = added_usage
        except Exception as e:
            print(colored(f"Error updating usage: {str(e)}", "red"))
            raise

    def generate_improvement_ideas(self):
        print(colored("Generating improvement ideas...", "green"))
        try:
            # Verify OpenAI API key
            if not os.environ.get('OPENAI_API_KEY'):
                raise ValueError("OpenAI API key not found in environment variables")
                
            print(colored(f"Initializing ChatOpenAI with model: {LLM_MODEL}", "green"))
            llm = ChatOpenAI(model=LLM_MODEL)
            
            # Format the prompt with the project structure
            print(colored("Processing Codebase...", "green"))
            processed_codebase = self.process_codebase(self.codebase)
            prompt_full_codebase = IMPROVEMENT_IDEAS.format(codebase=processed_codebase)

            # Count the tokens in the prompt
            print(colored("Counting Tokens for full prompt...", "green"))
            prompt_tokens = self.count_tokens(prompt_full_codebase)
            
            # run the model either with context or in RAG mode
            with get_openai_callback() as cb:
                if prompt_tokens < MAX_CONTEXT:
                    # Get response from LLM with codebase as context
                    print(colored(f"Using LLM-Context Window (tokens: {prompt_tokens}/{MAX_CONTEXT})", "green"))
                    response = llm.invoke(prompt_full_codebase)
                else:
                    # Use RAG with structure tree
                    print(colored(f"Using RAG (tokens: {prompt_tokens}/{MAX_CONTEXT})", "green"))
                    RAG_question = GET_RAG_IMPROVEMENT.format(structure=self.structure)
                    print(colored("Querying RAG DB...", "green"))
                    rag_context = query_RAG_DB(RAG_question)
                    rag_codebase = RAG_CODEBASE.format(rag_context=rag_context, structure=self.structure)
                    prompt_with_rag = IMPROVEMENT_IDEAS.format(codebase=rag_codebase)
                    print(colored("Getting response from LLM...", "green"))
                    response = llm.invoke(prompt_with_rag)
                current_usage = cb
            self.update_usage(current_usage)

            # Parse the response into a list of ideas
            print(colored("Parsing response...", "green"))
            ideas_text = response.content
            print(colored(f"Raw response content:\n{ideas_text}", "blue"))
            
            if not ideas_text:
                print(colored("Warning: Empty response from LLM", "yellow"))
                return [], current_usage
                
            # Split response into lines and look for [IDEA] tags
            ideas_lines = [line for line in ideas_text.split('\n') if '[IDEA]' in line]
            print(colored(f"Found {len(ideas_lines)} lines containing [IDEA] tags", "green"))
            
            if not ideas_lines:
                print(colored("Warning: No [IDEA] tags found in response", "yellow"))
                # Return the full response as a single idea if no tags found
                return [ideas_text.strip()], current_usage
            
            # Extract ideas from lines containing [IDEA] tags
            ideas_list = []
            for line in ideas_lines:
                try:
                    idea = line.split('[IDEA]')[1].strip()
                    ideas_list.append(idea)
                    print(colored(f"Extracted idea: {idea}", "green"))
                except IndexError as e:
                    print(colored(f"Error extracting idea from line: {line}", "yellow"))
                    continue
            
            if not ideas_list:
                print(colored("Warning: Failed to extract any ideas from response", "yellow"))
                return [ideas_text.strip()], current_usage
            
            return ideas_list, current_usage
        except Exception as e:
            print(colored(f"Error generating improvement ideas: {str(e)}", "red"))
            print(colored(f"Traceback: {traceback.format_exc()}", "red"))
            raise

    def generate_structure_tree(self, path):
        print(colored(f"Generating structure tree for path: {path}", "green"))
        try:
            structure = []
            
            for root, dirs, files in os.walk(path):
                # Modify `dirs` in-place to exclude directories that start with `.`
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                level = root.replace(path, '').count(os.sep)
                indent = '  ' * level
                structure.append(f'{indent}{os.path.basename(root)}/')
                for file in files:
                    if not file.startswith('.') and not file.endswith('.pyc'):
                        structure.append(f'{indent}  {file}')

            structure_tree = '\n'.join(structure)
            return structure_tree
        except Exception as e:
            print(colored(f"Error generating structure tree: {str(e)}", "red"))
            raise


def main():
    try:
        print(colored("Starting enhancement process...", "green"))
        enhancement = Enhancement()
        
        if IDEA_GENERATION:
            print(colored("Generating improvement ideas...", "green"))
            enhancement.ideas, enhancement.usage = enhancement.generate_improvement_ideas()
        else:
            input_idea = input("Enter idea for codebase enhancement:\n")
            enhancement.ideas = [str(input_idea)]

        # pretty print ideas and for codebase enhancement and usage of api (and cost)
        print(colored("\nIDEAS FOR CODEBASE ENHANCEMENT:\n", "blue"))
        for index, idea in enumerate(enhancement.ideas):
            print(colored(f"{index+1}: {idea}\n", "green"))
        print(enhancement.usage)
        
    except Exception as e:
        print(colored(f"Error in main: {str(e)}", "red"))
        print(colored(f"Traceback: {traceback.format_exc()}", "red"))
        sys.exit(1)


if __name__ == "__main__":
    main()
