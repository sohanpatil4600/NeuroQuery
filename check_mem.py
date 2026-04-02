import sys
import traceback
from app.memory.mem0_client import get_memory

def run():
    print("Initializing memory...")
    try:
        mem = get_memory()
        print("Memory Instance:", type(mem))
        if "Mock" not in str(type(mem)):
            print("Adding memory...")
            mem.add("My favorite product is the Hardware Key", user_id="u1")
            print("Searching memory...")
            results = mem.search("What is my favorite product?", user_id="u1")
            print("Search Results:", results)
        else:
            print("System defaulted to MockMemory.")
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    run()
