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
Based on the following project generate improvement ideas.

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