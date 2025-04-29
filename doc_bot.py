import os
import telebot
from langchain.prompts import PromptTemplate
import chromadb
from langchain.vectorstores import Chroma
from datetime import datetime
from telebot import types
import doc_core as dc
import yaml
from data import index_core as ic
from langchain.document_loaders import TextLoader
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings

bot = None
config = {}
answer_chains = {}
chat_history = {}

def load_config():
  global config
  
  with open('config/config_doc.yml', 'r') as file:
      config = yaml.safe_load(file)
      print("config reloaded: {}".format(config))



def init():
  load_config()

  global bot
  bot = telebot.TeleBot(config['bot_token'])
  os.environ.setdefault("GIGACHAT_CREDENTIALS", config['giga_creds'])

init()


@bot.message_handler(commands=['start'])
def start(message):
  chat_history.clear()
  markup = types.ReplyKeyboardRemove()
  bot.send_message(message.from_user.id, """🖖 Привет! Я могу помочь с аализовам ваших коллекций и документов""", reply_markup=markup)

def index_file(file, collection, db_storage_path):
    print("index file {} to collection {}".format(file, collection))
    today = ic.today_str()
    current_time_in_seconds = int(time.time())
    loader = TextLoader(file)
    doc = loader.load()[0]
    doc.metadata['upload_id'] = current_time_in_seconds
    doc.metadata['name'] = file
    doc.metadata['date'] = today
    doc.metadata['date_int'] = int(today.replace('-', ''))
    doc.metadata['expire_date'] = ic.date_add_days(today, 365) # 1 year expiration by default

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=200)
    splits = text_splitter.split_documents([doc])
    ic.numberize_splits(splits)
    print(len(splits))

    vectorstore = Chroma.from_documents(documents=splits, embedding=dc.embeddings, collection_name=collection, persist_directory=db_storage_path)



@bot.message_handler(content_types=['document'])
def handle_file(message):
    #try:
      #1. load file
      chat_id = str(message.chat.id)
      file_info = bot.get_file(message.document.file_id)
      downloaded_file = bot.download_file(file_info.file_path)

      if(file_info.file_path.endswith(".txt")):
        with open("upload/doc/{}.txt".format(chat_id), 'wb') as new_file:
          new_file.write(downloaded_file)   

      elif(file_info.file_path.endswith(".pdf")):
        with open("upload/doc/{}.pdf".format(chat_id), 'wb') as new_file:
          new_file.write(downloaded_file)
          os.system("pdftotext upload/doc/{}.pdf upload/doc/{}.txt".format(chat_id, chat_id))
          os.system("rm upload/doc/{}.pdf".format(chat_id))
        
      else: 
        bot.reply_to(message, "Документ должен быть в формате .txt или .pdf")
        new_file.close()
        return


      #2. index file
      index_file("upload/doc/{}.txt".format(chat_id), chat_id, config['db_path'])
      os.system("rm upload/doc/{}.txt".format(chat_id))

      #3. create answer chain
      prompt = PromptTemplate.from_template(config['prompt'])
      answer_chain, _ = dc.prepareAnswerChain(config['db_path'], chat_id, dc.embeddings, dc.llm, prompt, config['retriever'])
      
      if len(answer_chains) > 5:
        answer_chains.clear()

      answer_chains[chat_id] = answer_chain

    #except Exception as e:
     # bot.reply_to(message, "Опаньки, что-то пошло не так: {}".format(str(e)))


@bot.message_handler(commands=['clear'])
def clear_collection(message):
  chat_id = str(message.chat.id)
  chroma_client = chromadb.PersistentClient(path=config['db_path'])
  if ic.check_collection_exists(chroma_client, chat_id):
    chroma_client.delete_collection(chat_id)
    bot.reply_to(message, "Коллекция {} удалена".format(chat_id))

  answer_chains.remove(chat_id)  


def prepare_answer(question, collection):

  if collection in answer_chains.keys():
    answer = answer_chains[collection].invoke(question)
  else:
    chroma_client = chromadb.PersistentClient(path=config['db_path'])
    if ic.check_collection_exists(chroma_client, collection):
      prompt = PromptTemplate.from_template(config['prompt'])
      print("prepare answer chain for chat id {}".format(collection))
      answer_chain, _ = dc.prepareAnswerChain(config['db_path'], collection, dc.embeddings, dc.llm, prompt, config['retriever'])
      if len(answer_chains) > 5:
          answer_chains.clear()

      answer_chains[collection] = answer_chain
      answer = answer_chain.invoke(question)
    else:
      answer = "Ваша коллекция документво пуста"   

  return answer



def trim_question(question):
  return trim_text(question, 800)

def trim_text(text, size):
  return text[:size] if len(text) > size else text

def is_additional_question(question):
  return False
  
def prepare_question_chain(message):
  global chat_history

  prev_messages = []
  if message.chat.id in chat_history.keys():
    prev_messages = chat_history[message.chat.id]

  trimmed_question = trim_question(message.text)

  # if no history or question isnt additional then just create a new question thread and return current question
  if len(prev_messages) == 0 or not is_additional_question(trimmed_question):
    chat_history[message.chat.id] = [trimmed_question]
    return trimmed_question
  
  # else need to retrieve previous messages as context and add new question to the end
  thread = '\n'.join(prev_messages)
  chat_history[message.chat.id].append(trimmed_question)

  return '{} \n {}'.format(thread, trimmed_question)
  


@bot.message_handler(func=lambda msg: True)
def general_question(message):

  chat_id = str(message.chat.id)
  question = message.text
  print(">>>>>>>>>>>>>>> QQQ: " + str(datetime.now()) + " " + chat_id + ": " + question)

  question_with_context = prepare_question_chain(message)
  print("Question with context: {}".format(question_with_context))

  answer = prepare_answer(question_with_context, chat_id)
  
  print(">>>>>>>>>>>>>>> AAA " + chat_id + ": " + answer)
  #bot.reply_to(message, answer + suffix, parse_mode = 'Markdown')
  bot.reply_to(message, trim_text(answer, 3500))

#init()
print(str(datetime.now()) + " Marti Level Mpei Doc is here!")
bot.infinity_polling()