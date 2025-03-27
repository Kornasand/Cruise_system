from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLabel, QLineEdit, QComboBox, QSpinBox, 
    QDoubleSpinBox, QTextEdit, QMessageBox, 
    QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from database import db_connection
from booking import BookingSystem
from reviews import ReviewSystem
from tour_manager import TourManager
from user_manager import UserManager

class Dashboard(QWidget):
    def __init__(self, user_role, user_id):
        super().__init__()
        self.user_role = user_role
        self.user_id = user_id
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Cruise System Dashboard')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        #Общие вкладки
        self.tabs.addTab(self.create_profile_tab(), "Профиль")
        self.tabs.addTab(self.create_tours_tab(), "Доступные туры")

        #Пользовательские вкладки, зависимые от роли
        if self.user_role == 'user':
            self.tabs.addTab(self.create_bookings_tab(), "Мои бронирования")
            self.tabs.addTab(self.create_reviews_tab(), "Мои отзывы")
        elif self.user_role == 'manager':
            self.tabs.addTab(self.create_management_tab(), "Организация туров")
        elif self.user_role == 'admin':
            self.tabs.addTab(self.create_user_management_tab(), "Управление пользователями")

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
        self.tours_table.setColumnCount(6)
        self.tours_table.setHorizontalHeaderLabels(
            ['Name', 'Destination', 'Departure', 'Duration', 'Price', 'Cabins']
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
                SELECT name, destination, departure_date, duration, base_price, available_cabins
                FROM tours
            ''')
            tours = cursor.fetchall()
            
            self.tours_table.setRowCount(len(tours))
            for row_idx, row_data in enumerate(tours):
                for col_idx, value in enumerate(row_data):
                    self.tours_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def create_bookings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        #Список бронирований
        self.bookings_table = QTableWidget()
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
                    # Delete reservation and restore cabin
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
        self.reviews_table.setColumnCount(4)
        self.reviews_table.setHorizontalHeaderLabels(['Tour', 'Rating', 'Comment', 'Actions'])
        
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
            self.cmb_tours.addItems([f"{row[0]} - {row[1]}" for row in cursor.fetchall()])

        form_layout.addWidget(lbl_new)
        form_layout.addWidget(QLabel("Tour:"))
        form_layout.addWidget(self.cmb_tours)
        form_layout.addWidget(QLabel("Rating (1-5):"))
        form_layout.addWidget(self.spin_rating)
        form_layout.addWidget(QLabel("Comment:"))
        form_layout.addWidget(self.txt_comment)
        form_layout.addWidget(btn_submit)

        layout.addWidget(QLabel("My Reviews:"))
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
                WHERE r.user_id = ?
            ''', (self.user_id,))
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
        #селектор возвращает строку, не могу понять почему
        tour_id = int(selected[0])
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

        # Add Tour Form
        form = QWidget()
        form_layout = QVBoxLayout()
        
        self.txt_tour_name = QLineEdit()
        self.txt_tour_desc = QTextEdit()
        self.spin_price = QDoubleSpinBox()
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
            ("Name:", self.txt_tour_name),
            ("Description:", self.txt_tour_desc),
            ("Base Price:", self.spin_price),
            ("Departure Date:", self.date_edit),
            ("Destination:", self.txt_destination),
            ("Duration:", self.spin_duration),
            ("Comfort Level:", self.cmb_comfort),
            ("Available Cabins:", self.spin_cabins)
        ]

        for label, widget in inputs:
            form_layout.addWidget(QLabel(label))
            form_layout.addWidget(widget)

        form_layout.addWidget(btn_add)
        form.setLayout(form_layout)

        #Список туров
        self.tours_manage_table = QTableWidget()
        self.tours_manage_table.setColumnCount(8)
        self.tours_manage_table.setHorizontalHeaderLabels(
            ['ID', 'Name', 'Price', 'Departure', 'Destination', 'Cabins', 'Comfort', 'Actions']
        )
        self.load_manage_tours_data()

        layout.addWidget(QLabel("Manage Tours:"))
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
                btn_edit = QPushButton("Редактировать")
                btn_delete = QPushButton("Удалить")
                btn_edit.clicked.connect(lambda _, rid=row[0]: self.edit_tour(rid))
                btn_delete.clicked.connect(lambda _, rid=row[0]: self.delete_tour(rid))
                
                btn_layout = QWidget()
                btn_layout.setLayout(QHBoxLayout())
                btn_layout.layout().addWidget(btn_edit)
                btn_layout.layout().addWidget(btn_delete)
                
                self.tours_manage_table.setCellWidget(row_idx, 7, btn_layout)

    def create_user_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.users_table = QTableWidget()
        self.users_table.verticalHeader().setDefaultSectionSize(50)
        self.users_table.horizontalHeader().setDefaultSectionSize(200)
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(
            ['ID', 'Username', 'Role', 'Email', 'Actions']
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
            
            # Disable delete for current admin
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