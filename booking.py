from database import db_connection

class BookingSystem:
    @staticmethod
    def create_reservation(user_id, tour_id, cabin_type, selected_services):
        with db_connection() as conn:
            try:
                #Считаем общую цену
                cursor = conn.cursor()
                cursor.execute('SELECT base_price FROM tours WHERE id = ?', (tour_id,))
                base_price = cursor.fetchone()[0]
                
                #Пример введения доп услуг, влияющих на цену (пока неработает)
                service_prices = {
                    'spa': 50,
                    'excursion': 100,
                    'premium_dining': 75
                }
                service_cost = sum(service_prices[service] for service in selected_services)
                
                total_price = base_price + service_cost
                
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