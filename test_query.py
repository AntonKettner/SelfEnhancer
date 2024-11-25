import os

from src.create_database import generate_RAG_DB
from src.query_data import query_RAG_DB
from config.settings import *

response = query_RAG_DB("Python arguments database?")
# response = query_RAG_DB("What is the difference between octupusses and whales?")


# generate_RAG_DB()