from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

import chromadb
from data import index_core as ic

import time

DB_DIR = "./chroma_db"


def index_dpo_file(dpo_file, collection_name, rm_collection = False, db_dir = DB_DIR):
    chroma_client = chromadb.PersistentClient(path=db_dir)

    if rm_collection:
        if ic.check_collection_exists(chroma_client, collection_name):
            chroma_client.delete_collection(collection_name)
            print("Collection {} removed".format(collection_name))
        else:
            print("Collection {} not found".format(collection_name))    

    
    today = ic.today_str()
    current_time_in_seconds = int(time.time())
    loader = TextLoader(dpo_file)
    doc = loader.load()[0]
    doc.metadata['upload_id'] = current_time_in_seconds
    doc.metadata['name'] = dpo_file
    doc.metadata['date'] = today
    doc.metadata['date_int'] = int(today.replace('-', ''))
    doc.metadata['expire_date'] = ic.date_add_days(today, 365) # 1 year expiration by default

    text_splitter = CharacterTextSplitter(chunk_size=0, chunk_overlap=0, separator=r"={5,}", is_separator_regex=True)   # separator is 5= and more (=====)
    splits = text_splitter.split_documents([doc])
    ic.numberize_splits(splits)
    print(len(splits))
    EMBEDDINGS_MODEL = "cointegrated/rubert-tiny2"
    #EMBEDDINGS_MODEL = "ai-forever/sbert_large_nlu_ru"
    #EMBEDDINGS_MODEL = "cointegrated/LaBSE-en-ru"
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, collection_name=collection_name, persist_directory=DB_DIR)


#PATH = 'upload/dpo/'
#index_dpo_file(PATH + "/dpo_stats_excel.txt", "dpo_stats", True)