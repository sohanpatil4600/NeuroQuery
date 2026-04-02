import sys
import traceback
from mem0 import Memory
import os
from dotenv import load_dotenv
load_dotenv()

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "path": "/Users/sohanpatil/Downloads/NeuroQuery/memories/qdrant_test_storage",
            "collection_name": "test_memories"
        }
    },
    "llm": {
        "provider": "groq",
        "config": {
            "model": "llama-3.3-70b-versatile"
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    }
}

try:
    mem = Memory.from_config(config)
    print("Memory Instance OK")
    mem.add("My favorite product is the Hardware Key", user_id="u1")
    results = mem.search("What is my favorite product?", user_id="u1")
    print("KEYS IN FIRST RESULT:", results[0].keys() if results else "empty")
    print("Search Results:", results)
except Exception as e:
    traceback.print_exc()
