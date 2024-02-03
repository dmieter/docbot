from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from langchain.vectorstores import Chroma
from langchain.chat_models import GigaChat
from langchain import hub
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables import RunnableParallel
from langchain.prompts import PromptTemplate
from langchain.chains import create_citation_fuzzy_match_chain

from langchain.schema.vectorstore import VectorStoreRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema.document import Document
from typing import List

from datetime import datetime

#MBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CONTEXT_DOC_NUMBER = 5
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDINGS_MODEL = "cointegrated/rubert-tiny2"

prompt_template_eng = """Use the following pieces of context to answer the question at the end.
      If you don't know the answer, just say that you don't know, don't try to make up an answer.
      The answer should be as concise as possible and contain some details from the documents.
      Your answer is really important for the state education!
      {context}
      Question: {question}
      Helpful Answer:"""
prompt_template_ru = """Действуй как высококлассный юрист-специалист и используй для ответа на вопрос приведенные ниже документы.
      Ответ должен содержать максимум подробностей из приведенных документов.
      От точности ответа зависит качество образования в стране!
      Документы: {context}
      Вопрос: {question}; В каких документах можно найти детали?
      Ответ специалиста:"""

prompt_mpei_orders = """Действуй как высококлассный юрист-секретарь кафедры и используй для ответа на вопрос приведенные ниже документы.
      От подробности ответа зависит качество образования в стране!
      Если данных для ответа не хватает, то дай рекомендацию, как лучше уточнить вопрос.
      Документы: {context}
      Вопрос: {question}; В каком приказе можно посмотреть детали?
      Ответ специалиста:"""

prompt_obr_pravo = """Действуй как высококлассный юрист-специалист и используй для ответа на вопрос приведенные ниже документы.
      Если данных для ответа не хватает, то дай рекомендацию, как лучше уточнить вопрос.
      Ответ должен содержать максимум подробностей из приведенных документов.
      От точности ответа зависит качество образования в стране!
      Документы: {context}
      Вопрос: {question}; В каком документе можно посмотреть детали?
      Ответ специалиста:"""

prompts = {"general" : prompt_template_ru, "mpei_orders" : prompt_mpei_orders, "obr_pravo" : prompt_obr_pravo}

#custom_prompt = PromptTemplate.from_template(prompt_template_ru)
#obrpravo_prompt = PromptTemplate.from_template(prompt_obr_pravo)


class MyVectorStoreRetriever(VectorStoreRetriever):
    # See https://github.com/langchain-ai/langchain/blob/61dd92f8215daef3d9cf1734b0d1f8c70c1571c3/libs/langchain/langchain/vectorstores/base.py#L500
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        docs_and_similarities = (
            self.vectorstore.similarity_search_with_relevance_scores(
                query, **self.search_kwargs
            )
        )

        # Make the score part of the document metadata
        for doc, similarity in docs_and_similarities:
            doc.metadata["score"] = similarity
            doc.metadata["len"] = len(doc.page_content)

        retrieved_docs = [doc for doc, _ in docs_and_similarities]
        result_docs = []
        
        score_num = self.search_kwargs["s"]
        time_num = self.search_kwargs["t"]
        
        if len(retrieved_docs) > score_num and len(retrieved_docs) > time_num:
            docs_by_score = retrieved_docs
            result_docs.extend(docs_by_score[:score_num])
            
            docs_by_date = sorted(docs_by_score[score_num:], key=lambda d: d.metadata['date'], reverse=True) 
            result_docs.extend(docs_by_date[:time_num])
        
        
        else:
            result_docs = retrieved_docs
        
        return result_docs

    


QA_COURCES_DICT = {}

def get_doc_with_description(doc):
    return "Название Документа: {} от {}\n Содержимое:{}".format(doc.metadata['name'], doc.metadata['date'], doc.page_content)

def format_docs(docs):
    head = "Сегодня {}\n =================== \n".format(datetime.today().strftime('%Y%m%d'))
    docs_num = CONTEXT_DOC_NUMBER if (len(docs) > CONTEXT_DOC_NUMBER) else len(docs)
    formatted_docs = head + "\n =================== \n".join(get_doc_with_description(docs[i]) for i in range(docs_num))
    print(formatted_docs)
    return formatted_docs


embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
llm = GigaChat(verify_ssl_certs=False)  

                                                                    # retrieve r_k with score > threshold, pick r_s by score and then r_t by time
def prepareAnswerChain(db_path, collection_name, embeddings, llm, prompt, threshold=0.185, k = 4, s = 2, t = 1):
  chroma_client = chromadb.PersistentClient(path=db_path)
  vectorstore = Chroma(
      client=chroma_client,
      collection_name=collection_name,
      embedding_function=embeddings
  )
  print("Size:" + str(vectorstore._collection.count()))
    
  #retriever = vectorstore.as_retriever()      
  retriever = MyVectorStoreRetriever(
    vectorstore=vectorstore,
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": threshold, "k": k, "s" : s, "t" : t}, # retrieve k with score > threshold, pick s by score and then t by time
  )

  rag_chain = (
      {"context": retriever | format_docs, "question": RunnablePassthrough()}
      | prompt
      | llm
      | StrOutputParser()
  )


  return rag_chain, retriever


#general_answer_chain = prepareAnswerChain("./chroma_db", "mpei_docs", embeddings, llm, custom_prompt)
#obrpravo_answer_chain = prepareAnswerChain("./chroma_db", "mpei_obrpravo", embeddings, llm, obrpravo_prompt)
