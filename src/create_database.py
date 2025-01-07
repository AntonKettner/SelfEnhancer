__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
import openai
from dotenv import load_dotenv
import os
import shutil
import mimetypes
from config.settings import *
import glob

load_dotenv()

# Initialize mimetypes
mimetypes.init()


def generate_RAG_DB(path=UPLOADS_PATH, user_id=None):
    # Get user-specific RAG path
    rag_path = get_user_rag_path(user_id) if user_id is not None else RAG_DB_PATH
    print(f"Generating RAG DB with path: {path}")
    print(f"RAG_DB_PATH: {rag_path}")

    # Ensure RAG_DB_PATH directory exists with proper permissions
    os.makedirs(rag_path, exist_ok=True)
    os.chmod(rag_path, 0o755)

    # Ensure uploads directory exists with proper permissions
    os.makedirs(UPLOADS_PATH, exist_ok=True)
    os.chmod(UPLOADS_PATH, 0o755)

    documents = load_documents(path)
    if not documents:
        raise ValueError("No valid documents found to process")

    chunks = split_text(documents)
    if not chunks:
        raise ValueError("No valid chunks generated from documents")

    db = save_to_chroma(chunks, rag_path)
    return db


def is_text_file(file_path, filetype):
    """Determine if a file is a text file using mimetypes"""
    # First check the file extension
    if filetype in RAG_FILETYPES:
        return True

    # Then check mimetype
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and (
        "text" in mime_type
        or "javascript" in mime_type
        or "json" in mime_type
        or "xml" in mime_type
    ):
        return True

    # Finally, try to read the file as text
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read(1024)  # Try reading first 1KB
        return True
    except UnicodeDecodeError:
        return False


def load_documents(path):
    print(f"Loading documents from: {path}")
    documents = []

    for filetype in RAG_FILETYPES:
        try:
            # Get list of files using glob pattern
            glob_pattern = os.path.join(path, f"**/*.{filetype}")
            file_list = glob.glob(glob_pattern, recursive=True)

            # Process each file
            for file_path in file_list:
                try:
                    # Check if file still exists and is readable
                    if not os.path.exists(file_path):
                        print(f"File no longer exists: {file_path}")
                        continue

                    # Verify file is a text file
                    if not is_text_file(file_path, filetype):
                        print(f"Skipping non-text file: {file_path}")
                        continue

                    # Read file content
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if not content:
                            print(f"Skipping empty file: {file_path}")
                            continue

                        # Create document with metadata
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": file_path,
                                "filetype": filetype,
                                "size": len(content),
                            },
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
        return text[:char_idx].count("\n") + 1

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
            start_idx = chunk.metadata.get("start_index", 0)
            end_idx = start_idx + len(chunk.page_content)

            chunk.metadata["start_line"] = get_line_number(text, start_idx)
            chunk.metadata["end_line"] = get_line_number(text, end_idx)

        print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        print(f"Error splitting documents: {str(e)}")
        return []


def save_to_chroma(chunks: list, rag_path: str):
    print(f"Saving to ChromaDB at: {rag_path}")

    if not chunks:
        raise ValueError("Cannot save empty chunks to ChromaDB")

    try:
        # Clear out the database first
        if os.path.exists(rag_path):
            print(f"Removing existing ChromaDB at: {rag_path}")
            try:
                # Use chromadb directly for cleanup
                print("Attempting to reset ChromaDB...")
                settings = chromadb.Settings(
                    allow_reset=True, is_persistent=True, persist_directory=rag_path
                )
                client = chromadb.PersistentClient(settings=settings)
                client.reset()
                del client
            except Exception as e:
                print(f"Warning: Error resetting ChromaDB: {e}")
                # If reset fails, try manual cleanup
                try:
                    print("Attempting manual cleanup...")
                    shutil.rmtree(rag_path, ignore_errors=True)
                except Exception as e:
                    print(f"Warning: Manual cleanup failed: {e}")

        # Ensure all parent directories exist with proper permissions
        parent_dir = os.path.dirname(rag_path)
        print(f"Ensuring parent directory exists: {parent_dir}")
        os.makedirs(parent_dir, exist_ok=True)
        os.chmod(parent_dir, 0o777)

        # Recreate the ChromaDB directory with proper permissions
        print(f"Creating ChromaDB directory at: {rag_path}")
        os.makedirs(rag_path, exist_ok=True)
        os.chmod(rag_path, 0o777)  # Full permissions to handle Azure App Service restrictions

        # Ensure the directory is empty
        for item in os.listdir(rag_path):
            item_path = os.path.join(rag_path, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        # Verify directory permissions
        print("Verifying directory permissions...")
        try:
            # Create a test file to verify write permissions
            test_file = os.path.join(rag_path, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print("Successfully verified write permissions")

            # List directory contents and permissions
            print("Directory contents and permissions:")
            os.system(f"ls -la {rag_path}")
        except Exception as e:
            print(f"Permission verification failed: {e}")
            raise

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

        # Create ChromaDB instance
        print("Creating new ChromaDB instance...")
        settings = chromadb.Settings(
            allow_reset=True, is_persistent=True, persist_directory=rag_path
        )
        client = chromadb.PersistentClient(settings=settings)

        # Create collection
        print("Creating ChromaDB collection...")
        collection = client.create_collection(name="code_chunks")

        # Create Langchain wrapper
        db = Chroma(
            client=client,
            collection_name="code_chunks",
            embedding_function=embeddings,
        )

        # Add documents to the collection
        print("Adding documents to collection...")
        db.add_documents(documents=chunks)

        # Force persist and wait for files
        print("Persisting database...")
        client.persist()

        # Verify database files exist
        print("Verifying database files...")
        if not os.path.exists(os.path.join(rag_path, "chroma.sqlite3")):
            raise ValueError("Database files not created properly")
        print("Database files created successfully")

        return db
    except Exception as e:
        print(f"Error saving to ChromaDB: {str(e)}")
        raise
