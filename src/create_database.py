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
import magic
from config.settings import *

load_dotenv()

def generate_RAG_DB(path=UPLOADS_PATH):
    print(f"Generating RAG DB with path: {path}")
    print(f"RAG_DB_PATH: {RAG_DB_PATH}")
    
    # Ensure RAG_DB_PATH directory exists with proper permissions
    os.makedirs(RAG_DB_PATH, exist_ok=True)
    os.chmod(RAG_DB_PATH, 0o755)
    
    # Ensure uploads directory exists with proper permissions
    os.makedirs(UPLOADS_PATH, exist_ok=True)
    os.chmod(UPLOADS_PATH, 0o755)
    
    documents = load_documents(path)
    if not documents:
        raise ValueError("No valid documents found to process")
        
    chunks = split_text(documents)
    if not chunks:
        raise ValueError("No valid chunks generated from documents")
        
    db = save_to_chroma(chunks)
    return db

def load_documents(path):
    print(f"Loading documents from: {path}")
    documents = []
    
    # Initialize magic for file type detection
    mime = magic.Magic(mime=True)
    
    for filetype in RAG_FILETYPES:
        try:
            # Use DirectoryLoader with error handling for each file
            loader = DirectoryLoader(
                path,
                glob=f"**/*.{filetype}",
                recursive=True,
                show_progress=True,
                use_multithreading=True
            )
            
            # Load files with validation
            for file_path in loader._get_file_list():
                try:
                    # Check if file still exists and is readable
                    if not os.path.exists(file_path):
                        print(f"File no longer exists: {file_path}")
                        continue
                        
                    # Verify file type
                    detected_type = mime.from_file(file_path)
                    if not any(t in detected_type for t in ['text', 'python', 'javascript', 'json', 'xml', 'html']):
                        print(f"Skipping non-text file: {file_path}")
                        continue
                    
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if not content:
                            print(f"Skipping empty file: {file_path}")
                            continue
                            
                        # Create document with metadata
                        doc = Document(
                            page_content=content,
                            metadata={
                                'source': file_path,
                                'filetype': filetype,
                                'size': len(content)
                            }
                        )
                        documents.append(doc)
                        print(f"Successfully loaded: {file_path}")
                        
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error loading {filetype} files: {str(e)}")
            continue
            
    print(f"Successfully loaded {len(documents)} documents")
    return documents

def split_text(documents: list):
    print(f"Splitting {len(documents)} documents")
    if not documents:
        return []
        
    # Helper function to count lines up to a character index
    def get_line_number(text: str, char_idx: int) -> int:
        return text[:char_idx].count('\n') + 1

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )
    
    try:
        chunks = text_splitter.split_documents(documents)
        # Validate chunks aren't empty
        chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
        
        # Add line numbers to chunk metadata
        for chunk in chunks:
            text = chunk.page_content
            start_idx = chunk.metadata.get('start_index', 0)
            end_idx = start_idx + len(chunk.page_content)
            
            chunk.metadata['start_line'] = get_line_number(text, start_idx)
            chunk.metadata['end_line'] = get_line_number(text, end_idx)

        print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        print(f"Error splitting documents: {str(e)}")
        return []

def save_to_chroma(chunks: list):
    print(f"Saving to ChromaDB at: {RAG_DB_PATH}")
    
    if not chunks:
        raise ValueError("Cannot save empty chunks to ChromaDB")
        
    try:
        # Clear out the database first.
        if os.path.exists(RAG_DB_PATH):
            print(f"Removing existing ChromaDB at: {RAG_DB_PATH}")
            shutil.rmtree(RAG_DB_PATH)
            # Recreate the directory
            os.makedirs(RAG_DB_PATH, exist_ok=True)
            os.chmod(RAG_DB_PATH, 0o755)

        # Create embeddings instance first to validate OpenAI connection
        embeddings = OpenAIEmbeddings()
        # Test embeddings with a sample chunk
        try:
            test_embedding = embeddings.embed_query(chunks[0].page_content)
            if not test_embedding:
                raise ValueError("Failed to generate test embedding")
        except Exception as e:
            print(f"Error testing embeddings: {str(e)}")
            raise

        # Create a new DB from the documents.
        print("Creating new ChromaDB instance...")
        db = Chroma.from_documents(
            chunks, embeddings, persist_directory=RAG_DB_PATH
        )
        print(f"Successfully saved {len(chunks)} chunks to {RAG_DB_PATH}.")
        return db
    except Exception as e:
        print(f"Error saving to ChromaDB: {str(e)}")
        raise
