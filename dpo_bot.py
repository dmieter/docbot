import os
import random
import telebot
from langchain.prompts import PromptTemplate
import chromadb
from langchain.vectorstores import Chroma
from datetime import datetime
from telebot import types
import doc_core as dc
import multi_level_bot as mlb
import moderator as mdr
import yaml
import dpo_excel_update as dpu


#BOT_TOKEN = os.environ.get('DOCBOT_TOKEN')
#bot = telebot.TeleBot(BOT_TOKEN)
bot = None

config = {}
chat_history = {}
moderator = mdr.Moderator()
main_talk_bot = None

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

  global main_talk_bot
  main_talk_bot = mlb.create_talk_bot(config)


init()


@bot.message_handler(commands=['ban'])
def ban_user(message):
    try:
        if 'admins' in config.keys() and message.chat.id in config['admins']:
          user_id, date_str = message.text.split()[1:3]
          datetime.strptime(date_str, '%Y%m%d')  # Validate date format
          
          moderator.ban_user(int(user_id), date_str)

          bot.reply_to(message, f"Пользователь {user_id} заблокирован до {date_str}.")
    except Exception as e:
        print("{} {}".format(str(e), message.text))

@bot.message_handler(commands=['unban'])
def unban_user(message):
    try:
        if 'admins' in config.keys() and message.chat.id in config['admins']:
          user_id = message.text.split()[1]
          moderator.unban_user(int(user_id))
          bot.reply_to(message, f"Пользователь {user_id} разаблокирован.")
    except Exception as e:
        print("{} {}".format(str(e), message.text))        

@bot.message_handler(content_types=['document'])
def handle_file(message):
    try:
      file_info = bot.get_file(message.document.file_id)
      downloaded_file = bot.download_file(file_info.file_path)
      #bot.reply_to(message, downloaded_file)
      with open("upload/dpo/dpo.xlsx", 'wb') as new_file:
          new_file.write(downloaded_file)

      dpu.process_file("upload/dpo/dpo.xlsx")
      reload(message)
    except Exception as e:
      bot.reply_to(message, "Опаньки, возможно ошибка в формате данных: {}".format(str(e)))


@bot.message_handler(commands=['reload'])
def reload(message):
  try:
    if 'admins' in config.keys() and message.chat.id in config['admins']:
      load_config()
      global main_talk_bot
      main_talk_bot = mlb.create_talk_bot(config)
      
      bot.reply_to(message, "База знаний обновлена")
  except Exception as e:
        print("{} {}".format(str(e), message.text))

@bot.message_handler(commands=['start'])
def start(message):
  chat_history.clear()
  markup = types.ReplyKeyboardRemove()
  bot.send_message(message.from_user.id, """🖖 Привет! Я бот-специалист по программам ДПО! буду рад ответить на ваши вопросы.""", reply_markup=markup)


DPO_LINKS = {'Электрические станции' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=982',
             'Тепловые электрические станции' : 'https://mpei.ru/Education/educationalprograms/2023/Lists/DopPrograms2023/disp.aspx?ID=1476',
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
  reply_markup = None
  button_messages = ["Сколько стоит обучение по программе", "Какие сроки обучения по программе", "Дай контактные ланные по программе"]
    

  for key, value in DPO_LINKS.items():
    if key.lower() in answer.lower():
      if not references_str:
        references_str = "\nПодробные детали по соответсвующим программам:\n"
      references_str += "<a href='{}'>{}</a>\n".format(value, key)

      if not reply_markup:
         reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
      btn = types.KeyboardButton("Расскажи подробнее о программе " + key)
      reply_markup.add(btn)
      btn = types.KeyboardButton(random.choice(button_messages) + " " + key)
      reply_markup.add(btn)
      

  return references_str, reply_markup
  

def prepare_links(answer, docs):
  references_str = "\n"
  references = set()

  for doc in docs:
    if "url" in doc.metadata.keys() and doc.metadata["url"]:
      #references.add(doc.metadata["url"])
      references.add("<a href='{}'>{}</a>".format(doc.metadata["url"], doc.metadata["name"]))

  if len(references) > 0:
    references_str += '\n'.join(list(references))

  dpo_links, _ = prepare_dpo_links(answer)
  references_str += dpo_links

  return references_str

def addContactsIfNeeded(answer):
  if "контактные данные" in answer.lower() or "связаться" in answer.lower() or "обратиться" in answer.lower() or "к специалист" in answer.lower() or "со специалист" in answer.lower() or "у специалист" in answer.lower():
      return "\n\n<b>По общим вопросам обращайтесь к </b> Белобородову Александру Геннадьевичу Email: BeloborodovAG@mpei.ru"
  else:
      return ""


def log_answer(name, question, answer):
  current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  delimeter = "\n===============================\n"
  with open('question_log.txt', 'a') as f:
    f.write("{} ({}): {}\n\n{}{}".format(name, current_time_str, question, answer, delimeter))

from telebot import types
def prepare_answer(question, knowledge):
  reply_markup = None
  try:
    answer = main_talk_bot.ask(question)
    answer += addContactsIfNeeded(answer)
    #answer += prepare_links(answer, [])
    dpo_links, reply_markup = prepare_dpo_links(answer)
    answer += dpo_links
    
  except Exception as e:
    answer = "Опаньки, что-то пошло не так, попробуйте переформулировать вопрос :("
    log_answer(None, question, "Ошибка: {} {}".format(e.__str__(), e))
    print("Ошибка при ответе на вопрос '{}': {} {}".format(question, e.__str__(), e))

  return answer, reply_markup

def trim_question(question):
  return trim_text(question, 800)

def trim_text(text, size):
  return text[:size] if len(text) > size else text

def is_additional_question(question):
  keywords = ["а", "и", "ну", "только", "хорошо", "хорошо,", "нет", "нет,"]
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
  username = message.from_user.username if message.from_user.username is not None else message.chat.username
  question = message.text
  print(">>>>>>>>>>>>>>> QQQ: " + str(datetime.now()) + " " + str(message.chat.id) + ": " + question)
  

  is_allowed, description = moderator.is_question_allowed(message.chat.id, config)
  if not is_allowed:
    log_answer("{} ({})".format(username, chat.id), question, description)
    bot.reply_to(message, description)
    return

  question_with_context = prepare_question_chain(message)
  #print("Question with context: {}".format(question_with_context))

  answer, reply_markup = prepare_answer(question_with_context, None)
  log_answer("{} ({})".format(username, chat.id), question_with_context, answer)
  
  #print(">>>>>>>>>>>>>>> AAA " + str(message.chat.id) + ": " + answer)
  #bot.reply_to(message, answer + suffix, parse_mode = 'Markdown')

  bot.reply_to(message, trim_text(answer, 3600), parse_mode='HTML', reply_markup = reply_markup)

#init()
print(str(datetime.now()) + " Marti Level DPO Doc is here!")
bot.infinity_polling()