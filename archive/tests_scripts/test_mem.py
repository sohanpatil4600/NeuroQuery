from app.memory.mem0_client import memory
print("Memory Object:", memory)
if "MockMemory" not in str(type(memory)):
    memory.add("User Question: Remember that my absolute favorite product to track is the Hardware Key. | AI Insight: Okay.", user_id="u1")
    res = memory.search("What is my favorite product?", user_id="u1")
    print("Search Result:", res)
