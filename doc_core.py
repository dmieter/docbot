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
from langchain.retrievers import BM25Retriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema.document import Document
from typing import List

import yaml
import string
from datetime import datetime

MAX_CONTEXT_DOC_NUMBER = 100 # maximum number of docs for llm
MAX_RELATED_DOCS_NUMBER = 5 # maximum number of neighbour docs (radius)

#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDINGS_MODEL = "cointegrated/rubert-tiny2"
#EMBEDDINGS_MODEL = "ai-forever/sbert_large_nlu_ru"
#EMBEDDINGS_MODEL = "cointegrated/LaBSE-en-ru"

prompt_template_eng = """Use the following pieces of context to answer the question at the end.
      If you don't know the answer, just say that you don't know, don't try to make up an answer.
      The answer should be as concise as possible and contain some details from the documents.
      Your answer is really important for the state education!
      {context}
      Question: {question}
      Helpful Answer:"""
prompt_template_ru = """Действуй как высококлассный юрист-специалист и используй для ответа на вопрос приведенные ниже документы.
      От точности и подробности ответа зависит качество образования в стране!
      Документы: {context}
      Вопрос: {question}; расскажи подробности. В каких документах можно посмотреть дополнительные детали?
      Ответ специалиста:"""

prompt_mpei_orders = """Действуй как высококлассный юрист-секретарь кафедры и используй для ответа на вопрос приведенные ниже документы.
      От подробности ответа зависит качество образования в стране!
      Если данных для ответа не хватает, то дай рекомендацию, как лучше уточнить вопрос.
      Документы: {context}
      Вопрос: {question}; расскажи подробности. В каком приказе можно посмотреть детали? 
      Ответ специалиста:"""

prompt_dpo = """Действуй как педантный консультант-секретарь кафедры Университета МЭИ.
      Используй для ответа следующие данные: {context}.
      В ответе уточни,тип программы: повышения квалификации или профессиональной переподготовки.
      Вопрос: {question}.
      На утверждения без вопроса, вопросы не по теме обучения, благодарности, привествия и тому подобное отвечай кратко, формально и вежливо.
      При наличии вопроса по возможности приведи соответствующую, но краткую информацию о подходящих программах с указанием полного названия.
      Твой ответ:"""

prompt_obr_pravo = """Действуй как высококлассный юрист-специалист и используй для ответа на вопрос приведенные ниже документы.
      Если данных для ответа не хватает, то дай рекомендацию, как лучше уточнить вопрос.
      Ответ должен содержать максимум подробностей из приведенных документов.
      От точности ответа зависит качество образования в стране!
      Документы: {context}
      Вопрос: {question}; В каком документе можно посмотреть детали?
      Ответ специалиста:"""

prompts = {"general" : prompt_template_ru, "mpei_orders" : prompt_mpei_orders, "obr_pravo" : prompt_obr_pravo, "prompt_dpo" : prompt_dpo}

#custom_prompt = PromptTemplate.from_template(prompt_template_ru)
#obrpravo_prompt = PromptTemplate.from_template(prompt_obr_pravo)

def load_properties_file():
  with open('config/properties.yml', 'r') as file:
      properties = yaml.safe_load(file)
      print("properties loaded: {}".format(properties))

  return properties    

properties = load_properties_file()

def tokenize(s: str) -> list[str]:
    """Очень простая функция разбития предложения на слова"""
    return s.lower().translate(str.maketrans("", "", string.punctuation)).split(" ")

class MyVectorStoreRetriever(VectorStoreRetriever):
    # See https://github.com/langchain-ai/langchain/blob/61dd92f8215daef3d9cf1734b0d1f8c70c1571c3/libs/langchain/langchain/vectorstores/base.py#L500
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        chroma_valid_parameters = {'k', 'score_threshold'}
        choma_search_kwargs = {k: v for k, v in self.search_kwargs.items() if k in chroma_valid_parameters}
        docs_and_similarities = (
            self.vectorstore.similarity_search_with_relevance_scores(
                query, **choma_search_kwargs
            )
        )

        # Make the score part of the document metadata
        for doc, similarity in docs_and_similarities:
            doc.metadata["score"] = similarity
            doc.metadata["len"] = len(doc.page_content)

        retrieved_docs = self.select_best(docs_and_similarities)

        # additionally search documents by different text search algorithm (without embeddings)
        if "bm25" in self.search_kwargs.keys():
            bm25_args = self.search_kwargs["bm25"].split("/")
            select_num = int(bm25_args[0])
            select_from_num = int(bm25_args[1])
            additional_docs = self.select_by_bm25(query, select_num, select_from_num) # additionally select like 3/50 by BM25
            retrieved_docs.extend(additional_docs)

        if "neighbours" in self.search_kwargs.keys():
            result_docs = self.retrieve_with_neighbours(retrieved_docs)
        elif "next" in self.search_kwargs.keys():
            result_docs = self.retrieve_with_next(retrieved_docs)
        else:
            result_docs = retrieved_docs

        #print("context docs: {}".format(result_docs))
        return result_docs    
    
    def select_by_bm25(self, query, select_num, select_from_num):
        similar_docs = self.vectorstore.similarity_search(query, k=select_from_num)
        bm25 = BM25Retriever.from_documents(documents=similar_docs, preprocess_func=tokenize,k=select_num)
        result_docs = bm25.get_relevant_documents(query)

        for doc in result_docs:
            doc.metadata['retriever'] = 'BM25'

        return result_docs


    # returns first s docs by score and first t by time from the rest over threshold
    def select_best(self, docs_and_similarities):
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
        
        for doc in result_docs:
            doc.metadata['retriever'] = 'SIMILARITY'

        return result_docs


    # retrieves best docs with neighbor parts of the same document
    def retrieve_with_neighbours(self, docs_and_similarities):
        neighbours_sizes = self.search_kwargs["neighbours"]
        result_docs = []

        i = 0
        for i, doc in enumerate(docs_and_similarities):
            radius_size = neighbours_sizes[i] if i < len(neighbours_sizes) else 0
            result_docs.extend(self.retrieve_neighbours(doc, radius_size))

        return self.remove_duplicate_docs(result_docs)
    
    def retrieve_with_next(self, docs_and_similarities):
        result_docs = []

        for doc in docs_and_similarities:
            result_docs.extend(self.retrieve_next(doc))

        return self.remove_duplicate_docs(result_docs)

    def retrieve_related_docs(self, doc):

        source_name = doc.metadata['name']
        source_upload_id = doc.metadata['upload_id']
        source_page_num = doc.metadata['page_num']
        related_docs = {}

        data = self.vectorstore.get()
        for idx in range(len(data['ids'])):

            id = data['ids'][idx]
            metadata = data['metadatas'][idx]

            if (
                all(key in metadata.keys() for key in ['name', 'upload_id', 'page_num'])
                and metadata['upload_id'] == source_upload_id
                and metadata['name'] == source_name
                and source_page_num - MAX_RELATED_DOCS_NUMBER < metadata['page_num'] < source_page_num + MAX_RELATED_DOCS_NUMBER 
            ):
                related_docs[metadata['page_num']] = Document(page_content=data['documents'][idx],
                                                              metadata=metadata)
                
        return related_docs
            
    def retrieve_neighbours(self, doc, half_size):
        if not all(key in doc.metadata.keys() for key in ['name', 'upload_id', 'page_num']):
            return [doc]
        
        # get docs from the same document and upload_id (to get relevant pages)
        related_docs = self.retrieve_related_docs(doc)

        neighbor_docs = []
        source_page_num = doc.metadata['page_num']
        before_sum, after_sum = 0, 0

        # get docs before page_num up to half_size in total
        added = True
        page_counter = source_page_num
        while(added):
            added = False
            page_counter -= 1
            if page_counter in related_docs.keys():
                neighbour_doc = related_docs[page_counter]
                if neighbour_doc.metadata['page_len'] + before_sum < half_size:
                    neighbor_docs.append(neighbour_doc)
                    before_sum += neighbour_doc.metadata['page_len']
                    added = True

        # append source doc with page_num
        neighbor_docs.append(doc)

        # get docs after page_num up to half_size in total
        added = True
        page_counter = source_page_num
        while(added):
            added = False
            page_counter += 1
            if page_counter in related_docs.keys():
                neighbour_doc = related_docs[page_counter]
                if neighbour_doc.metadata['page_len'] + after_sum < half_size:
                    neighbor_docs.append(neighbour_doc)
                    after_sum += neighbour_doc.metadata['page_len']
                    added = True          
                

        return sorted(neighbor_docs, key=lambda d: d.metadata['page_num'], reverse=False)
    
    def retrieve_next(self, doc):
        if not all(key in doc.metadata.keys() for key in ['name', 'upload_id', 'page_num']):
            return [doc]
        
        # get docs from the same document and upload_id (to get relevant pages)
        source_page_num = doc.metadata['page_num']
        if source_page_num % 2 != 0:
            return [doc]    # source document isn't KEYWORD SECTION, so don't need to get next

        related_docs = self.retrieve_related_docs(doc)
        result_docs = []
        next_page = source_page_num + 1
        if next_page in related_docs.keys():
            result_docs.append(related_docs[next_page])
        else:
            print("WARNING: next page not found for {}".format(doc))    

        return result_docs    


    def remove_duplicate_docs(self, docs):
        docs_dict = {}
        for doc in docs:
            docs_dict["{}:{}:{}".format(doc.metadata["upload_id"], doc.metadata["name"], doc.metadata["page_num"])] = doc # storing each doc as upload_id:name:page_num

        return list(docs_dict.values())

    



def get_doc_with_description(doc):
    #return " Название Документа: {} от {}\n Блок: {}\n\n{}".format(doc.metadata['name'], doc.metadata['date'], doc.metadata['page_num'], doc.page_content)
    return doc.page_content

def format_docs(docs):
    head = "Сегодня {}\n===================\n".format(datetime.today().strftime('%Y-%m-%d'))
    docs_num = MAX_CONTEXT_DOC_NUMBER if (len(docs) > MAX_CONTEXT_DOC_NUMBER) else len(docs)
    formatted_docs = head + "\n===================\n".join(get_doc_with_description(docs[i]) for i in range(docs_num))

    if "stoplist" in properties.keys():
        for word in properties["stoplist"]:
            formatted_docs = formatted_docs.replace(word, "")
    
    print(formatted_docs)
    #print(len(formatted_docs))
    return formatted_docs


embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
#llm = GigaChat(verify_ssl_certs=False, model='GigaChat-Lite')  
llm = GigaChat(verify_ssl_certs=False)  

from langchain.cache import InMemoryCache
import langchain
langchain.llm_cache = InMemoryCache()

                                                                    # retrieve r_k with score > threshold, pick r_s by score and then r_t by time

def prepareSimpleAnswerChain(llm, prompt):
    rag_chain = (
      {"question": RunnablePassthrough(), "context": RunnablePassthrough()}
      | prompt
      | llm
      | StrOutputParser()
    )
    
    return rag_chain, None

def prepareAnswerChain(db_path, collection_name, embeddings, llm, prompt, search_args):
  print("Prepare answer chain for collection_name {}".format(collection_name))
  chroma_client = chromadb.PersistentClient(path=db_path)
  vectorstore = Chroma(
      client=chroma_client,
      collection_name=collection_name,
      embedding_function=embeddings
  )
  collection_size = vectorstore._collection.count()
  print("Size:" + str(collection_size))

  if collection_size == 0:
      return None, None     # do not return and process empty collections
    
  #retriever = vectorstore.as_retriever()      
  retriever = MyVectorStoreRetriever(
    vectorstore=vectorstore,
    search_type="similarity_score_threshold",
    search_kwargs=search_args # retrieve k with score > threshold, pick s by score and then t by time
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

def extract_arg(message):
    return message.split()[1:]

def extract_arg_num(message, num, default):
    args = extract_arg(message)
    print(args)
    if len(args) > num:
        return int(args[num])
    else: 
        return default


def get_config_value(key, category, default_category): 
  if key in category.keys():
    return category[key]
  else:
    return default_category[key]
