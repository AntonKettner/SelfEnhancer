__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import glob
import tiktoken

from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback

from termcolor import colored
from src.create_database import generate_RAG_DB
from src.query_data import query_RAG_DB
from config.settings import *
from data.prompts import *

class Enhancement:
    def __init__(self):
        self.codebase = self.get_codebase(DATA_PATH)
        self.structure = self.generate_structure_tree(DATA_PATH)
        self.db = generate_RAG_DB(DATA_PATH)

    def update_rag_db(self, path=DATA_PATH):
        print(colored("Creating RAG DB...", "green"))
        self.db = generate_RAG_DB(path)

    def count_tokens(self, prompt):
        encoding_model = tiktoken.encoding_name_for_model(LLM_MODEL)
        encoding = tiktoken.get_encoding(encoding_model)
        tokens = encoding.encode(prompt)
        return len(tokens)

    def get_codebase(self, path):
        codebase = {}
        for extension in RAG_FILETYPES:
            for file_path in glob.glob(os.path.join(path, "**/*.{}".format(extension)), recursive=True):
                with open(file_path, "r") as file:
                    content = file.read()
                    numbered_content = f"FILE:{os.path.relpath(file_path, path)}\n"
                    for i, line in enumerate(content.split("\n"), 1):
                        numbered_content += f":{i}:{line}\n"
                    codebase[os.path.relpath(file_path, path)] = numbered_content
        return codebase

    def process_codebase(self, codebase):
        prompt = ""
        for file_path, content in codebase.items():
            prompt += f"File: {file_path}\n{content}\n\n"
        return prompt

    def update_usage(self, added_usage):
        if hasattr(self, "usage"):
            self.usage.total_tokens += added_usage.total_tokens
            self.usage.prompt_tokens += added_usage.prompt_tokens
            self.usage.completion_tokens += added_usage.completion_tokens
            self.usage.total_cost += added_usage.total_cost
        else:
            self.usage = added_usage

    def generate_improvement_ideas(self):
        print(colored("Generating improvement ideas...", "green"))
        llm = ChatOpenAI(model=LLM_MODEL)
        
        # Format the prompt with the project structure
        print(colored("Processing Codebase...", "green"))
        processed_codebase = self.process_codebase(self.codebase)
        prompt_full_codebase = IMPROVEMENT_IDEAS.format(codebase=processed_codebase)

        # Count the tokens in the prompt
        print(colored("Counting Tokens for full prompt...", "green"))
        prompt_tokens = self.count_tokens(prompt_full_codebase)
        
        # run the model either with contet or in RAG mode
        with get_openai_callback() as cb:
            if prompt_tokens < MAX_CONTEXT:
                # Get response from LLM with codebase as context
                print(colored(f"Prompt tokens ({prompt_tokens}) are less than the maximum context {MAX_CONTEXT}. Using LLM-Context Window...", "green"))
                response = llm.invoke(prompt_full_codebase)
            else:
                # Use RAG with structure tree
                print(colored(f"Prompt tokens ({prompt_tokens}) are more than the maximum context {MAX_CONTEXT}. Using RAG...", "green"))
                RAG_question = GET_RAG_IMPROVEMENT.format(structure=self.structure)
                rag_context = query_RAG_DB(RAG_question)
                rag_codebase=RAG_CODEBASE.format(rag_context=rag_context, structure=self.structure)
                prompt_with_rag = IMPROVEMENT_IDEAS.format(codebase=rag_codebase)
                response = llm.invoke(prompt_with_rag)
            current_usage = cb
        self.update_usage(current_usage)

        # Parse the response into a list of ideas
        ideas_text = response.content
        ideas_list = [
            idea.split('[IDEA]')[1].strip()
            for idea in ideas_text.split('\n')
            if '[IDEA]' in idea
        ]
        
        return ideas_list, current_usage

    def generate_structure_tree(self, path):
        print(colored("Generating structure tree...", "green"))
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


def main():
    
    enhancement = Enhancement()
    if IDEA_GENERATION:
        enhancement.ideas, enhancement.usage = enhancement.generate_improvement_ideas()
    else:
        input_idea = input("Enter idea for codebase enhancement:\n")
        enhancement.ideas = [str(input_idea)]

    # pretty print ideas and for codebase enhancement and usage of api (and cost)
    print(colored("IDEAS FOR CODEBASE ENHANCEMENT:\n", "blue"))
    for index, idea in enumerate(enhancement.ideas):
        print(colored(f"{index+1}: {idea}\n", "green"))
    print(enhancement.usage)


if __name__ == "__main__":
    main()
