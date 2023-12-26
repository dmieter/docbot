import os, os.path
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
    collection_name="mpei_docs",
    embedding_function=embeddings
)
print("Size:" + str(vectorstore._collection.count()))

class AnswerQuestion(object):
    @cherrypy.expose
    def index(self, question = "", answer = ""):
        question_title = ' Док, ' if len(question) > 0 else ''
        return """<html>
          <head>
            <link rel="stylesheet" href="static/css/doc.css">
          </head>
          <body>
            <form method="get" action="ask">
              <input type="text" value="" name="question" />
              <button type="submit">Задать вопрос</button>
            </form>
            <img src="static/images/doc-logo.jpg" width="200" height="200" border="-5">
              <p>>{}{}</p>
              <p>> {}</p>
          </body>
        </html>""".format(question_title, question, answer)

    @cherrypy.expose
    def ask(self, question=""):
        trimmed_question = question[:300] if len(question) > 300 else question
        res_docs = vectorstore.similarity_search(trimmed_question)
        return self.index(question, res_docs[0].page_content[:1000])


if __name__ == '__main__':
    work_dir = os.path.abspath(os.getcwd())
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': work_dir
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(work_dir, "docbot", "static"),
        }
    }
    cherrypy.quickstart(AnswerQuestion(), '/', conf)
