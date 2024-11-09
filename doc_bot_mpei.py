import os
import telebot
from langchain.prompts import PromptTemplate
import chromadb
from langchain.vectorstores import Chroma
from datetime import datetime
from telebot import types
import doc_core as dc
import multi_level_bot as mlb
import yaml
from data import list_mpei_documents as lmd

#BOT_TOKEN = os.environ.get('DOCBOT_TOKEN')
#bot = telebot.TeleBot(BOT_TOKEN)
bot = None

config = {}
chat_history = {}
main_talk_bot = None

def load_config():
  global config
  
  with open('config/config_mpei.yml', 'r') as file:
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

@bot.message_handler(commands=['reload'])
def reload(message):
  init()
  markup = types.ReplyKeyboardRemove()
  bot.reply_to(message, "База знаний обновлена", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
  chat_history.clear()
  markup = types.ReplyKeyboardRemove()
  bot.send_message(message.from_user.id, """🖖 Привет! Я бот-специалист по программам ДПО! буду рад ответить на ваши вопросы.""", reply_markup=markup)

def prepare_answer(question, knowledge):

  answer = main_talk_bot.ask(question)

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

  answer = prepare_answer(question_with_context, None)
  
  print(">>>>>>>>>>>>>>> AAA " + str(message.chat.id) + ": " + answer)
  #bot.reply_to(message, answer + suffix, parse_mode = 'Markdown')
  bot.reply_to(message, trim_text(answer, 3500))

#init()
print(str(datetime.now()) + " Marti Level Mpei Doc is here!")
bot.infinity_polling()