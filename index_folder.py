import sys
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
import pandas as pd
from datetime import datetime
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


# 0. LOAD INPUT ARGUMENTS
INPUT_DIR = loadArgument(1, './pdf/mpei/obr_pravo/index/')
SUFFIX = loadArgument(2, '.pdf.txt')
CHUNK_SIZE = loadArgument(3, 1500)
CHUNK_OVERLAP_SIZE = loadArgument(4, 350)
DB_DIR = loadArgument(5, "./chroma_db_6")
COLLECTION = loadArgument(6, "obr_pravo")
META_FILE_CSV = loadArgument(7, "./pdf/mpei/obr_pravo/index/metadata.csv")

#index_folder.py . .pdf.txt 800 150 ./chroma_db mpei_all metadata.csv



# 1. LOAD INPUT DOCUMENTS

loader = DirectoryLoader(INPUT_DIR, glob="**/*" + SUFFIX)
docs = loader.load()
docs_to_index = []


# 2. PREPARE METADATA FOR DOCUMENTS

if len(META_FILE_CSV) > 0:     # load only documents described in metadata csv
    print("Setting metadata from " + META_FILE_CSV)
    df_metadata = pd.read_csv(META_FILE_CSV, names=["date", "filename", "name", "url"], delimiter=";")
    for doc in docs:
        source_file, source_file_origin = retrieve_filename(doc.metadata['source'])
        metadata = df_metadata[(df_metadata.filename == source_file) | (df_metadata.filename == source_file_origin)]
        if metadata.size > 0:
            metadata_entry = metadata.iloc[0]
            doc.metadata['name'] = metadata_entry['name']
            doc.metadata['date'] = str(metadata_entry['date'])
            docs_to_index.append(doc)

else:   # load all documents with default metadata
    today = datetime.today().strftime('%Y%m%d')
    print("Setting simple metadata for " + today)
    docs_to_index = docs
    for doc in docs_to_index:
        source_file, source_file_origin = retrieve_filename(doc.metadata['source'])
        doc.metadata['name'] = source_file_origin
        doc.metadata['date'] = today
                



# 3. SPLIT AND STORE DOCUMENTS

print(len(docs_to_index))
text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP_SIZE)
splits = text_splitter.split_documents(docs_to_index)
print(len(splits))

from langchain.embeddings import HuggingFaceEmbeddings

#https://www.sbert.net/docs/pretrained_models.html
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDINGS_MODEL = "cointegrated/rubert-tiny2"
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, collection_name=COLLECTION, persist_directory=DB_DIR)