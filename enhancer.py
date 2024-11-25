import os
import glob

from langchain_openai import ChatOpenAI

from termcolor import colored
from src.create_database import generate_RAG_DB
from src.query_data import query_RAG_DB
from config.settings import *
from data.prompts import *

class Enhancement:
    def __init__(self, idea_generation):
        self.codebase = self.get_codebase(DATA_PATH)
        # self.structure = self.generate_structure_tree(DATA_PATH)
        self.db = generate_RAG_DB(DATA_PATH)
        self.ideas = self.generate_improvement_ideas() if idea_generation else None

    def rag_query(self, query_text):
        query_RAG_DB(query_text, self.db)

    def update_rag_db(self, path=DATA_PATH):
        print(colored("Creating RAG DB...", "green"))
        self.db = generate_RAG_DB(path)

    def get_codebase(self, path):
        codebase = {}
        for extension in RAG_FILETYPES:
            for file_path in glob.glob(os.path.join(path, "**/*.", extension), recursive=True):
                with open(file_path, "r") as file:
                    content = file.read()
                    numbered_content = f"FILE:{os.path.relpath(file_path, path)}\n"
                    for i, line in enumerate(content.split("\n"), 1):
                        numbered_content += f":{i}:{line}\n"
                    codebase[os.path.relpath(file_path, path)] = numbered_content
        return codebase

    def generate_improvement_ideas(self):
        print(colored("Generating improvement ideas...", "green"))
        llm = ChatOpenAI()
        
        # Format the prompt with the project structure
        prompt = IMPROVEMENT_IDEAS.format(codebase=self.codebase)
        
        # Get response from LLM
        response = llm.invoke(prompt)
        
        # Parse the response into a list of ideas
        ideas_text = response.content
        ideas_list = [
            idea.split('[IDEA]')[1].strip()
            for idea in ideas_text.split('\n')
            if '[IDEA]' in idea
        ]
        
        self.ideas = ideas_list
        return ideas_list

    def generate_structure_tree(self, path):
        print(colored("Generating structure tree...", "green"))
        structure = []
        
        for root, dirs, files in os.walk(path):
            level = root.replace(path, '').count(os.sep)
            indent = '  ' * level
            structure.append(f'{indent}{os.path.basename(root)}/')
            
            for file in files:
                if not file.startswith('.') and not file.endswith('.pyc'):
                    structure.append(f'{indent}  {file}')
        
        return '\n'.join(structure)

def main():
    enhancement = Enhancement(IDEA_GENERATION)

    # pretty print ideas for codebase enhancement
    print(colored("IDEAS FOR CODEBASE ENHANCEMENT:\n", "blue"))
    for index, idea in enumerate(enhancement.ideas):
        print(colored(f"{index+1}: {idea}\n", "green"))


if __name__ == "__main__":
    main()


# generate_RAG_DB()