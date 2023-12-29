import os, os.path
import cherrypy
from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from langchain.vectorstores import Chroma
from langchain.chat_models import GigaChat
from langchain import hub
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import PromptTemplate

GENERAL_EXPERTISE = 'general'
OBR_PRAVO_EXPERTISE = 'obr_pravo'
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CONTEXT_DOC_NUMBER = 3
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

prompt_template_eng = """Use the following pieces of context to answer the question at the end.
      If you don't know the answer, just say that you don't know, don't try to make up an answer.
      The answer should be as concise as possible and contain some details from the documents.
      Your answer is really important for the state education!
      {context}
      Question: {question}
      Helpful Answer:"""
prompt_template_ru = """Действуй как секретарь кафедры технического университета.
      Используй для ответа на вопрос приведенные ниже документы.
      Если данных для ответа не хватает, то явно укажи на это в ответе.
      Добавь в ответ дополнительные релевантные подробности из документов.
      От точности ответа зависит качество образования в стране!
      Документы: {context}
      Вопрос: {question}
      Ответ секретаря:"""
prompt_obr_pravo = """Действуй как юрист-специалист и используй для ответа на вопрос приведенные ниже документы.
      Если данных для ответа не хватает, то дай рекомендацию, как лучше уточнить вопрос.
      Ответ должен содержать максимум подробностей из приведенных документов.
      От точности ответа зависит качество образования в стране!
      Документы: {context}
      Вопрос: {question}
      Ответ специалиста:"""


custom_prompt = PromptTemplate.from_template(prompt_template_ru)
obrpravo_prompt = PromptTemplate.from_template(prompt_obr_pravo)



def format_docs(docs):
    docs_num = CONTEXT_DOC_NUMBER if (len(docs) > CONTEXT_DOC_NUMBER) else len(docs)
    return "\n =================== \n".join(docs[i].page_content for i in range(docs_num))


embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
llm = GigaChat(verify_ssl_certs=False)  
def prepareAnswerChain(db_path, collection_name, embeddings, llm, prompt):
  chroma_client = chromadb.PersistentClient(path=db_path)
  vectorstore = Chroma(
      client=chroma_client,
      collection_name=collection_name,
      embedding_function=embeddings
  )
  print("Size:" + str(vectorstore._collection.count()))

  retriever = vectorstore.as_retriever()      
  rag_chain = (
      {"context": retriever | format_docs, "question": RunnablePassthrough()}
      | prompt
      | llm
      | StrOutputParser()
  )

  return rag_chain


general_answer_chain = prepareAnswerChain("./chroma_db", "mpei_docs", embeddings, llm, custom_prompt)
obrpravo_answer_chain = prepareAnswerChain("./chroma_db", "mpei_obrpravo", embeddings, llm, obrpravo_prompt)


test_chroma_client = chromadb.PersistentClient(path="./chroma_db")
test_vectorstore = Chroma(
    client=test_chroma_client,
    collection_name="mpei_obrpravo",
    embedding_function=embeddings
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
    
    def answer(self, question, expert):
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
