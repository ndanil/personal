from datetime import datetime, date, time, timedelta
import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

from data import db_session
from data.users import Users
from data.counts import Counts
from data.categories import Categories

TOKEN = ''

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(bot, update):
    logger.warning(f'Update {update} caused error {bot.error}')





def isAuthorized(userid):
    session = db_session.create_session()
    return userid in [user[0] for user in session.query(Users.userid).all()]

STATE = []

def start(bot, update):
    userid = update.message.from_user.id
    username = update.message.from_user.first_name + ' ' + update.message.from_user.last_name
    session = db_session.create_session()
    if not isAuthorized(userid):
        user = Users(
            userid=userid,
            username=username
        )
        session.add(user)
        session.commit()
    update.message.reply_text('Добро пожаловать в бот, который поможет вам вести учет. Учет чего? Решать вам. Бега в километрах, книги в метрах (например, Анатолий Вассерман прочитал около 100 метров "в толщину" книг и примерно столько же журналов к 2012 году)')
    if len(session.query(Categories).filter(Categories.userid == userid).all())==0:
        update.message.reply_text('Напишите через пробел все категории, по которым вы собираетесь вести учет. Например, "Бег(км) Фантастика(стр)"')
        STATE.append('cats')

def catsKeyboard(userid):
    session = db_session.create_session()
    cats = [cat.title for cat in session.query(Categories).filter(Categories.userid == userid).all()]
    keyboard = []
    for i in range(len(cats)):
        if not i%3:
            keyboard.append([cats[i]])
        else:
            keyboard[-1].append(cats[i])
    return ReplyKeyboardMarkup(keyboard, row_width=1, resize_keyboard=True)

def textInput(bot, update):
    if 'cats' in STATE:
        cats = update.message.text.split()
        userid = update.message.from_user.id
        session = db_session.create_session()
        for cat in cats:
            t = Categories(
                userid = userid,
                title=cat
            )
            session.add(t)
        session.commit()
        STATE.remove('cats')
        update.message.reply_text('Все ваши категории успешно добавлены!\n Выберите категорию, чтобы зачесть прогресс.', reply_markup=catsKeyboard(userid))



def main():
    db_session.global_init("db/personal")
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, textInput))
    #dp.add_handler(MessageHandler(Filters.forwarded, add_guilds2))
    #dp.add_handler(CommandHandler('lazy',lazy))

    dp.add_error_handler(error)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
