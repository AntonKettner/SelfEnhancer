# =========================================RAG=========================================
RAG_QUERY = """
RAG context:
---
{context}
---

Please answer the following question:
---
{question}
---
"""

# =========================================IMPROVEMENT IDEAS=========================================
IMPROVEMENT_IDEAS = """
Based on the following project generate improvement ideas. Consider general code quality, readability, maintainability, stability and featureset.

Project:
****
{codebase}
****
Please generate 5 specific improvement ideas on how to enhance this codebase. Format your response exactly as follows:

1. [IDEA] First improvement idea
2. [IDEA] Second improvement idea
3. [IDEA] Third improvement idea
4. [IDEA] Fourth improvement idea
5. [IDEA] Fifth improvement idea

Each idea should be practical, specific, and implementable.
"""

GET_RAG_IMPROVEMENT = """
BAD CODE quality, readability, maintainability, stability and featureset.

Project:
****
{structure}
****
"""

RAG_CODEBASE = """
RAG context:
__
{rag_context}
__

Structure Tree:
__
{structure}
__
"""
