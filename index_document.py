from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
import pandas as pd
from datetime import datetime
import time

import index_core as ic



# 0. LOAD INPUT ARGUMENTS
DOC_PATH = ic.loadArgument(1, 'pdf/mpei/bars/LecturerInstruction.pdf.txt')
EXPIRE_DAYS = ic.loadArgument(2, 90)
DB_DIR = ic.loadArgument(3, "./chroma_db")
COLLECTION = ic.loadArgument(4, "obr_pravo")
CHUNK_SIZE = ic.loadArgument(5, 1000)
CHUNK_OVERLAP_SIZE = ic.loadArgument(6, 500)

#index_document.py order_15.pdf.txt 60 ./chroma_db mpei_all 1500 300



# 1. LOAD INPUT DOCUMENTS
today = ic.today_str()
current_time_in_seconds = int(time.time())

loader = TextLoader(DOC_PATH)
docs = loader.load()
for doc in docs:
    source_file, source_file_origin = ic.retrieve_filename(doc.metadata['source'])
    doc.metadata['upload_id'] = current_time_in_seconds
    doc.metadata['name'] = source_file_origin
    doc.metadata['date'] = today
    doc.metadata['expire_date'] = ic.date_add_days(today, EXPIRE_DAYS)
                



# 3. SPLIT AND STORE DOCUMENTS

text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP_SIZE)
splits = text_splitter.split_documents(docs)
ic.numberize_splits(splits)
print(len(splits))

from langchain.embeddings import HuggingFaceEmbeddings

#https://www.sbert.net/docs/pretrained_models.html
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDINGS_MODEL = "cointegrated/rubert-tiny2"
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, collection_name=COLLECTION, persist_directory=DB_DIR)