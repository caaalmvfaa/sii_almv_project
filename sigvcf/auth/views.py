# sigvcf/auth/views.py
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont

from sigvcf.auth.viewmodels import LoginViewModel

class LoginView(QDialog):
    """
    Ventana de diálogo modal para la autenticación de usuarios.
    """
    def __init__(self, view_model: LoginViewModel):
        super().__init__()
        self.vm = view_model
        self.setWindowTitle("Inicio de Sesión - SIG-VCF")
        self.setModal(True)
        self.setMinimumWidth(350)

        # --- UI Setup ---
        main_layout = QVBoxLayout(self)
        
        title = QLabel("Sistema Integral de Gestión")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        self.usuario_edit = QLineEdit()
        self.usuario_edit.setPlaceholderText("Nombre de usuario")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Contraseña")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("Usuario:", self.usuario_edit)
        form_layout.addRow("Contraseña:", self.password_edit)
        
        self.login_button = QPushButton("Ingresar")
        
        main_layout.addWidget(title)
        main_layout.addWidget(form_widget)
        main_layout.addWidget(self.login_button)

        # --- Conexiones ---
        self.login_button.clicked.connect(self._on_login_clicked)
        self.vm.login_exitoso.connect(self.accept) # QDialog.accept() cierra el diálogo con resultado Aceptado
        self.vm.login_fallido.connect(self._show_error_message)

    @Slot()
    def _on_login_clicked(self):
        usuario = self.usuario_edit.text()
        password = self.password_edit.text()
        self.vm.intentar_login(usuario, password)

    @Slot(str)
    def _show_error_message(self, message: str):
        QMessageBox.warning(self, "Error de Autenticación", message)