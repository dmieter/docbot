import chromadb
import index_core as ic

DB_DIR = ic.loadArgument(1, "./chroma_db")


chroma_client = chromadb.PersistentClient(path="./chroma_db")
coll = chroma_client.list_collections()[0].get()



for collection in chroma_client.list_collections():
    ids_to_remove = []
    coll = collection.get()
    
    for idx in range(len(coll['ids'])):

        id = coll['ids'][idx]
        metadata = coll['metadatas'][idx]
        expire_date_str = metadata['expire_date']

        if not expire_date_str or len(expire_date_str) == 0:  # expire_date not set
            continue

        today = ic.today_str()
        if expire_date_str < today:
            ids_to_remove.append(id)

    print("Removing expired ids {} from collection {}".format(ids_to_remove, collection))
    collection.delete(ids_to_remove)
