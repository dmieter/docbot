import os
import telebot
from langchain.prompts import PromptTemplate
import chromadb
from langchain.vectorstores import Chroma
from datetime import datetime
from telebot import types
import doc_core as dc
import yaml
from data import list_mpei_documents as lmd

BOT_TOKEN = os.environ.get('DOCBOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

config = {}
answer_chains = {}
retrievers = {}


def load_config():
  global config
  
  with open('config/config.yml', 'r') as file:
      config = yaml.safe_load(file)
      print("config reloaded: {}".format(config))

def get_config_value(key, category, default_category): 
  if key in category.keys():
    return category[key]
  else:
    return default_category[key]

def init():
  load_config()
  answer_chains.clear()
  retrievers.clear()
  

  for category_name in config['categories'].keys():
    category = config['categories'][category_name]

    prompt_template_name = get_config_value('prompt', category, config['default'])
    prompt_template = dc.prompts[prompt_template_name]
    prompt = PromptTemplate.from_template(prompt_template)

    display_name = category['display_name']
    db_path = get_config_value('db_path', category, config['default'])
    retriever_config = get_config_value('retriever', category, config['default'])

    answer_chain, retriever = dc.prepareAnswerChain(db_path, category_name, dc.embeddings, dc.llm, prompt, search_args=retriever_config)
                                                    #search_args={"score_threshold": retriever['threshold'], "k": retriever['k'], "s" : retriever['s'], "t" : retriever['t'], "neighbours": [1500, 1000]})
    
    if answer_chain:
      answer_chains[display_name] = answer_chain
      retrievers[display_name] = retriever


@bot.message_handler(commands=['reload'])
def reload(message):
  init()
  bot.reply_to(message, "База знаний обновлена")

@bot.message_handler(commands=['category'])
def set_knowledge_base(message, greeting = "Выберите категорию знаний"):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  for key in answer_chains.keys():
    btn = types.KeyboardButton(key)
    markup.add(btn)
  bot.send_message(message.from_user.id, greeting, reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
  set_knowledge_base(message, """🖖 Привет! Я док, специалист по различным документам и приказам МЭИ! 
Рекомендую сразу выбрать интересующую категорию знаний
В дальнейшем для выбора категории можно использовать команду /category""")

@bot.message_handler(commands=['new'])
def new_mpei_orders(message):
  docs_num = dc.extract_arg_num(message.text, 0, 10)
  docs_num = min(docs_num, 20) # there's a limit in the message len
  new_docs = lmd.retrieve_recent_docs(number=docs_num)
  mpei_links = []
  order_num = 1
  if len(new_docs) > 0:
    for date, expire_date, filename, name, url, desc in new_docs:
      mpei_links.append("<a href='{}'>{}. {}</a>\n{}\n".format(url, order_num, name, desc))
      order_num += 1

    answer = "\n".join(mpei_links)

  else:
    answer = "Новых документов не найдено"
  bot.reply_to(message, answer, parse_mode = 'HTML')

def prepare_links(docs):
  references_str = "\n"
  references = set()

  for doc in docs:
    if "url" in doc.metadata.keys() and doc.metadata["url"]:
      #references.add(doc.metadata["url"])
      references.add("<a href='{}'>{}</a>".format(doc.metadata["url"], doc.metadata["name"]))

  if len(references) > 0:
    references_str += '\n'.join(list(references))

  return references_str

def prepare_answer(question, knowledge):

  if knowledge in answer_chains.keys():
    answer = answer_chains[knowledge].invoke(question)

    related_docs = retrievers[knowledge].get_relevant_documents(question)
    answer += prepare_links(related_docs)
    #print("Retrieved docs: {}".format(related_docs))

  else:
    answer = "Документы по категории {} еще готовятся".format(knowledge)

  return answer


@bot.message_handler(func=lambda msg: True)
def general_question(message):

  if message.text in answer_chains.keys():
    bot.unpin_all_chat_messages(chat_id = message.chat.id)
    bot.pin_chat_message(chat_id = message.chat.id, message_id = message.message_id)
    bot.reply_to(message, "Документы готовы")
  else:
    chat = bot.get_chat(message.chat.id)
    question = message.text
    print(">>>>>>>>>>>>>>> QQQ: " + str(datetime.now()) + " " + str(message.chat.id) + ": " + question)

    trimmed_question = question[:1000] if len(question) > 1000 else question
    knowledge_base = chat.pinned_message.text if chat.pinned_message else config['default']['knowledge_base']
    answer = prepare_answer(trimmed_question, knowledge_base).replace('_', ' ')
    
    print(">>>>>>>>>>>>>>> AAA " + str(message.chat.id) + ": " + answer)
    suffix = """\n<b>{}.</b>""".format(knowledge_base)
    #bot.reply_to(message, answer + suffix, parse_mode = 'Markdown')
    bot.reply_to(message, answer + suffix, parse_mode = 'HTML')

init()
print(str(datetime.now()) + " Doc is here!")
bot.infinity_polling()