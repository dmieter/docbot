import sys
import chromadb
from datetime import datetime
from datetime import timedelta
import re

def loadArgument(number, default):
    if len(sys.argv) > number:
        return sys.argv[number]
    else:
        return default

def retrieve_filename(filepath):
    source_file = filepath.split("/")[-1]
    source_file_origin= re.sub(".txt$", "", source_file)
    return source_file, source_file_origin

def today_str():
    return datetime.today().strftime('%Y-%m-%d')

def date_add_days(date_str, days):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_plus = date_obj + timedelta(days)
    return date_plus.strftime('%Y-%m-%d')

def check_already_indexed(filename, persist_directory, collection_name):
    chroma_client = chromadb.PersistentClient(path = persist_directory)
    collection = chroma_client.get_collection(name = collection_name)

    if collection:
        metadatas = collection.get()['metadatas']
        for metadata in metadatas:
            if filename == metadata['name']:
                return True

    return False

def check_collection_exists(db, collection_name):
    collections = db.list_collections()
    for collection in collections:
        if collection_name == collection.name:
            return True

    return False    

def numberize_splits(splits):
    previous_doc = ""
    page_counter = 0
    for split in splits:
        
        split.metadata["page_len"] = len(split.page_content)

        if previous_doc != split.metadata["name"]:
            page_counter = 0
            previous_doc = split.metadata["name"]
            split.metadata["page_num"] = page_counter
        else:
            split.metadata["page_num"] = page_counter
        
        page_counter += 1

        #print("{}: {} ({})".format(split.metadata["page_num"],split.page_content[:20], split.metadata["name"]))


def check_already_indexed(filename, collection):
    #chroma_client = chromadb.PersistentClient(path = persist_directory)
    #collection = chroma_client.get_collection(name = collection_name)

    if collection:
        metadatas = collection.get()['metadatas']
        for metadata in metadatas:
            print(metadata['name'])
            print(filename)
            if filename == metadata['name']:
                return True

    return False
#check_already_indexed('hello', 'chroma_db', 'obr_pravo');