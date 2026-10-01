import chromadb
from google import genai
import json

client = chromadb.PersistentClient(path="/Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/law_corpus/data/chroma")
coll = client.get_collection("georgian_laws")
results = coll.query(query_texts=["კანაფის ფისის ნარკოტიკის ზღვრები რაარის"], n_results=5)
for i in range(len(results["ids"][0])):
    print(f"ID: {results['ids'][0][i]}")
    print(f"Metadata: {results['metadatas'][0][i]}")
    print(f"Content: {results['documents'][0][i][:200]}")
    print("-" * 50)
