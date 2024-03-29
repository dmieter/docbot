
import chromadb
import index_core as ic



# 0. LOAD INPUT ARGUMENTS
COMMAND = ic.loadArgument(1, "doc") # list/data/docs/expire/expired
DB_DIR = ic.loadArgument(2, "./chroma_db")
COLLECTION = ic.loadArgument(3, "internal_knowledge")
DOC_ID = ic.loadArgument(4, "f1fd1772-c8ae-11ee-a602-d70abbf3fc2e")


chroma_client = chromadb.PersistentClient(path = DB_DIR)


def process_command():


    if 'LIST' == COMMAND.upper():
        collections = chroma_client.list_collections()
        names = [col.name for col in collections]
        names.sort()
        for name in names:
            print(name)
        return
        
    

    if not ic.check_collection_exists(chroma_client, COLLECTION):
        return
    
    collection = chroma_client.get_collection(name = COLLECTION)
    data = collection.get()
    
    output = set()
    
    if 'DATA' == COMMAND.upper():
        for idx in range(len(data['ids'])):

            id = data['ids'][idx]
            metadata = data['metadatas'][idx]

            url = metadata['url'] if 'url' in metadata.keys() else ''
            expire_date = metadata['expire_date'] if 'expire_date' in metadata.keys() else ''
            output.add("{} {};{};{};{}".format(id, metadata['date'], expire_date, metadata['name'], url))

        output = sorted(output)
        for line in output:
            print(line)
        return

    if 'DOCS' == COMMAND.upper():
        for metadata in data['metadatas']:
            output.add("{};{}".format(metadata['date'], metadata['name']))

        output = sorted(output)
        for line in output:
            print(line)
        return
    
    if 'DOC' == COMMAND.upper():
        print(collection.get(ids=[DOC_ID]))
        return
    
    if 'EXPIRED' == COMMAND.upper():
        today = ic.today_str()
        for metadata in data['metadatas']:
            if 'expire_date' in metadata.keys() and today > metadata['expire_date']:
                output.add("{};{}".format(metadata['expire_date'], metadata['name']))

        output = sorted(output)
        for line in output:
            print(line)
        return

    if 'EXPIRE' == COMMAND.upper():
        for metadata in data['metadatas']:
            expire_date = metadata['expire_date'] if 'expire_date' in metadata.keys() else '2100-01-01'
            output.add("{};{}".format(expire_date, metadata['name']))

        output = sorted(output)
        for line in output:
            print(line)
        return
    

process_command()    
