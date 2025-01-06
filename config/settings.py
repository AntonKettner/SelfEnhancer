import os


# =========================================PATHS=========================================
def get_user_rag_path(user_id=None):
    base_path = os.environ.get("RAG_DB_PATH", "/home/site/wwwroot/data/chroma")
    if user_id is not None:
        return os.path.join(base_path, f"user_{user_id}")
    return base_path


RAG_DB_PATH = get_user_rag_path()  # Default path without user_id
DATA_PATH = os.environ.get("DATA_PATH", os.getcwd())
UPLOADS_PATH = os.path.join("/home/site/wwwroot/data", "uploads")

# =========================================PARAMS=========================================
MAX_RAG_VECTOR_NO = 3
RAG_FILETYPES = [
    "py",  # Python files
    "txt",  # Text files
    "md",  # Markdown
    "js",  # JavaScript
    "ts",  # TypeScript
    "jsx",  # React
    "tsx",  # React with TypeScript
    "json",  # JSON files
    "yml",  # YAML files
    "yaml",  # YAML files
    "html",  # HTML files
    "css",  # CSS files
    "sh",  # Shell scripts
    "xml",  # XML files
    "sql",  # SQL files
]

MIN_RELEVANCE_SCORE = (
    0.58  # 0 similarity score means it is the same Vector, 1 means it is completely different
)
HUMAN_IN_THE_LOOP = True
LLM_MODEL = "gpt-4o-mini"
IDEA_GENERATION = True

# =========================================MAX_CONTEXTS_BY_MODEL=========================================
if "3.5" in LLM_MODEL:
    MAX_CONTEXT = 16385  # For gpt-3.5-turbo
else:
    MAX_CONTEXT = 128e3  # For gpt-4o-mini
