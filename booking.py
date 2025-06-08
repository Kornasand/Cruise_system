from database import db_connection
import sqlite3
class BookingSystem:
    @staticmethod
    def create_reservation(user_id, tour_id, cabin_type, selected_services,total_price):
        with db_connection() as conn:
            try:
                cursor = conn.cursor()
                
                #Создаем бронь
                cursor.execute('''
                    INSERT INTO reservations (
                        user_id, tour_id, cabin_type, services, total_price
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    tour_id,
                    cabin_type,
                    ','.join(selected_services),
                    total_price
                ))
                
                #Обновляем список доступных кают
                cursor.execute('''
                    UPDATE tours
                    SET available_cabins = available_cabins - 1
                    WHERE id = ?
                ''', (tour_id,))
                
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Booking error: {e}")
                return False

    def delete_special_offer(tour_id_inc):
        with db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM special_offers WHERE id = ?',(tour_id_inc,))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False  #Ключ не нашелся