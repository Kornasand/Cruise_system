import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from auth import AuthSystem
from dashboard import Dashboard

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.show_login()

    def show_login(self):
        from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout

        self.login_widget = QWidget()
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.handle_login)
        
        register_btn = QPushButton("Зарегистрироваться")
        register_btn.clicked.connect(self.handle_register)

        layout.addWidget(QLabel("Вход в круизную систему"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)
        
        self.login_widget.setLayout(layout)
        self.setCentralWidget(self.login_widget)
        self.setWindowTitle("Круизная система - Вход")
        self.resize(300, 200)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        success, message, user_data = AuthSystem.login_user(username, password)
        
        if success:
            self.show_dashboard(user_data)
        else:
            QMessageBox.critical(self, "Ошибка входа", message)

    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        success, message = AuthSystem.register_user(username, password)
        if success:
            QMessageBox.information(self, "Успешно", message)
        else:
            QMessageBox.critical(self, "Не удалось выполнить регистрацию", message)

    def show_dashboard(self, user_data):
        self.dashboard = Dashboard(user_data['role'], user_data['id'])
        self.setCentralWidget(self.dashboard)
        self.setWindowTitle(f"Круизная система - {user_data['role'].capitalize()} Приборная панель")
        self.resize(1024, 768)

if __name__ == "__main__":
    #Инициализация базы данных, можно потом убрать
    from database import initialize_database
    initialize_database()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())