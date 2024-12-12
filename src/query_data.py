import argparse
import dotenv
from termcolor import colored
# from dataclasses import dataclass
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

    # Prepare the DB.
    embedding_function = OpenAIEmbeddings()
    print(f"db_path: {db_path}")
    db = Chroma(persist_directory=db_path, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=MAX_RAG_VECTOR_NO)

    # Filter out results with low relevance scores and return if no results are found.
    if len(results) == 0:
        print(f"Unable to find any well matching results.")
        raise ValueError("No results from RAG.")
    for doc, score in results:
        if score < MIN_RELEVANCE_SCORE:
            results.remove((doc, score))

    # format the results for usage with LLM
    formatted_results = format_results(results)
    print(colored(f"Results:\n\n{formatted_results}", "green"))

    # prompt the LLM with the RAG context
    prompt_template = ChatPromptTemplate.from_template(RAG_QUERY)
    prompt = prompt_template.format(context=formatted_results, question=query_text)
    model = ChatOpenAI()
    response = model.invoke(prompt)
    return response

