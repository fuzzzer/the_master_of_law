from app.integrations.chroma_client import get_chroma_client

def test():
    client = get_chroma_client()
    res = client.get_by_ids(["threshold_drug_narcotics_76"])
    if not res:
        print("Not found in ChromaDB!")
    else:
        for r in res:
            print("Found:", r["chunk_id"])
            print("Content:", r["content"][:200])

test()
