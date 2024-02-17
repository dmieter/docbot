import chromadb
import index_core as ic

#COMMAND = ic.loadArgument(1, "rm_col")         #expire/doc/created/rm_col
DB_DIR = ic.loadArgument(2, "./chroma_db")
#FILTER = ic.loadArgument(3, "mpei_orders")
#COLLECTION = ic.loadArgument(4, "")

COMMAND = ic.loadArgument(1, "doc")
FILTER = ic.loadArgument(3, "ПРИКАЗ от 14 февраля 2024 года № 117")
COLLECTION = ic.loadArgument(4, "mpei_orders")

def process_command():

    chroma_client = chromadb.PersistentClient(path=DB_DIR)

    if 'RM_COL' == COMMAND.upper():         # REMOVE WHOLE COLLECTION
        if ic.check_collection_exists(chroma_client, FILTER):
            chroma_client.delete_collection(FILTER)
            print("Collection {} removed".format(FILTER))
        else:
            print("Collection {} not found".format(FILTER))    
        return


    for collection in chroma_client.list_collections():

        if len(COLLECTION) > 0 and COLLECTION != collection.name:   # process specific collection if specified
            continue

        ids_to_remove = []
        coll = collection.get()
        
        for idx in range(len(coll['ids'])):

            id = coll['ids'][idx]
            metadata = coll['metadatas'][idx]

            if 'EXPIRE' == COMMAND.upper():     # REMOVE ALL EXPIRED DOCUMENTS

                if not 'expire_date' in metadata.keys(): # expire_date not set
                    continue

                expire_date_str = metadata['expire_date']
                today = ic.today_str()
                if expire_date_str < today:
                    ids_to_remove.append(id)
                
                continue    

            if 'DOC' == COMMAND.upper():        # REMOVE DOCUMENTS BY NAME

                if FILTER == metadata['name']:
                    ids_to_remove.append(id)
                
                continue 

            if 'CREATED' == COMMAND.upper():    # REMOVE DOCUMENTS CREATED BEFORE DATE

                if metadata['date'] < FILTER:
                    ids_to_remove.append(id)
                
                continue   

        print("Removing ids {} from collection {} according to command {}".format(ids_to_remove, collection.name, COMMAND))
        if len(ids_to_remove) > 0:
            collection.delete(ids_to_remove)


process_command()