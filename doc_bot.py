import os
import telebot
from langchain.prompts import PromptTemplate
import chromadb
from langchain.vectorstores import Chroma
from datetime import datetime
from telebot import types
import doc_core as dc
import yaml

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
    retriever = get_config_value('retriever', category, config['default'])

    answer_chain, retriever = dc.prepareAnswerChain(db_path, category_name, dc.embeddings, dc.llm, prompt, 
                                                    search_args={"score_threshold": retriever['threshold'], "k": retriever['k'], "s" : retriever['s'], "t" : retriever['t'], "neighbours": [1500, 1000]})
    
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


def prepare_answer(question, knowledge):

  if knowledge in answer_chains.keys():
    answer = answer_chains[knowledge].invoke(question)
  else:
    answer = "Документы по категории {} еще готовятся".format(knowledge)

  print("Retrieved docs: {}".format(dc.format_docs(retrievers[knowledge].get_relevant_documents(question))))

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
    print(str(datetime.now()) + " " + str(message.chat.id) + " Q: " + question)

    trimmed_question = question[:800] if len(question) > 800 else question
    knowledge_base = chat.pinned_message.text if chat.pinned_message else config['default']['knowledge_base']
    answer = prepare_answer(trimmed_question, knowledge_base)
    
    print(str(message.chat.id) + " A: " + answer)
    suffix = """\n*{}.*""".format(knowledge_base)
    bot.reply_to(message, answer + suffix, parse_mode = 'Markdown')

init()
print(str(datetime.now()) + " Doc is here!")
bot.infinity_polling()