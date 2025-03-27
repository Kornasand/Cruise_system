from database import db_connection

class UserManager:
    @staticmethod
    def get_all_users():
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, role, email FROM users')
            return cursor.fetchall()

    @staticmethod
    def update_user_role(user_id, new_role):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET role = ? WHERE id = ?
            ''', (new_role, user_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete_user(user_id):
        with db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False  #Ключ не нашелся