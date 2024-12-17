__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import argparse
import dotenv
import os
from termcolor import colored
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from data.prompts import *
from config.settings import *

dotenv.load_dotenv()


def format_results(results):
    formatted_results = ""
    for doc, score in results:
        formatted_results += f"File: {doc.metadata.get('source', 'No source')}\n"
        formatted_results += f"Line: {doc.metadata.get('start_line', 'N')}-"
        formatted_results += f"{doc.metadata.get('end_line', 'A')}\n"
        formatted_results += f"Relevance score: {score}\n"
        formatted_results += f"Content: \n***\n{doc.page_content}\n***\n"
    return formatted_results


def query_RAG_DB(query_text, db_path=RAG_DB_PATH):
    print(f"Querying RAG DB at path: {db_path}")
    
    try:
        # Verify ChromaDB directory exists
        if not os.path.exists(db_path):
            print(f"ChromaDB directory does not exist at: {db_path}")
            print("Creating directory...")
            os.makedirs(db_path, exist_ok=True)
            os.chmod(db_path, 0o755)
            raise ValueError(f"ChromaDB not initialized at {db_path}. Please run the enhancement process first.")

        # Verify OpenAI API key
        if not os.environ.get('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key not found in environment variables")

        # Prepare the DB.
        print("Initializing OpenAI embeddings...")
        embedding_function = OpenAIEmbeddings()
        print(f"Loading ChromaDB from: {db_path}")
        db = Chroma(persist_directory=db_path, embedding_function=embedding_function)

        # Search the DB.
        print(f"Performing similarity search for query: {query_text}")
        results = db.similarity_search_with_relevance_scores(query_text, k=MAX_RAG_VECTOR_NO)

        # Filter out results with low relevance scores and return if no results are found.
        if len(results) == 0:
            print(f"Unable to find any matching results.")
            raise ValueError("No results from RAG.")
        
        filtered_results = []
        for doc, score in results:
            if score >= MIN_RELEVANCE_SCORE:
                filtered_results.append((doc, score))
        
        if not filtered_results:
            print(f"No results met the minimum relevance score of {MIN_RELEVANCE_SCORE}")
            raise ValueError("No relevant results found")

        # format the results for usage with LLM
        print("Formatting results...")
        formatted_results = format_results(filtered_results)
        print(colored(f"Results:\n\n{formatted_results}", "green"))

        # prompt the LLM with the RAG context
        print("Creating LLM prompt...")
        prompt_template = ChatPromptTemplate.from_template(RAG_QUERY)
        prompt = prompt_template.format(context=formatted_results, question=query_text)
        
        print(f"Initializing ChatOpenAI with model: {LLM_MODEL}")
        model = ChatOpenAI(model=LLM_MODEL)
        
        print("Sending request to OpenAI...")
        response = model.invoke(prompt)
        print("Received response from OpenAI")
        
        return response
        
    except Exception as e:
        error_msg = f"Error in query_RAG_DB: {str(e)}"
        print(colored(error_msg, "red"))
        raise Exception(error_msg) from e
