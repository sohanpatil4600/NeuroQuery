import sys
from app.memory.mem0_client import get_memory

def run():
    print("Initializing memory...")
    try:
        mem = get_memory()
        print("Memory Instance:", type(mem))
        if "Mock" not in str(type(mem)):
            print("Fetching all memories for user 'u1'...")
            results = mem.search("favorite product", user_id="u1")
            import json
            print(json.dumps(results, default=str, indent=2))
        else:
            print("System defaulted to MockMemory.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
