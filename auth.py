from database import db_connection
import bcrypt

class AuthSystem:
    @staticmethod
    def register_user(username, password, role='user', email=None):
        with db_connection() as conn:
            cursor = conn.cursor()
            try:
                #Проверяем есть ли пользователь в базе
                cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
                if cursor.fetchone():
                    return False, "Имя пользователя уже существует"

                #Хэшируем пароль, потому что все так делают
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                #Заносим нового пользователя в бд
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role, email)
                    VALUES (?, ?, ?, ?)
                ''', (username, hashed_pw, role, email))
                conn.commit()
                return True, "Регистрация прошла успешно"
            except sqlite3.Error as e:
                return False, str(e)

    @staticmethod
    def login_user(username, password):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, password_hash, role FROM users WHERE username = ?
            ''', (username,))
            user = cursor.fetchone()
            
            if not user:
                return False, "Пользователь не найден", None
            
            user_id, hashed_pw, role = user
            if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
                return True, "Вход в систему прошел успешно", {'id': user_id, 'role': role}
            return False, "Неверный пароль", None