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
            "path": "/Users/sohanpatil/Downloads/NeuroQuery/memories/qdrant_test_v4",
            "collection_name": "agentic_bi_memories_v4",
            "embedding_model_dims": 384
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
    print("Loading memory...")
    mem = Memory.from_config(config)
    print("Adding memory...")
    mem.add("User Question: My favorite product is the Hardware Key | AI Insight: Hardware Key", user_id="u1")
    print("Searching...")
    results = mem.search("What is my favorite product?", user_id="u1")
    print("Raw format:")
    import json
    # Print the raw dict representation to stdout
    print(json.dumps(results, default=str, indent=2))
except Exception as e:
    traceback.print_exc()
