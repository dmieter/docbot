import os
import telebot
from langchain.prompts import PromptTemplate
import chromadb
from langchain.vectorstores import Chroma
import doc_core as dc

BOT_TOKEN = os.environ.get('DOCBOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)


obrpravo_prompt = PromptTemplate.from_template(dc.prompt_obr_pravo)
obrpravo_answer_chain = dc.prepareAnswerChain("./chroma_db", "mpei_obrpravo", dc.embeddings, dc.llm, obrpravo_prompt)


@bot.message_handler(func=lambda msg: True)
def general_question(message):
  question = message.text
  trimmed_question = question[:400] if len(question) > 400 else question
  answer = obrpravo_answer_chain.invoke(trimmed_question)
  bot.reply_to(message, answer)

bot.infinity_polling()