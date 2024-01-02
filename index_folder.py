import sys
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

def loadArgument(number, default):
    if len(sys.argv) > number:
        return sys.argv[number]
    else:
        return default
    

INPUT_DIR = loadArgument(1, '.')
EXTENSION = loadArgument(2, 'txt')
CHUNK_SIZE = loadArgument(3, 800)
CHUNK_OVERLAP_SIZE = loadArgument(4, 150)
DB_DIR = loadArgument(5, "./chroma_db")
COLLECTION = loadArgument(6, "general")

#index_folder.py . txt 800 150 ./chroma_db mpei_all

loader = DirectoryLoader(INPUT_DIR, glob="**/*." + EXTENSION)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP_SIZE)
splits = text_splitter.split_documents(docs)

from langchain.embeddings import HuggingFaceEmbeddings

#https://www.sbert.net/docs/pretrained_models.html
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, collection_name=COLLECTION, persist_directory=DB_DIR)