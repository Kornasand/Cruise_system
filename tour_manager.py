from datetime import datetime
from database import db_connection

class TourManager:
    @staticmethod
    def add_tour(name, description, base_price, departure_date, destination,
                duration, comfort_level, available_cabins):
        with db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO tours (
                        name, description, base_price, departure_date,
                        destination, duration, comfort_level, available_cabins
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    name, description, base_price,
                    datetime.strptime(departure_date, '%Y-%m-%d').date(),
                    destination, duration, comfort_level, available_cabins
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return False

    @staticmethod
    def search_tours(filters):
        query = '''
            SELECT * FROM tours
            WHERE 1=1
        '''
        params = []
        
        if filters.get('destination'):
            query += ' AND destination = ?'
            params.append(filters['destination'])
        
        if filters.get('max_price'):
            query += ' AND base_price <= ?'
            params.append(filters['max_price'])
        
        if filters.get('start_date'):
            query += ' AND departure_date >= ?'
            params.append(filters['start_date'])
        
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()