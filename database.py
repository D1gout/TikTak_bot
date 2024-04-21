import json
import sqlite3


class DBConnect:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()

    def CreateDB(self):
        # Создаем таблицу для пользователей, если она не существует
        self.cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL UNIQUE,
                        game_count INTEGER,
                        win INTEGER,
                        loose INTEGER
                    )''')

        # Создаем таблицу для запросов, если она не существует
        self.cur.execute('''CREATE TABLE IF NOT EXISTS requests (
                                id INTEGER PRIMARY KEY,
                                sender_id INTEGER NOT NULL,
                                sender_name TEXT NOT NULL,
                                receiver_id INTEGER NOT NULL
                            )''')

        # Создаем таблицу для игры, если она не существует
        self.cur.execute('''CREATE TABLE IF NOT EXISTS game (
                                        id INTEGER PRIMARY KEY,
                                        sender_id INTEGER NOT NULL,
                                        receiver_id INTEGER NOT NULL,
                                        last_move_user_id INTEGER NOT NULL,
                                        last_move TEXT,
                                        board TEXT,
                                        end_game BOOLEAN DEFAULT FALSE
                                    )''')

        # Подтверждение изменений
        self.conn.commit()

    def InsertUserDB(self, user_id: int):
        if not self.cur.execute(f"SELECT * FROM users WHERE user_id = {user_id}").fetchall():
            self.cur.execute(f"INSERT INTO users (user_id, game_count, win, loose) VALUES ({user_id}, 0, 0, 0)")
            self.conn.commit()

    def InsertRequestDB(self, sender_id: int, sender_name: str, receiver_id: int):
        if not self.cur.execute(f"SELECT * FROM requests WHERE "
                                f"sender_id = {sender_id} AND receiver_id = {receiver_id}").fetchall():
            self.cur.execute(f"INSERT INTO requests (sender_id, sender_name, receiver_id) "
                             f"VALUES ({sender_id}, '{sender_name}', {receiver_id})")

            self.conn.commit()

    def GetRequestsDB(self, user_id: int):
        return self.cur.execute(f"SELECT * FROM requests WHERE receiver_id = {user_id}").fetchall()

    def DeleteRequestDB(self, sender_id: int, receiver_id: int):
        self.cur.execute(f"DELETE FROM requests WHERE sender_id = {sender_id} AND receiver_id = {receiver_id}")

        self.conn.commit()

    def GetGameStatusDB(self, user_id: int):
        return self.cur.execute(f"SELECT end_game FROM game "
                                f"WHERE sender_id = {user_id} or receiver_id = {user_id}").fetchone()

    def InsertLastMoveDB(self, sender_id: int, receiver_id: int, last_move: str, board: tuple):

        board_pos = ' '.join(elem.callback_data.split(':')[0] for elem in board)

        if self.cur.execute(f"SELECT * FROM game "
                            f"WHERE sender_id = {sender_id} or receiver_id = {sender_id}").fetchone():

            self.cur.execute(f"UPDATE game SET last_move_user_id = {sender_id}, "
                             f"last_move = '{last_move}', board = '{board_pos}'"
                             f"WHERE sender_id = {sender_id} or receiver_id = {sender_id}")

        else:
            self.cur.execute(f"INSERT INTO game (sender_id, receiver_id, last_move_user_id, last_move, board) "
                             f"VALUES ({sender_id}, {receiver_id}, {sender_id}, '{last_move}', '{board_pos}')")

        self.conn.commit()

    def GetLastMoveDB(self, sender_id: int):
        return self.cur.execute(f"SELECT * FROM game "
                                f"WHERE sender_id = {sender_id} or receiver_id = {sender_id}").fetchone()

    def InsertGameStatDB(self, user_id, win: bool):
        if win:
            self.cur.execute(f"UPDATE users SET game_count = game_count + 1, win = win + 1 "
                             f"WHERE user_id = {user_id}")
        else:
            self.cur.execute(f"UPDATE users SET game_count = game_count + 1, loose = loose + 1 "
                             f"WHERE user_id = {user_id}")

        self.conn.commit()

    def InsertGameEnd(self, user_id):
        self.cur.execute(f"UPDATE game SET end_game = TRUE WHERE sender_id = {user_id} or receiver_id = {user_id}")

        self.conn.commit()

    def GetPlayerStatsDB(self, user_id):
        return self.cur.execute(f"SELECT game_count, win, loose FROM users WHERE user_id = {user_id}").fetchone()
