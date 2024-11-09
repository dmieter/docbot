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

#BOT_TOKEN = os.environ.get('DOCBOT_TOKEN')
#bot = telebot.TeleBot(BOT_TOKEN)
bot = None

config = {}
answer_chains = {}
retrievers = {}
chat_history = {}

def load_config():
  global config
  
  with open('config/config_dpo.yml', 'r') as file:
      config = yaml.safe_load(file)
      print("config reloaded: {}".format(config))



def init():
  load_config()

  global bot
  bot = telebot.TeleBot(config['bot_token'])
  os.environ.setdefault("GIGACHAT_CREDENTIALS", config['giga_creds'])

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


init()

@bot.message_handler(commands=['reload'])
def reload(message):
  init()
  bot.reply_to(message, "База знаний обновлена")

@bot.message_handler(commands=['start'])
def start(message):
  chat_history.clear()
  bot.send_message(message.from_user.id, """🖖 Привет! Я бот-специалист по программам ДПО! буду рад ответить на ваши вопросы.""")


DPO_LINKS = {'Электрические станции' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=982',
             'Электроснабжение' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1199',
             'Промышленное и гражданское строительство' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1026',
             'Менеджмент государственных, муниципальных и корпоративных закупок' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1309',
             'Менеджмент закупок товаров, работ, услуг' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1315',
             'Обследование, наладка, материалы и методы контроля качества' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1518',
             'Оценка стоимости предприятия' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1284',
             'Переводчик в сфере профессиональной коммуникации' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1068',
             'Подготовка сметной документации':  'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1319',
             'Управление государственными и муниципальными закупками' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1176',
             'Ультразвуковой контроль с применением системы на фазированных решётках HARFANG VEO' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1175',
             'Электроэнергетика и электротехника' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1444',
             'Диагностика структуры и свойств кристаллических материалов' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=996'}
def prepare_dpo_links(answer):
  references_str = ""

  for key, value in DPO_LINKS.items():
    if key.lower() in answer.lower():
      if not references_str:
        references_str = "\nПодробные детали по соответсвующим программам:\n"
      references_str += "<a href='{}'>{}</a>\n".format(value, key)

  return references_str
  

def prepare_links(answer, docs):
  references_str = "\n"
  references = set()

  for doc in docs:
    if "url" in doc.metadata.keys() and doc.metadata["url"]:
      #references.add(doc.metadata["url"])
      references.add("<a href='{}'>{}</a>".format(doc.metadata["url"], doc.metadata["name"]))

  if len(references) > 0:
    references_str += '\n'.join(list(references))

  references_str += prepare_dpo_links(answer)

  return references_str

def prepare_answer(question, knowledge):

  if knowledge in answer_chains.keys():
    answer = answer_chains[knowledge].invoke(question)

    related_docs = retrievers[knowledge].get_relevant_documents(question)
    answer += prepare_links(answer, related_docs)
    #print("Retrieved docs: {}".format(related_docs))

  else:
    answer = "Что-то пошло не так. \nПопробуйте перезагрузить бота через команду /start".format(knowledge)

  return answer


def trim_question(question):
  return trim_text(question, 800)

def trim_text(text, size):
  return text[:size] if len(text) > size else text

def is_additional_question(question):
  keywords = ["а", "и", "ну", "теперь", "только", "хорошо", "хорошо,", "нет", "нет,"]
  trimmed_question = question.strip().lower()
  if len(trimmed_question) > 0:
    first_word = trimmed_question.split()[0]
    return first_word in keywords or trimmed_question[0] == '>'
  else:
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

  chat = bot.get_chat(message.chat.id)
  question = message.text
  print(">>>>>>>>>>>>>>> QQQ: " + str(datetime.now()) + " " + str(message.chat.id) + ": " + question)

  question_with_context = prepare_question_chain(message)
  print("Question with context: {}".format(question_with_context))

  knowledge_base = config['default']['knowledge_base']
  answer = prepare_answer(question_with_context, knowledge_base).replace('_', ' ')
  
  print(">>>>>>>>>>>>>>> AAA " + str(message.chat.id) + ": " + answer)
  suffix = """\n<b>{}.</b>""".format(knowledge_base)
  #bot.reply_to(message, answer + suffix, parse_mode = 'Markdown')
  bot.reply_to(message, trim_text(answer, 3500) + suffix, parse_mode = 'HTML')

#init()
print(str(datetime.now()) + " ChatDPO is here!")
bot.infinity_polling()