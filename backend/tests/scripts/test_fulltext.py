import json
from pathlib import Path
from app.config.settings import settings

def test():
    path = Path(settings.chroma_persist_dir).parent / "thresholds" / "threshold_catalog.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    thresholds = {}
    for t in data.get("thresholds", []):
        thresholds[f"threshold_{t['id']}"] = t
        
    queries = ["კანაფის ფისის ნარკოტიკის ზღვრები რაარის"]
    
    for query in queries:
        tokens = query.lower().split()
        scored = []
        for tid, data in thresholds.items():
            text = json.dumps(data, ensure_ascii=False).lower()
            s = 0.0
            for t in tokens:
                if len(t) < 3: continue
                if t in text: s += 1.0
                elif len(t) >= 5 and t[:4] in text: s += 0.8
            if s > 0:
                scored.append((tid, s))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        print(f"Top hits for: {query}")
        for tid, score in scored[:5]:
            print(f"{tid}: {score}")

test()
