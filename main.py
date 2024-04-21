import logging

from aiogram import Bot, Dispatcher, types
from aiogram import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import TOKEN, db
from functions import check_winner

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

cross = InlineKeyboardButton('❌', callback_data='cross')
zero = InlineKeyboardButton('⭕️', callback_data='zero')


class TGMessage:
    def __init__(self):
        self.user_id = None
        self.contact_id = None
        self.contact_message_id = None
        self.row = []

    async def start(self, message):
        self.user_id = message.chat.id

        db.InsertUserDB(self.user_id)

        await bot.send_message(self.user_id, 'Привет, я бот для игры в Крестики-Нолики\n'
                                             'Для того что бы начать играть отправьте профиль противника')

    async def send_request(self, message):
        self.user_id = message.chat.id

        contact_id = message.contact.user_id
        contact_name = message.contact.first_name

        db.InsertRequestDB(self.user_id, contact_name, contact_id)
        await message.answer(f"Запрос {contact_name} отправлен")

    async def get_request(self, message):
        self.user_id = message.chat.id

        requests = db.GetRequestsDB(self.user_id)
        if requests:
            accept_request_button = InlineKeyboardMarkup()
            for request in requests:
                accept_request_button.add(InlineKeyboardButton(text=f"Принять запрос от {request[2]}",
                                                               callback_data=f"accept_request:{request[1]}"))
            await bot.send_message(self.user_id, 'У вас есть запросы на игру', reply_markup=accept_request_button)
        else:
            await bot.send_message(self.user_id, 'У вас нет запросов на игру')

    async def stats(self, message):
        self.user_id = message.chat.id

        stat = db.GetPlayerStatsDB(self.user_id)

        await bot.send_message(self.user_id, f"Статистика игрока\n"
                                             f"Количество игр: {stat[0]}\n"
                                             f"Побед: {stat[1]}\n"
                                             f"Поражений: {stat[2]}")

    async def process_callback_accept(self, callback_query):
        self.user_id = callback_query.from_user.id

        contact_id = callback_query.data.split(':')[1]

        db.DeleteRequestDB(contact_id, self.user_id)

        await bot.delete_message(self.user_id, callback_query.message.message_id)
        await bot.send_message(self.user_id, f"Запрос принят")

        desk_buttons = InlineKeyboardMarkup(row_width=3)

        self.row = []
        for i in range(9):
            empty = InlineKeyboardButton('⬜️', callback_data=f'empty:{i}')
            self.row.append(empty)

        desk_buttons.add(*self.row)

        db.InsertLastMoveDB(self.user_id, contact_id, 'cross', self.row)
        self.contact_message_id = await bot.send_message(self.user_id, f"Игра", reply_markup=desk_buttons)
        await bot.send_message(contact_id, f"Игра", reply_markup=desk_buttons)

    async def process_callback_game(self, callback_query):
        self.user_id = callback_query.from_user.id

        if db.GetGameStatusDB(self.user_id):
            return

        empty_row_id = callback_query.data.split(':')[1]

        desk_buttons = InlineKeyboardMarkup(row_width=3)

        game = db.GetLastMoveDB(self.user_id)

        if self.user_id == game[1]:
            message_text = f"Ход Ноликов"
            self.contact_id = game[2]
        else:
            message_text = f"Ход Крестиков"
            self.contact_id = game[1]

        if self.user_id == game[3]:
            return

        if not self.row:
            row_name = [elem for elem in game[5].split(' ')]

            for button_pos in range(len(row_name)):
                if row_name[button_pos] == 'empty':
                    self.row.append(InlineKeyboardButton('⬜️', callback_data=f'empty:{button_pos}'))
                elif row_name[button_pos] == 'cross':
                    self.row.append(InlineKeyboardButton('❌', callback_data='cross'))

                elif row_name[button_pos] == 'zero':
                    self.row.append(InlineKeyboardButton('⭕️', callback_data='zero'))

        for i in range(9):
            if i == int(empty_row_id):
                if game[4] == 'cross':
                    self.row[i] = zero

                else:
                    self.row[i] = cross

        desk_buttons.add(*self.row)

        db.InsertLastMoveDB(self.user_id, self.contact_id, 'cross' if game[4] == 'zero' else 'zero', self.row)

        winner = check_winner(self.row)
        if winner[0]:
            if winner[1] == 'cross':
                message_text = 'Победили Крестики'
                db.InsertGameStatDB(game[1], True)
                db.InsertGameStatDB(game[2], False)
            elif winner[1] == 'zero':
                message_text = 'Победили Нолики'
                db.InsertGameStatDB(game[1], False)
                db.InsertGameStatDB(game[2], True)
            else:
                message_text = 'Ничья'
                db.InsertGameStatDB(game[1], True)
                db.InsertGameStatDB(game[2], True)

            db.InsertGameEnd(self.user_id)

            await bot.send_message(self.contact_id, message_text)

        await bot.delete_message(self.user_id, callback_query.message.message_id)

        if self.user_id != game[3] and self.contact_message_id is not None:
            await bot.delete_message(self.contact_message_id.chat.id, self.contact_message_id.message_id)

        self.contact_message_id = await bot.send_message(self.user_id, message_text, reply_markup=desk_buttons)
        await bot.send_message(self.contact_id, message_text, reply_markup=desk_buttons)


tg_message_handler = TGMessage()


@dp.message_handler(commands=['start'])
async def func(message: types.Message):
    await tg_message_handler.start(message)


@dp.message_handler(commands=['requests'])
async def func(message: types.Message):
    await tg_message_handler.get_request(message)


@dp.message_handler(commands=['stats'])
async def func(message: types.Message):
    await tg_message_handler.stats(message)


# Обработчик всех входящих контактов
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle(message: types.Message):
    await tg_message_handler.send_request(message)


# Обработчик открытия Запроса на игру
@dp.callback_query_handler(lambda c: c.data.startswith('accept_request'))
async def process_callback_button(callback_query: types.CallbackQuery):
    await tg_message_handler.process_callback_accept(callback_query)


# Обработчик нажатия на поле игры
@dp.callback_query_handler(lambda c: c.data.startswith('empty'))
async def process_callback_button(callback_query: types.CallbackQuery):
    await tg_message_handler.process_callback_game(callback_query)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
