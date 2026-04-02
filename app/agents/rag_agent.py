import os
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer

# Lazy load Embedder to avoid blocking startup
embedder = None
glossary_lines = []
glossary_embeddings = None

def init_rag():
    global embedder, glossary_lines, glossary_embeddings
    if embedder is None:
        try:
            print("[RAG] Initializing Knowledge Base Embedder...")
            embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Load business glossary
            glossary_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'business_glossary.txt')
            if os.path.exists(glossary_path):
                with open(glossary_path, 'r', encoding='utf-8') as f:
                    glossary_lines = [line.strip() for line in f if line.strip()]
                
                if glossary_lines:
                    print(f"[RAG] Embedding {len(glossary_lines)} business rules in-memory...")
                    glossary_embeddings = embedder.encode(glossary_lines, convert_to_tensor=True)
            else:
                print(f"[RAG] Warning: Glossary file not found at {glossary_path}")
        except Exception as e:
            print(f"[RAG] Critical Error during init: {e}")
            embedder = "FAILED"

def run(state):
    try:
        init_rag()
        question = state.get("question", "")
        
        # If embedder failed or no constraints, skip
        if embedder == "FAILED" or not glossary_lines or not question:
            state['rag_context'] = ""
            return state

        # Embed question
        q_emb = embedder.encode(question, convert_to_tensor=True)
        
        # Calculate cosine similarity against all rules
        cos_scores = F.cosine_similarity(q_emb.unsqueeze(0), glossary_embeddings)
        
        # Get top 3 most relevant rules
        top_k = min(3, len(glossary_lines))
        top_results = torch.topk(cos_scores, k=top_k)
        
        rel_rules = []
        for score, idx in zip(top_results[0], top_results[1]):
            # Threshold ensures we only inject relevant rules
            if score.item() > 0.2: 
                rel_rules.append(glossary_lines[idx])
                
        if rel_rules:
            state['rag_context'] = "Business Definitions from RAG:\n" + "\n".join(rel_rules)
            print(f"[RAG] Appended {len(rel_rules)} context rules.")
        else:
            state['rag_context'] = ""
            
    except Exception as e:
        print(f"[RAG] Runtime Error: {e}")
        state['rag_context'] = ""
        
    return state
