from app.utils.logger_utils import silence_ai_noise
silence_ai_noise()

import os
from mem0 import Memory
from dotenv import load_dotenv
import logging

load_dotenv()

# Use environment variables
groq_key = os.getenv("GROQ_API_KEY")
if groq_key == "your_groq_key": groq_key = None

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "path": "/Users/sohanpatil/Downloads/NeuroQuery/memories/qdrant_storage",
            "collection_name": "agentic_bi_memories_v3",
            "embedding_model_dims": 384
        }
    },
    "llm": {
        "provider": "groq",
        "config": {
            "model": "llama-3.3-70b-versatile",
            "api_key": groq_key
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    }
}

memory_instance = None

def get_memory():
    global memory_instance
    if memory_instance is not None:
        return memory_instance
        
    try:
        if groq_key:
            print(f"[MEMORY] Initializing with key: {groq_key[:5]}...")
            memory_instance = Memory.from_config(config)
            print("[MEMORY] Mem0 initialized successfully with real provider.")
            return memory_instance
        else:
            print("[MEMORY] GROQ_API_KEY missing or invalid - Using Mock Memory.")
    except Exception as e:
        print(f"[MEMORY] CRITICAL: Initialization failed: {e}")
        import traceback
        traceback.print_exc()

    # Provide a mock memory object if init fails to prevent crashes
    class MockMemory:
        def add(self, *args, **kwargs): 
            print("[MEMORY-MOCK] Add ignored (Initialization failed)")
            pass
        def search(self, *args, **kwargs): 
            print("[MEMORY-MOCK] Search returned [] (Initialization failed)")
            return []
            
    memory_instance = MockMemory()
    return memory_instance
