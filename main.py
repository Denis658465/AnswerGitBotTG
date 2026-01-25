import telebot
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")

bot = telebot.TeleBot(token)

@bot.message_handler(commands=["start"])
def get_start(message):
      bot.send_message(message.chat.id, "Привет только начали!")   

@bot.message_handler (content_types=["text"])
def first_answtr(message):
    text = message.text.lower()
    
    if "программист" in text:
        bot.send_message(message.chat.id, "Подари мышку")  
    elif "дизайнеру" in text:
        bot.send_message(message.chat.id, "Подари попкорницу") 
    elif "трактористу" in text:
        bot.send_message(message.chat.id, "Подари ковш")
    elif "водителю" in text:
        bot.send_message(message.chat.id, "Подари время")
    elif "копателю" in text:
        bot.send_message(message.chat.id, "Подари пластиковую картушку")
    else:
        bot.send_message(message.chat.id,"Я могу подсказать подарки (программисту,дизайнеру,водителю,копателю,трактористу)")  

if "__main__" == __name__:
    bot.infinity_polling()