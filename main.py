from datetime import datetime, date, time, timedelta
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler, RegexHandler

from data import db_session
from data.users import Users
from data.counts import Counts
from data.categories import Categories

TOKEN = '1411094474:AAG18T4-xvVTZSy-L0dJTalPov5kBgfRvPs'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(bot, update):
    logger.warning(f'Update {update} caused error {bot.error}')





def isAuthorized(userid):
    session = db_session.create_session()
    return userid in [user[0] for user in session.query(Users.userid).all()]


PROGRESS,STATISTICS = range(2)

def start(bot, update, user_data):
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
    update.message.reply_text('Добро пожаловать в бот, который поможет вам вести учет. Учет чего? Решать вам. Бега в километрах, книги в метрах (например, Анатолий Вассерман прочитал около 100 метров "в толщину" книг и примерно столько же журналов к 2012 году)', reply_markup=default_keyboard())
    if len(session.query(Categories).filter(Categories.userid == userid).all())==0:
        update.message.reply_text('Напишите через пробел все категории, по которым вы собираетесь вести учет. Например, "Бег(км) Фантастика(стр)"', reply_markup=ReplyKeyboardRemove())
        user_data['cats']=True
    return PROGRESS

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

def counts_keyboard():
    return ReplyKeyboardMarkup([['1'],['5', '10', '15'],['Назад']], row_width=1, resize_keyboard=True)

def default_keyboard():
    return ReplyKeyboardMarkup([['Мой прогресс','Добавить']], row_width=1, resize_keyboard=True)

def textInput(bot, update, user_data):
    userid = update.message.from_user.id
    session = db_session.create_session()
    if 'cats' in user_data:
        cats = update.message.text.split()
        for cat in cats:
            t = Categories(
                userid = userid,
                title=cat
            )
            session.add(t)
        session.commit()
        del user_data['cats']
        update.message.reply_text('Все ваши категории успешно добавлены!\n Выберите категорию, чтобы зачесть прогресс.', reply_markup=catsKeyboard(userid))
    elif update.message.text in [cat.title for cat in session.query(Categories).filter(Categories.userid == userid).all()]:
        cat = update.message.text
        user_data['active_cat'] = cat
        update.message.reply_text('Отлично! Какой у Вас прогресс по '+ cat +'?', reply_markup=counts_keyboard())
    elif update.message.text=='Назад':
        del user_data['active_cat']
        update.message.reply_text('Хотите посмотреть Ваш текущий прогресс или добавить еще?', reply_markup=default_keyboard())
    elif update.message.text.isdigit() and user_data['active_cat']:
        data = Counts(
            userid=userid,
            catid = session.query(Categories.id).filter(Categories.userid==userid , Categories.title==user_data['active_cat']).one()[0],
            count=int(update.message.text),
            updated=datetime.now()

        )
        session.add(data)
        session.commit()
        update.message.reply_text('Добавлено '+update.message.text+' в Ваш личный прогресс по '+ user_data['active_cat'])
    return PROGRESS



def end(bot, update):
    user = update.message.from_user
    logger.info("User %s end the conversation.", user.first_name)
    update.message.reply_text(
        'Прощай!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def add_progress(bot, update):
    userid = update.message.from_user.id
    update.message.reply_text('Выберите категорию, чтобы зачесть прогресс.',
                              reply_markup=catsKeyboard(userid))
    return PROGRESS


def stats(bot, update):
    userid = update.message.from_user.id
    session = db_session.create_session()
    keyboard = [
        [InlineKeyboardButton("Год", callback_data="year"),
         InlineKeyboardButton("Месяц", callback_data="month"),
         InlineKeyboardButton("Неделя", callback_data="week"),
         InlineKeyboardButton("Сегодня", callback_data="today")]
    ]
    cats = [cat for cat in session.query(Categories).filter(Categories.userid == userid).all()]
    answer = 'Ваш прогресс за сегодня:\n'
    for cat in cats:
        total = sum([c.count for c in session.query(Counts).filter(Counts.userid==userid, Counts.catid==cat.id, Counts.updated>= datetime.now() - timedelta(days=datetime.today().weekday(), hours=0, minutes=0, seconds=0, milliseconds=0))])
        answer+=cat.title+': '+str(total)+'\n'
    update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    return STATISTICS


def main():
    db_session.global_init("db/personal")
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True),
                      MessageHandler(Filters.text, start, pass_user_data=True)],

        states={
            PROGRESS: [RegexHandler('^Добавить$',add_progress),
                       RegexHandler('^Мой прогресс$', stats),
                MessageHandler(Filters.text, textInput, pass_user_data=True)],
            STATISTICS:[RegexHandler('^Добавить$',add_progress),
                       RegexHandler('^Мой прогресс$', stats)]

        },

        fallbacks=[RegexHandler('^End$', end, pass_user_data=True)]

    )
    dp.add_error_handler(error)
    dp.add_handler(conv_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
