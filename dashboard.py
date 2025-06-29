from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLabel, QLineEdit, QComboBox, QSpinBox, 
    QDoubleSpinBox, QTextEdit, QMessageBox, 
    QHeaderView, QDateEdit, 
    QDialog, QDialogButtonBox, QCheckBox, QFormLayout,QScrollArea
)
import sqlite3
import matplotlib
matplotlib.use('Qt5Agg')  # Use the Qt backend
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPainter, QColor
from database import db_connection
from booking import BookingSystem
from datetime import datetime as py_datetime
from reviews import ReviewSystem
from tour_manager import TourManager
from user_manager import UserManager

class Dashboard(QWidget):
    def __init__(self, user_role, user_id):
        super().__init__()
        self.user_role = user_role
        self.user_id = user_id
        self.cart = []
        self.is_discount = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Cruise System Dashboard')
        self.setGeometry(100, 100, 1280, 1024)


        #self.setVerticalScrollBar(scroll_bar)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()


        
        #Общие вкладки
        self.tabs.addTab(self.create_profile_tab(), "Профиль")
        self.tabs.addTab(self.create_tours_tab(), "Доступные туры")

        #Пользовательские вкладки, зависимые от роли
        if self.user_role == 'user':
            #self.tabs.addTab(self.create_bookings_tab(), "Мои бронирования")
            self.tabs.addTab(self.create_reviews_tab(), "Мои отзывы")
            self.tabs.addTab(self.create_cart_tab(), "Корзина")
        elif self.user_role == 'manager':
            self.tabs.addTab(self.create_management_tab(), "Организация туров")
        elif self.user_role == 'admin':
            self.tabs.addTab(self.create_user_management_tab(), "Управление пользователями")

        if self.user_role in ['user', 'manager', 'admin']:
            self.tabs.addTab(self.create_special_offers_tab(), "Спецпредложения")
        if self.user_role in ['manager', 'admin']:
            self.tabs.addTab(self.create_analytics_tab(), "Аналитика")

        layout.addWidget(self.tabs)
        self.setLayout(layout)



    def create_profile_tab(self):
        #Управления профилями (возможно не нужно, но пока пусть будет)
        pass

    def create_tours_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        #Вкладка для всех туров
        self.tours_table = QTableWidget()
        self.tours_table.verticalHeader().setDefaultSectionSize(50)
        self.tours_table.horizontalHeader().setDefaultSectionSize(100)
        self.tours_table.setColumnCount(6)
        self.tours_table.setHorizontalHeaderLabels(
            ['Имя', 'Место назначения', 'Отбытие', 'Длительность', 'Цена', 'Каюты']
        )
        self.tours_table.setColumnCount(7)  # Add Actions column
        self.tours_table.setHorizontalHeaderLabels(
            ['Имя', 'Место назначения', 'Отбытие', 'Длительность', 'Цена', 'Каюты', 'Действия']
        )
        
        #Заполняем вкладку данными
        self.load_tours_data()
        
        layout.addWidget(self.tours_table)
        tab.setLayout(layout)
        return tab

    def load_tours_data(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, destination, departure_date, duration, base_price, available_cabins FROM tours''')
            tours = cursor.fetchall()
        
            self.tours_table.setRowCount(len(tours))
            for row_idx, row_data in enumerate(tours):
                tour_id = row_data[0]
                for col_idx, value in enumerate(row_data[1:]):  # Skip ID
                    self.tours_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
                #Кнопка брони
                if self.user_role == 'user':
                    btn_book = QPushButton("Забронировать")
                    btn_book.clicked.connect(lambda _, tid=tour_id: self.book_tour_disable_discount(tid))
                    self.tours_table.setCellWidget(row_idx, 6, btn_book)

    def book_tour_disable_discount(self,tid):
        self.is_discount = False
        self.book_tour(tid)

    def book_tour(self, tour_id):
        self.selected_tour_id = tour_id
        self.show_booking_dialog()

    def show_booking_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Бронирование тура")
        layout = QVBoxLayout()

    
        #Выбраем уровень комфорта
        layout.addWidget(QLabel("Уровень комфорта:"))
        self.cmb_comfort = QComboBox()
        self.cmb_comfort.addItems(["Standard", "Premium", "Luxury"])
        layout.addWidget(self.cmb_comfort)
    
        #Доп услуги
        layout.addWidget(QLabel("Дополнительные услуги:"))
        self.chk_services = []
        services = ["SPA", "Экскурсии", "Премиум питание"]
        for service in services:
            chk = QCheckBox(service)
            self.chk_services.append(chk)
            layout.addWidget(chk)
    
        #Считаем цену 
        self.lbl_price = QLabel("Итоговая цена: $0.00")
        layout.addWidget(self.lbl_price)
        self.calculate_price()
    
        #Подвязываем доп параметры к финальной цене
        self.cmb_comfort.currentIndexChanged.connect(self.calculate_price)
        for chk in self.chk_services:
            chk.stateChanged.connect(self.calculate_price)
    
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(lambda: self.confirm_booking(dialog))
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
    
        dialog.setLayout(layout)
        dialog.exec()

    def calculate_price(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            if self.is_discount:
                cursor.execute('SELECT base_price FROM tours WHERE id = (SELECT tour_id FROM special_offers WHERE id = ?)',(self.selected_tour_id,))
                print(self.selected_tour_id)
                price = cursor.fetchone()[0]
                cursor.execute('SELECT discount_percent FROM special_offers WHERE id = ?', (self.selected_tour_id,))
                discount = cursor.fetchone()[0]
                base_price = price * (1 - discount/100)
            else:
                cursor.execute('SELECT base_price FROM tours WHERE id = ?', (self.selected_tour_id,))
                base_price = cursor.fetchone()[0]
    
        #Тут множители цены в зависимости от уровня билета
        comfort_multiplier = {
            "Standard": 1.0,
            "Premium": 1.3,
            "Luxury": 1.8
        }
        multiplier = comfort_multiplier[self.cmb_comfort.currentText()]
        price = base_price * multiplier
    
        #Цена услуг
        service_prices = {"SPA": 50, "Экскурсии": 100, "Премиум питание": 75}
        for chk in self.chk_services:
            if chk.isChecked():
                price += service_prices[chk.text()]
    
        self.lbl_price.setText(f"Итоговая цена: ${price:.2f}")

    def confirm_booking(self, dialog):
        selected_services = [chk.text() for chk in self.chk_services if chk.isChecked()]
        cabin_type = self.cmb_comfort.currentText()
    
        success = BookingSystem.create_reservation(
            self.user_id,
            self.selected_tour_id,
            cabin_type,
            selected_services
        )
    
        if success:
            QMessageBox.information(self, "Успех", "Тур успешно забронирован!")
            dialog.accept()
            self.load_bookings_data()  # Refresh bookings tab
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось забронировать тур")

    def create_bookings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        #Список бронирований
        self.bookings_table = QTableWidget()
        self.bookings_table.verticalHeader().setDefaultSectionSize(50)
        self.bookings_table.horizontalHeader().setDefaultSectionSize(100)
        self.bookings_table.setColumnCount(6)
        self.bookings_table.setHorizontalHeaderLabels(
            ['Tour', 'Departure', 'Cabin', 'Services', 'Total Price', 'Actions']
        )
        self.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        #Подгружаем исходные данные
        self.load_bookings_data()
        
        layout.addWidget(QLabel("Мои брони:"))
        layout.addWidget(self.bookings_table)
        tab.setLayout(layout)
        return tab

    def load_bookings_data(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.name, t.departure_date, r.cabin_type, r.services, r.total_price, r.id
                FROM reservations r
                JOIN tours t ON r.tour_id = t.id
                WHERE r.user_id = ?
            ''', (self.user_id,))
            bookings = cursor.fetchall()

            self.bookings_table.setRowCount(len(bookings))
            for row_idx, (name, dep_date, cabin, services, price, res_id) in enumerate(bookings):
                self.bookings_table.setItem(row_idx, 0, QTableWidgetItem(name))
                self.bookings_table.setItem(row_idx, 1, QTableWidgetItem(dep_date))
                self.bookings_table.setItem(row_idx, 2, QTableWidgetItem(cabin))
                self.bookings_table.setItem(row_idx, 3, QTableWidgetItem(services))
                self.bookings_table.setItem(row_idx, 4, QTableWidgetItem(f"${price:.2f}"))
                
                # Add cancel button
                btn_cancel = QPushButton("Отмена")
                btn_cancel.clicked.connect(lambda _, rid=res_id: self.cancel_booking(rid))
                self.bookings_table.setCellWidget(row_idx, 5, btn_cancel)

    def cancel_booking(self, reservation_id):
        confirm = QMessageBox.question(
            self, "Подтверждение отмены", 
            "Вы уверены, что хотите отменить это бронирование?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            with db_connection() as conn:
                cursor = conn.cursor()
                try:
                    #Удалияем бронирование и возвращаем каюту
                    cursor.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
                    conn.commit()
                    self.load_bookings_data()
                    QMessageBox.information(self, "Успешно", "Бронирование успешно отменено.")
                except sqlite3.Error as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось отменить бронирование: {str(e)}")

    def create_reviews_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        #Список обзоров
        self.reviews_table = QTableWidget()
        self.reviews_table.verticalHeader().setDefaultSectionSize(50)
        self.reviews_table.horizontalHeader().setDefaultSectionSize(100)
        self.reviews_table.setColumnCount(4)
        self.reviews_table.setHorizontalHeaderLabels(['Тур', 'Рейтинг', 'Комментарий', 'Действия'])
        
        #Форма отзыва
        form_layout = QVBoxLayout()
        lbl_new = QLabel("Добавить новый отзыв:")
        
        self.cmb_tours = QComboBox()
        self.spin_rating = QSpinBox()
        self.spin_rating.setRange(1, 5)
        self.txt_comment = QTextEdit()
        btn_submit = QPushButton("Добавить отзыв")
        btn_submit.clicked.connect(self.submit_review)

        #Заполнение туров (комбо из брони + туры)
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.name FROM reservations r
                JOIN tours t ON r.tour_id = t.id
                WHERE r.user_id = ?
            ''', (self.user_id,))
            for tour_id, tour_name in cursor.fetchall():
                self.cmb_tours.addItem(tour_name, tour_id)
        form_layout.addWidget(lbl_new)
        form_layout.addWidget(QLabel("Тур:"))
        form_layout.addWidget(self.cmb_tours)
        form_layout.addWidget(QLabel("Рейтинг (1-5):"))
        form_layout.addWidget(self.spin_rating)
        form_layout.addWidget(QLabel("Комментарий:"))
        form_layout.addWidget(self.txt_comment)
        form_layout.addWidget(btn_submit)

        layout.addWidget(QLabel("Отзывы:"))
        layout.addWidget(self.reviews_table)
        layout.addLayout(form_layout)
        tab.setLayout(layout)
        self.load_reviews_data()
        return tab

    def load_reviews_data(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.name, r.rating, r.comment, r.id 
                FROM reviews r
                JOIN tours t ON r.tour_id = t.id
            ''', )
            reviews = cursor.fetchall()

            self.reviews_table.setRowCount(len(reviews))
            for row_idx, (name, rating, comment, rev_id) in enumerate(reviews):
                self.reviews_table.setItem(row_idx, 0, QTableWidgetItem(name))
                self.reviews_table.setItem(row_idx, 1, QTableWidgetItem(str(rating)))
                self.reviews_table.setItem(row_idx, 2, QTableWidgetItem(comment))
                
                # Add delete button
                btn_delete = QPushButton("Удалить")
                btn_delete.clicked.connect(lambda _, rid=rev_id: self.delete_review(rid))
                self.reviews_table.setCellWidget(row_idx, 3, btn_delete)

    def submit_review(self):
        selected = self.cmb_tours.currentText().split(" - ")
        #селектор возвращает пустую строку, не могу понять почему
        tour_id = self.cmb_tours.currentData()
        rating = self.spin_rating.value()
        comment = self.txt_comment.toPlainText()

        success, message = ReviewSystem.submit_review(
            self.user_id, tour_id, rating, comment
        )
        if success:
            QMessageBox.information(self, "Успешно", message)
            self.load_reviews_data()
            self.txt_comment.clear()
        else:
            QMessageBox.critical(self, "Ошибка", message)

    def delete_review(self, review_id):
        confirm = QMessageBox.question(
            self, "Подтвердите удаление", 
            "Вы уверены, что хотите удалить этот отзыв?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
                conn.commit()
                self.load_reviews_data()

    def create_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        form = QWidget()
        form_layout = QVBoxLayout()
        

        self.txt_tour_name = QLineEdit()
        self.txt_tour_desc = QTextEdit()
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setMaximum(999999)
        self.spin_price.setPrefix("$")
        self.date_edit = QDateEdit()
        self.txt_destination = QLineEdit()
        self.spin_duration = QSpinBox()
        self.spin_duration.setSuffix(" days")
        self.cmb_comfort = QComboBox()
        self.cmb_comfort.addItems(["Standard", "Premium", "Luxury"])
        self.spin_cabins = QSpinBox()
        
        btn_add = QPushButton("Добавить новый тур")
        btn_add.clicked.connect(self.add_tour)

        inputs = [
            ("Имя:", self.txt_tour_name),
            ("Описание:", self.txt_tour_desc),
            ("Базовая цена:", self.spin_price),
            ("Дата отбытия:", self.date_edit),
            ("Место назназчения:", self.txt_destination),
            ("Длительность:", self.spin_duration),
            ("Уровень комфорта:", self.cmb_comfort),
            ("Доступные каюты:", self.spin_cabins)
        ]

        for label, widget in inputs:
            form_layout.addWidget(QLabel(label))
            form_layout.addWidget(widget)

        form_layout.addWidget(btn_add)
        form.setLayout(form_layout)

        #Список туров
        self.tours_manage_table = QTableWidget()
        self.tours_manage_table.verticalHeader().setDefaultSectionSize(50)
        self.tours_manage_table.horizontalHeader().setDefaultSectionSize(100)
        self.tours_manage_table.setColumnCount(8)
        self.tours_manage_table.setHorizontalHeaderLabels(
            ['ID', 'Имя', 'Цена', 'Отбытие', 'Место назначения', 'Каюты', 'Уровень комфорта', 'Действия']
        )
        self.load_manage_tours_data()

        layout.addWidget(QLabel("Организация туров:"))
        layout.addWidget(form)
        layout.addWidget(self.tours_manage_table)
        tab.setLayout(layout)
        return tab

    def add_tour(self):
        success = TourManager.add_tour(
            name=self.txt_tour_name.text(),
            description=self.txt_tour_desc.toPlainText(),
            base_price=self.spin_price.value(),
            departure_date=self.date_edit.date().toString("yyyy-MM-dd"),
            destination=self.txt_destination.text(),
            duration=self.spin_duration.value(),
            comfort_level=self.cmb_comfort.currentText(),
            available_cabins=self.spin_cabins.value()
        )
        if success:
            QMessageBox.information(self, "Успех", "Тур добавлен.")
            self.load_manage_tours_data()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось добавить тур")

    def load_manage_tours_data(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tours')
            tours = cursor.fetchall()

            self.tours_manage_table.setRowCount(len(tours))
            for row_idx, row in enumerate(tours):
                for col_idx, value in enumerate(row[1:]):  # Skip ID
                    self.tours_manage_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
                
                #Добавляем кнопки редактировать/удалить
                btn_delete = QPushButton("Удалить")
                btn_delete.clicked.connect(lambda _, rid=row[0]: self.delete_tour(rid))
                
                btn_layout = QWidget()
                btn_layout.setLayout(QHBoxLayout())
                btn_layout.layout().addWidget(btn_delete)
                
                self.tours_manage_table.setCellWidget(row_idx, 7, btn_layout)

    def create_user_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.users_table = QTableWidget()
        self.users_table.verticalHeader().setDefaultSectionSize(50)
        self.users_table.horizontalHeader().setDefaultSectionSize(100)
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(
            ['ID', 'Имя пользователя', 'Роль', 'Email', 'Действия']
        )
        self.load_users_data()

        layout.addWidget(QLabel("Управление пользователями:"))
        layout.addWidget(self.users_table)
        tab.setLayout(layout)
        return tab

    def load_users_data(self):
        users = UserManager.get_all_users()
        self.users_table.setRowCount(len(users))
        for row_idx, (uid, username, role, email) in enumerate(users):
            self.users_table.setItem(row_idx, 0, QTableWidgetItem(str(uid)))
            self.users_table.setItem(row_idx, 1, QTableWidgetItem(username))
            self.users_table.setItem(row_idx, 2, QTableWidgetItem(role))
            self.users_table.setItem(row_idx, 3, QTableWidgetItem(email if email else ""))
            
            #Кнопки изменения роли + кнопка удаления
            cmb_role = QComboBox()
            cmb_role.addItems(['user', 'manager', 'admin'])
            cmb_role.setCurrentText(role)
            cmb_role.currentTextChanged.connect(
                lambda new_role, uid=uid: UserManager.update_user_role(uid, new_role)
            )
            
            btn_delete = QPushButton("Удалить")
            btn_delete.clicked.connect(lambda _, uid=uid: self.delete_user(uid))
            
            #Запрещаем удалиние своей записи в бд
            if uid == self.user_id and self.user_role == 'admin':
                btn_delete.setEnabled(False)

            btn_widget = QWidget()
            btn_widget.setLayout(QHBoxLayout())
            btn_widget.layout().addWidget(cmb_role)
            btn_widget.layout().addWidget(btn_delete)
            
            self.users_table.setCellWidget(row_idx, 4, btn_widget)

    def delete_user(self, user_id):
        if user_id == self.user_id:
            QMessageBox.warning(self, "Ошибка", "Вы не можете удалить свою учетную запись!")
            return

        confirm = QMessageBox.question(
            self, "Подтвердите удаление", 
            f"Удалить пользователя #{user_id}? Это действие невозможно отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if UserManager.delete_user(user_id):
                self.load_users_data()
                QMessageBox.information(self, "Успешно", "Пользователь удален")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить пользователя")

    def delete_special_offer(self, offer_id_inc):
        confirm = QMessageBox.question(
            self, "Подтвердите удаление", 
            f"Удалить тур #{offer_id_inc}? Это действие невозможно отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if BookingSystem.delete_special_offer(offer_id_inc):
                self.load_special_offers()
                QMessageBox.information(self, "Успешно", "Предложение удалено")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить предложение")

    def delete_tour(self, tour_id):
        confirm = QMessageBox.question(
            self, "Подтвердите удаление", 
            f"Удалить тур #{tour_id}? Это действие невозможно отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if TourManager.delete_tour(tour_id):
                self.load_manage_tours_data()
                QMessageBox.information(self, "Успешно", "Тур удален")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить тур")

    def create_special_offers_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
    
        #Вкладка специальных предложений
        self.offers_table = QTableWidget()
        self.offers_table.verticalHeader().setDefaultSectionSize(50)
        self.offers_table.horizontalHeader().setDefaultSectionSize(100)
        self.offers_table.setColumnCount(6)
        self.offers_table.setHorizontalHeaderLabels(
            ['Тур', 'Скидка', 'Начало', 'Конец', 'Цена со скидкой', 'Действия']
        )
        self.load_special_offers()
        layout.addWidget(self.offers_table)
    
        #Добавляем форму для менеджеров/администраторов
        if self.user_role in ['manager', 'admin']:
            form_layout = QFormLayout()
        
            self.cmb_offer_tour = QComboBox()
            self.spin_discount = QDoubleSpinBox()
            self.spin_discount.setRange(1, 100)
            self.spin_discount.setSuffix("%")
            self.date_start = QDateEdit(QDate.currentDate())
            self.date_end = QDateEdit(QDate.currentDate().addDays(30))
        
            form_layout.addRow("Тур:", self.cmb_offer_tour)
            form_layout.addRow("Скидка:", self.spin_discount)
            form_layout.addRow("Начало:", self.date_start)
            form_layout.addRow("Конец:", self.date_end)
        
            btn_add = QPushButton("Добавить спецпредложение")
            btn_add.clicked.connect(self.add_special_offer)
            form_layout.addRow(btn_add)
        
            layout.addLayout(form_layout)
            self.load_tours_for_offers()
    
        tab.setLayout(layout)
        return tab

    def load_tours_for_offers(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM tours')
            for tour_id, name in cursor.fetchall():
                self.cmb_offer_tour.addItem(name, tour_id)

    def load_special_offers(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT s.id, t.name, s.discount_percent, s.start_date, s.end_date, t.base_price, t.id
            FROM special_offers s
            JOIN tours t ON s.tour_id = t.id
            ''')
            offers = cursor.fetchall()
        
            self.offers_table.setRowCount(len(offers))
            for row_idx, (offer_id, name, discount, start, end, price, tour_id) in enumerate(offers):
                self.offers_table.setItem(row_idx, 0, QTableWidgetItem(name))
                self.offers_table.setItem(row_idx, 1, QTableWidgetItem(f"{discount}%"))
                self.offers_table.setItem(row_idx, 2, QTableWidgetItem(start))
                self.offers_table.setItem(row_idx, 3, QTableWidgetItem(end))
            
                #Рассчитываем цену со скидкой (можно позже использовать)
                discounted_price = price * (1 - discount/100)
                self.offers_table.setItem(row_idx, 4, QTableWidgetItem(f"${discounted_price:.2f}"))
            
                #Добавляем кнопку "Забронировать" для пользователей
                if self.user_role == 'user':
                    btn_book = QPushButton("Забронировать")
                    btn_book.clicked.connect(lambda _, tid=offer_id: self.book_tour_enable_discount(tid))
                    self.offers_table.setCellWidget(row_idx, 5, btn_book)
                #Добавляем кнопку удаления для менеджеров/администраторов
                elif self.user_role in ['manager', 'admin']:
                    btn_delete = QPushButton("Удалить")
                    btn_delete.clicked.connect(lambda _, oid=offer_id: self.delete_special_offer(oid))
                    self.offers_table.setCellWidget(row_idx, 5, btn_delete)

    def book_tour_enable_discount(self, tid):
        self.is_discount = True
        self.book_tour(tid)

    def add_special_offer(self):
        tour_id = self.cmb_offer_tour.currentData()
        discount = self.spin_discount.value()
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")
    
        with db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO special_offers (tour_id, discount_percent, start_date, end_date)
                    VALUES (?, ?, ?, ?)
                ''', (tour_id, discount, start_date, end_date))
                conn.commit()
                QMessageBox.information(self, "Успех", "Спецпредложение добавлено!")
                self.load_special_offers()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить предложение: {str(e)}")

    def create_cart_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
    
        self.cart_table = QTableWidget()
        self.cart_table.verticalHeader().setDefaultSectionSize(50)
        self.cart_table.horizontalHeader().setDefaultSectionSize(100)
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(
            ['Тур', 'Комфорт', 'Услуги', 'Цена', 'Действия']
        )
        self.lbl_cart_total = QLabel("Итого: $0.00")

        self.load_cart_data()
    
        btn_checkout = QPushButton("Оформить заказ")
        btn_checkout.clicked.connect(self.checkout)
    
        layout.addWidget(self.cart_table)
        layout.addWidget(self.lbl_cart_total)
        layout.addWidget(btn_checkout)
        tab.setLayout(layout)
        return tab

    def load_cart_data(self):
        self.cart_table.setRowCount(len(self.cart))
        total = 0
    
        for row_idx, item in enumerate(self.cart):
            tour_name, comfort, services, price = item
            total += price
        
            self.cart_table.setItem(row_idx, 0, QTableWidgetItem(tour_name))
            self.cart_table.setItem(row_idx, 1, QTableWidgetItem(comfort))
            self.cart_table.setItem(row_idx, 2, QTableWidgetItem(", ".join(services)))
            self.cart_table.setItem(row_idx, 3, QTableWidgetItem(f"${price:.2f}"))
        
            # Remove button
            btn_remove = QPushButton("Удалить")
            btn_remove.clicked.connect(lambda _, idx=row_idx: self.remove_from_cart(idx))
            self.cart_table.setCellWidget(row_idx, 4, btn_remove)
    
        self.lbl_cart_total.setText(f"Итого: ${total:.2f}")

    def remove_from_cart(self, index):
        self.cart.pop(index)
        self.load_cart_data()

    def checkout(self):
        for item in self.cart:
            tour_name, comfort, services, price = item
            # Get tour ID from name
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM tours WHERE name = ?', (tour_name,))
                tour_id = cursor.fetchone()[0]
        
            BookingSystem.create_reservation(
                self.user_id,
                tour_id,
                comfort,
                services,
                price
            )
    
        self.cart = []
        self.load_cart_data()
        QMessageBox.information(self, "Успех", "Заказ успешно оформлен!")

    #Изменяем функию book_tour для добавления в корзину
    def confirm_booking(self, dialog):
        selected_services = [chk.text() for chk in self.chk_services if chk.isChecked()]
        cabin_type = self.cmb_comfort.currentText()
    
        #Находим имя тура
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM tours WHERE id = (SELECT tour_id FROM special_offers WHERE id = ?)', (self.selected_tour_id,))
            tour_name = cursor.fetchone()[0]
    
        #Рассчитываем финальную цену
        price = float(self.lbl_price.text().split('$')[1])
    
        #Добавляем в корзину
        self.cart.append((tour_name, cabin_type, selected_services, price))
        self.load_cart_data()
    
        dialog.accept()
        QMessageBox.information(self, "Добавлено в корзину", "Тур добавлен в корзину!")

    def create_analytics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Date range selection
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("С:"))
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel("По:"))
        self.end_date_edit = QDateEdit(QDate.currentDate())
        date_layout.addWidget(self.end_date_edit)
        
        btn_update = QPushButton("Обновить")
        btn_update.clicked.connect(self.update_analytics)
        date_layout.addWidget(btn_update)
        
        layout.addLayout(date_layout)
        
        # Tab widget for different charts
        self.analytics_tabs = QTabWidget()
        
        # Create tabs and layouts
        self.tab1 = QWidget()
        self.tab1_layout = QVBoxLayout(self.tab1)
        
        self.tab2 = QWidget()
        self.tab2_layout = QVBoxLayout(self.tab2)
        
        self.tab3 = QWidget()
        self.tab3_layout = QVBoxLayout(self.tab3)
        
        self.analytics_tabs.addTab(self.tab1, "Популярность туров")
        self.analytics_tabs.addTab(self.tab2, "Спрос по датам")
        self.analytics_tabs.addTab(self.tab3, "Распределение по типам")
        
        layout.addWidget(self.analytics_tabs)
        tab.setLayout(layout)
        
        # Create initial figures
        self.create_figures()
        
        # Load initial data
        self.update_analytics()
        
        return tab
    
    def create_figures(self):
        # Create figure for tour popularity
        self.fig1 = Figure(figsize=(8, 4))
        self.canvas1 = FigureCanvas(self.fig1)
        self.tab1_layout.addWidget(self.canvas1)
        
        # Create figure for date demand
        self.fig2 = Figure(figsize=(8, 4))
        self.canvas2 = FigureCanvas(self.fig2)
        self.tab2_layout.addWidget(self.canvas2)
        
        # Create figure for comfort distribution
        self.fig3 = Figure(figsize=(8, 4))
        self.canvas3 = FigureCanvas(self.fig3)
        self.tab3_layout.addWidget(self.canvas3)
    
    def update_analytics(self):
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # Update all charts
        self.show_tour_popularity(start_date, end_date)
        self.show_date_demand(start_date, end_date)
        self.show_comfort_distribution(start_date, end_date)
    
    def show_tour_popularity(self, start_date, end_date):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.name, COUNT(r.id) as bookings
                FROM reservations r
                JOIN tours t ON r.tour_id = t.id
                WHERE r.booking_date BETWEEN ? AND ?
                GROUP BY t.name
                ORDER BY bookings DESC
                LIMIT 10
            ''', (start_date, end_date))
            results = cursor.fetchall()
        
        self.fig1.clear()
        ax = self.fig1.add_subplot(111)
        
        if results:
            names = [row[0] for row in results]
            bookings = [row[1] for row in results]
            
            # Create bar chart
            y_pos = np.arange(len(names))
            ax.barh(y_pos, bookings, align='center', color='royalblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names)
            ax.invert_yaxis()  # Top tour at the top
            ax.set_xlabel('Количество бронирований')
            ax.set_title('Топ 10 популярных туров')
        
        self.canvas1.draw()
    
    def show_date_demand(self, start_date, end_date):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT booking_date, COUNT(id) as bookings
                FROM reservations
                WHERE booking_date BETWEEN ? AND ?
                GROUP BY booking_date
                ORDER BY booking_date
            ''', (start_date, end_date))
            results = cursor.fetchall()
        
        self.fig2.clear()
        ax = self.fig2.add_subplot(111)
        
        if results:
            dates = [py_datetime.strptime(row[0], '%Y-%m-%d') for row in results]
            bookings = [row[1] for row in results]
            
            # Create line chart
            ax.plot(dates, bookings, 'o-', color='green')
            ax.set_xlabel('Дата бронирования')
            ax.set_ylabel('Количество бронирований')
            ax.set_title('Спрос по датам бронирования')
            
            # Format date labels
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            self.fig2.autofmt_xdate()  # Rotate dates
        
        self.canvas2.draw()
    
    def show_comfort_distribution(self, start_date, end_date):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cabin_type, COUNT(id) as bookings
                FROM reservations
                WHERE booking_date BETWEEN ? AND ?
                GROUP BY cabin_type
            ''', (start_date, end_date))
            results = cursor.fetchall()
        
        self.fig3.clear()
        ax = self.fig3.add_subplot(111)
        
        if results:
            types = [row[0] for row in results]
            bookings = [row[1] for row in results]
            
            # Create pie chart
            colors = ['gold', 'yellowgreen', 'lightcoral']
            ax.pie(bookings, labels=types, autopct='%1.1f%%',
                   colors=colors, startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures pie is circular
            ax.set_title('Распределение по классам кают')
        
        self.canvas3.draw()