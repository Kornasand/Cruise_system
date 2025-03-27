from database import db_connection

class ReviewSystem:
    @staticmethod
    def submit_review(user_id, tour_id, rating, comment):
        with db_connection() as conn:
            cursor = conn.cursor()
            try:
                #Проверяем нету ли уже брони на тур у пользователя
                cursor.execute('''
                    SELECT id FROM reservations
                    WHERE user_id = ? AND tour_id = ?
                ''', (user_id, tour_id))
                
                if not cursor.fetchone():
                    return False, "You must book the tour before reviewing"
                
                cursor.execute('''
                    INSERT INTO reviews (user_id, tour_id, rating, comment)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, tour_id, rating, comment))
                
                conn.commit()
                return True, "Review submitted successfully"
            except sqlite3.Error as e:
                return False, str(e)

    @staticmethod
    def get_tour_reviews(tour_id):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT users.username, reviews.rating, reviews.comment
                FROM reviews
                JOIN users ON reviews.user_id = users.id
                WHERE tour_id = ?
            ''', (tour_id,))
            return cursor.fetchall()