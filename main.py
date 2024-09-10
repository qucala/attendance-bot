import telebot
import csv
import codecs
import datetime
import os
from dotenv import load_dotenv
from rtu_schedule_parser import ExcelScheduleParser, ScheduleData
from rtu_schedule_parser.constants import Institute, Degree
from rtu_schedule_parser.downloader import ScheduleDownloader
import requests
from time import sleep
from telebot.types import ReactionTypeEmoji
load_dotenv()
TOKEN = os.getenv('TOKEN')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')
MESSAGE_THREAD_ID = os.getenv('MESSAGE_THREAD_ID')
group=os.getenv('GROUP')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['send_poll_today'])
def send_polles(message):
    try:
        r=requests.get('https://www.timeapi.io/api/time/current/zone?timeZone=Europe%2FMoscow').json()
        days_translation = {
            "Monday": "понедельник",
            "Tuesday": "вторник",
            "Wednesday": "среда",
            "Thursday": "четверг",
            "Friday": "пятница",
            "Saturday": "суббота",
            "Sunday": "воскресенье"
        }
        day_of_week_english = r["dayOfWeek"]
        day_of_week_russian = str(days_translation.get(day_of_week_english))
        print(day_of_week_russian)
        # Извлекаем аргументы из сообщения пользователя
        # args = message.text.split()[1:]  # Пропускаем команду '/send_poll'
        
        
        
        tw = str(datetime.datetime.now().isocalendar()[1]-35)  # Номер недели
        day = day_of_week_russian  # День недели

        
                # Initialize downloader with default directory to save files
        downloader = ScheduleDownloader()

        # Get documents for specified institute and degree
        docs = downloader.get_documents(specific_institutes={Institute.IIT}, specific_degrees={Degree.BACHELOR})

        # Download only if they are not downloaded yet.
        downloaded = downloader.download_all(docs)

        # Create schedule with downloaded files
        schedules = None  # type: ScheduleData | None
        for doc in downloaded:
            parser = ExcelScheduleParser(
                doc[1], doc[0].period, doc[0].institute, doc[0].degree
            )
            
            # The `force` argument is used to ignore exceptions during document parsing. 
            # This lets you to parse all possible groups.
            if schedules is None:
                schedules = parser.parse(force=True)
            else:
                schedules.extend(parser.parse(force=True).get_schedule())

        # Get a schedule for the specified group
        group_schedule = schedules.get_group_schedule(group)

        # Initialize pandas dataframe
        df = group_schedule.get_dataframe()
        # Запускаем функцию отправки опросов с указанными аргументами
        df=df.drop_duplicates()
        # Вывод данных
        
        first_sort=df[df['weeks'].apply(lambda x: tw in x)]
        second_sort=first_sort[df['weekday'].apply(lambda x: day in x)]
        # df_filtered = df[df['weeks'].apply(lambda x: tw in x.split(','))]
        for i, data in second_sort[['lesson_num', 'lesson','type']].iterrows():
            print(data['lesson_num'],data['lesson'],data['type'])
            days_dic = {
                "лек": "Лекция",
                "лаб": "Лабораторная",
                "пр": "Практика",
                
            }
            data_not_sorted = data['type']
            data_sorted = str(days_dic.get(data_not_sorted))
            bot.send_poll(chat_id=TARGET_CHAT_ID,message_thread_id=MESSAGE_THREAD_ID,question=str(str(data['lesson_num'])+'  '+data_sorted+'  '+'по  '+data['lesson']), is_anonymous=False,options=['Я', 'Не я(у)', 'Не я(н)', 'Опа'])
            
        
        bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji('👍')], is_big=False)
        sleep(5)
        bot.delete_message(chat_id=message.chat.id,message_id=message.id)
    
    except ValueError:
        bot.reply_to(message, "Ошибка ввода! Убедитесь, что номер недели указан числом.")
    
bot.polling()
