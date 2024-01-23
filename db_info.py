
import chromadb
import index_core as ic



# 0. LOAD INPUT ARGUMENTS
COMMAND = ic.loadArgument(1, "data")
DB_DIR = ic.loadArgument(2, "./docbot/chroma_db")
COLLECTION = ic.loadArgument(3, "mpei-new-orders")

#index_document.py order_15.pdf.txt 60 ./chroma_db mpei_all 1500 300


chroma_client = chromadb.PersistentClient(path = DB_DIR)


def process_command():

    if 'LIST' == COMMAND.upper():
        collections = chroma_client.list_collections()
        names = [col.name for col in collections]
        names.sort()
        for name in names:
            print(name)
        return
        
    
    collection = chroma_client.get_or_create_collection(name = COLLECTION)
    data = collection.get()
    
    output = set()
    
    if 'DATA' == COMMAND.upper():
        for metadata in data['metadatas']:
            output.add("{};{};{}".format(metadata['date'], metadata['expire_date'], metadata['name']))

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
    
    if 'EXPIRE' == COMMAND.upper():
        for metadata in data['metadatas']:
            output.add("{};{}".format(metadata['expire_date'], metadata['name']))

        output = sorted(output)
        for line in output:
            print(line)
        return
    
    if 'EXPIRED' == COMMAND.upper():
        today = ic.today_str()
        for metadata in data['metadatas']:
            if today > metadata['expire_date']:
                output.add("{};{}".format(metadata['expire_date'], metadata['name']))

        output = sorted(output)
        for line in output:
            print(line)
        return


    

process_command()    
