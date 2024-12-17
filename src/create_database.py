__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import openai
from dotenv import load_dotenv
import os
import shutil
from config.settings import *

load_dotenv()


#! Add check for existing database -> save saving times of all docs and their lengths to temp dir
def generate_RAG_DB(path=DATA_PATH):
    print(f"Generating RAG DB with path: {path}")
    print(f"RAG_DB_PATH: {RAG_DB_PATH}")
    
    # Ensure RAG_DB_PATH directory exists with proper permissions
    os.makedirs(RAG_DB_PATH, exist_ok=True)
    os.chmod(RAG_DB_PATH, 0o755)
    
    documents = load_documents(path)
    chunks = split_text(documents)
    db = save_to_chroma(chunks)
    return db


def load_documents(path):
    print(f"Loading documents from: {path}")
    # Load Python, text, and markdown files from all subdirectories
    documents = []
    for filetype in RAG_FILETYPES:
        try:
            loader = DirectoryLoader(path, glob=f"**/*.{filetype}", recursive=True)
            single_type_docs = loader.load()
            documents.extend(single_type_docs)
            print(f"Loaded {len(single_type_docs)} {filetype} files")
        except Exception as e:
            print(f"Error loading {filetype} files: {str(e)}")
    return documents


def split_text(documents: list):
    print(f"Splitting {len(documents)} documents")
    # Helper function to count lines up to a character index
    def get_line_number(text: str, char_idx: int) -> int:
        return text[:char_idx].count('\n') + 1

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    
    # Add line numbers to chunk metadata
    for chunk in chunks:
        text = chunk.page_content
        start_idx = chunk.metadata.get('start_index', 0)
        end_idx = start_idx + len(chunk.page_content)
        
        chunk.metadata['start_line'] = get_line_number(text, start_idx)
        chunk.metadata['end_line'] = get_line_number(text, end_idx)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks


def save_to_chroma(chunks: list):
    print(f"Saving to ChromaDB at: {RAG_DB_PATH}")
    try:
        # Clear out the database first.
        if os.path.exists(RAG_DB_PATH):
            print(f"Removing existing ChromaDB at: {RAG_DB_PATH}")
            shutil.rmtree(RAG_DB_PATH)
            # Recreate the directory
            os.makedirs(RAG_DB_PATH, exist_ok=True)
            os.chmod(RAG_DB_PATH, 0o755)

        # Create a new DB from the documents.
        print("Creating new ChromaDB instance...")
        db = Chroma.from_documents(
            chunks, OpenAIEmbeddings(), persist_directory=RAG_DB_PATH
        )
        print(f"Successfully saved {len(chunks)} chunks to {RAG_DB_PATH}.")
        return db
    except Exception as e:
        print(f"Error saving to ChromaDB: {str(e)}")
        raise
