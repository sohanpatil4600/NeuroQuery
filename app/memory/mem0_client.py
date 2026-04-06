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
openai_key = os.getenv("OPENAI_API_KEY")

# Relative path for portability
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
memories_path = os.path.join(base_dir, "memories", "qdrant_storage")

def get_config():
    """
    Dynamically build Mem0 config based on available API keys.
    """
    provider = "groq"
    model = "llama-3.3-70b-versatile"
    api_key = groq_key

    if not groq_key and openai_key:
        provider = "openai"
        model = "gpt-4o"
        api_key = openai_key
        print(f"[MEMORY] Switching provider to {provider} (Groq key missing)")

    return {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": memories_path,
                "collection_name": "agentic_bi_memories_v3",
                "embedding_model_dims": 384 # Always 384 for v3 collection
            }
        },
        "llm": {
            "provider": provider,
            "config": {
                "model": model,
                "api_key": api_key
            }
        },
        "embedder": {
            "provider": "huggingface", # Always use HF to match v3 collection dims
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
        active_key = groq_key or openai_key
        if active_key:
            print(f"[MEMORY] Initializing with key: {active_key[:5]}...")
            config = get_config()
            memory_instance = Memory.from_config(config)
            print(f"[MEMORY] Mem0 initialized successfully with {config['llm']['provider']} provider.")
            return memory_instance
        else:
            print("[MEMORY] No valid API keys found (Groq/OpenAI) - Using Mock Memory.")
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

def clear_long_term_memory(user_id=None):
    """Wipe all memories for a specific user or everyone."""
    memory = get_memory()
    try:
        # Check if it's the real Mem0 or a Mock
        if hasattr(memory, 'reset'):
            memory.reset() 
        elif hasattr(memory, 'delete_all'):
            memory.delete_all(user_id=user_id)
        else:
            print("[MEMORY] Cannot clear: Memory is currently in Mock mode.")
            return False
            
        print(f"[MEMORY] Long-term memory cleared for: {user_id if user_id else 'ALL'}")
        return True
    except Exception as e:
        print(f"[MEMORY] Failed to clear memory: {e}")
        return False
