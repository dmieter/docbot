from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from langchain.vectorstores import Chroma
from langchain.chat_models import GigaChat
from langchain import hub
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import PromptTemplate

EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CONTEXT_DOC_NUMBER = 3
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
#EMBEDDINGS_MODEL = "cointegrated/rubert-tiny2"

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


#custom_prompt = PromptTemplate.from_template(prompt_template_ru)
#obrpravo_prompt = PromptTemplate.from_template(prompt_obr_pravo)



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


#general_answer_chain = prepareAnswerChain("./chroma_db", "mpei_docs", embeddings, llm, custom_prompt)
#obrpravo_answer_chain = prepareAnswerChain("./chroma_db", "mpei_obrpravo", embeddings, llm, obrpravo_prompt)
