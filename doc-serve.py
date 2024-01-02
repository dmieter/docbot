import os, os.path
import cherrypy
from langchain.prompts import PromptTemplate
import chromadb
from langchain.vectorstores import Chroma
import doc_core as dc

GENERAL_EXPERTISE = 'general'
OBR_PRAVO_EXPERTISE = 'obr_pravo' 
custom_prompt = PromptTemplate.from_template(dc.prompt_template_ru)
obrpravo_prompt = PromptTemplate.from_template(dc.prompt_obr_pravo)

general_answer_chain = dc.prepareAnswerChain("./chroma_db", "mpei_docs", dc.embeddings, dc.llm, custom_prompt)
obrpravo_answer_chain = dc.prepareAnswerChain("./chroma_db", "mpei_obrpravo", dc.embeddings, dc.llm, obrpravo_prompt)


test_chroma_client = chromadb.PersistentClient(path="./chroma_db")
test_vectorstore = Chroma(
    client=test_chroma_client,
    collection_name="mpei_obrpravo",
    embedding_function=dc.embeddings
)


class AnswerQuestion(object):
    @cherrypy.expose
    def index(self, question = "", answer = ""):
        question_title = ' Док, ' if len(question) > 0 else ''
        return """<html>
          <head>
            <link rel="stylesheet" href="static/css/doc.css">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
          </head>
          <body>
            <form method="get" action="ask">
              <label for="expert">Область знаний:</label>
              <select id="expert" name="expert">
                <option value="obr_pravo">Образовательное право</option>
                <option value="general">Общие знания</option>
              </select>
              <br>
              <input type="text" value="" name="question" />
              <button type="submit">Задать вопрос</button>
            </form>
            <img src="static/images/doc-logo.jpg" width="200" height="200" border="-5">
              <p>>{}{}</p>
              <p>> {}</p>
          </body>
        </html>""".format(question_title, question, answer)

    @cherrypy.expose
    def ask(self, question="", expert = 'general'):
        trimmed_question = question[:300] if len(question) > 300 else question
        #res_docs = test_vectorstore.similarity_search(trimmed_question)
        #return self.index(question, expert + ": " +res_docs[0].page_content[:1000])

        answer = self.answer(trimmed_question, expert)
        return self.index(question, answer)
    
    def answer(self, question, expert = OBR_PRAVO_EXPERTISE):
        if expert == OBR_PRAVO_EXPERTISE:
          return expert + ": " + obrpravo_answer_chain.invoke(question)
        else:
          return expert + ": " + general_answer_chain.invoke(question)



if __name__ == '__main__':
    work_dir = os.path.abspath(os.getcwd())
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': work_dir
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(work_dir, "static"),
        }
    }
    cherrypy.quickstart(AnswerQuestion(), '/', conf)
