import os
# =========================================PATHS=========================================
RAG_DB_PATH = os.environ.get('RAG_DB_PATH', '/home/site/wwwroot/data/chroma')
DATA_PATH = os.environ.get('DATA_PATH', os.getcwd())
# =========================================PARAMS=========================================
MAX_RAG_VECTOR_NO = 3
RAG_FILETYPES = ["py", "txt", "md"]
MIN_RELEVANCE_SCORE = 0.58    # 0 similarity score means it is the same Vector, 1 means it is completely different
HUMAN_IN_THE_LOOP = True
LLM_MODEL = "gpt-4o-mini"
IDEA_GENERATION = True
# =========================================MAX_CONTEXTS_BY_MODEL=========================================
if "3.5" in LLM_MODEL:
    MAX_CONTEXT = 16385
else:
    MAX_CONTEXT = 128e3
