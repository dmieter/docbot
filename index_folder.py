
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
import chromadb
import pandas as pd
from datetime import datetime
import time

import index_core as ic


# 0. LOAD INPUT ARGUMENTS
INPUT_DIR = ic.loadArgument(1, '../pdf/mpei/obr_pravo/index/')
SUFFIX = ic.loadArgument(2, '.pdf.txt')
CHUNK_SIZE = int(ic.loadArgument(3, 1200))
CHUNK_OVERLAP_SIZE = int(ic.loadArgument(4, 300))
DB_DIR = ic.loadArgument(5, "./chroma_db")
COLLECTION = ic.loadArgument(6, "obr_pravo")
META_FILE_CSV = ic.loadArgument(7, "../pdf/mpei/obr_pravo/index/metadata.csv")

#index_folder.py . .pdf.txt 800 150 ./chroma_db mpei_all metadata.csv

def process_command():

    # 1. LOAD INPUT DOCUMENTS
    current_time_in_seconds = int(time.time())

    loader = DirectoryLoader(INPUT_DIR, glob="**/*" + SUFFIX)
    docs = loader.load()
    docs_to_index = []

    chroma_client = chromadb.PersistentClient(path = DB_DIR)
    collection = chroma_client.get_or_create_collection(name = COLLECTION)

    # 2. PREPARE METADATA FOR DOCUMENTS

    if len(META_FILE_CSV) > 0:     # load only documents described in metadata csv
        print("Setting metadata from " + META_FILE_CSV)
        df_metadata = pd.read_csv(META_FILE_CSV, names=["date", "expire_date", "filename", "name", "url"], delimiter=";")
        for doc in docs:
            source_file, source_file_origin = ic.retrieve_filename(doc.metadata['source'])
            metadata = df_metadata[(df_metadata.filename == source_file) | (df_metadata.filename == source_file_origin)]
            if metadata.size > 0: # load only those files presented in metadata csv
                metadata = metadata.iloc[0]

                if not ic.check_already_indexed(metadata['name'], collection): # skip already indexd files
                    doc.metadata['upload_id'] = current_time_in_seconds
                    doc.metadata['name'] = metadata['name']
                    doc.metadata['date'] = str(metadata['date'])
                    doc.metadata['expire_date'] = str(metadata['expire_date'])
                    doc.metadata['url'] = str(metadata['url'])
                    docs_to_index.append(doc)
                else:
                    print("File {} already indexed in {}".format(metadata['name'], COLLECTION))   

    else:   # load all documents with default metadata
        today = ic.today_str()
        print("Setting simple metadata for " + today)
        docs_to_index = docs
        for doc in docs_to_index:
            source_file, source_file_origin = ic.retrieve_filename(doc.metadata['source'])
            if not ic.check_already_indexed(source_file_origin, collection):
                doc.metadata['upload_id'] = current_time_in_seconds
                doc.metadata['name'] = source_file_origin
                doc.metadata['date'] = today
                doc.metadata['expire_date'] = ic.date_add_days(today, 90) # 3 monthes expiration by default
            else:
                print("File {} already indexed in {}".format(source_file), COLLECTION)
                    



    # 3. SPLIT AND STORE DOCUMENTS

    print(len(docs_to_index))
    if(len(docs_to_index) > 0):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP_SIZE)
        splits = text_splitter.split_documents(docs_to_index)
        ic.numberize_splits(splits)
        print(len(splits))

        from langchain.embeddings import HuggingFaceEmbeddings

        #https://www.sbert.net/docs/pretrained_models.html
        #EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        EMBEDDINGS_MODEL = "cointegrated/rubert-tiny2"
        #EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
        vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, collection_name=COLLECTION, persist_directory=DB_DIR)



process_command()
