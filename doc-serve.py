import cherrypy
from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from langchain.vectorstores import Chroma

EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
vectorstore = Chroma(
    client=chroma_client,
    collection_name="mpei_orders",
    embedding_function=embeddings
)
print("Size:" + str(vectorstore._collection.count()))

class AnswerQuestion(object):
    @cherrypy.expose
    def index(self):
        return """<html>
          <head></head>
          <body>
            <form method="get" action="generate">
              <input type="text" value="" name="question" />
              <button type="submit">Initiate the sending...</button>
            </form>
          </body>
        </html>"""

    @cherrypy.expose
    def generate(self, question=""):
        res_docs = vectorstore.similarity_search(question)
        return "Answer for {} is: {}".format(question, res_docs[0].page_content)


if __name__ == '__main__':
    cherrypy.quickstart(AnswerQuestion())
