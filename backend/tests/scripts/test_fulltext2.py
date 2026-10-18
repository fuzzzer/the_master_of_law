import json
from pathlib import Path
from app.config.settings import settings
from app.services.rag_retrieval_service import get_rag_service

def test():
    rag = get_rag_service()
    index = rag._load_article_index()
        
    queries = ["კანაფის ფისის ნარკოტიკის ზღვრები რაარის"]
    
    for query in queries:
        tokens = query.lower().split()
        scored = []
        for aid, data in index.items():
            text = json.dumps(data, ensure_ascii=False).lower() if isinstance(data, dict) else str(data).lower()
            s = 0.0
            for t in tokens:
                if len(t) < 3: continue
                if t in text: s += 1.0
                elif len(t) >= 5 and t[:4] in text: s += 0.8
            if s > 0:
                scored.append((aid, s))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        print(f"Top article hits for: {query}")
        for aid, score in scored[:10]:
            print(f"{aid}: {score}")

test()
