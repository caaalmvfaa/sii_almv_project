# sigvcf/auth/viewmodels.py
from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot

from sigvcf.containers import Container
from sigvcf.auth.services import AuthService

class LoginViewModel(QObject):
    """
    ViewModel para la pantalla de Login.
    """
    # Señal emitida con el objeto Usuario en un login exitoso
    login_exitoso = Signal(object)
    # Señal emitida con un mensaje de error en un login fallido
    login_fallido = Signal(str)

    @inject
    def __init__(
        self,
        auth_service: AuthService = Provide[Container.auth_service],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.auth_service = auth_service

    @Slot(str, str)
    def intentar_login(self, usuario: str, contrasena: str):
        """
        Intenta autenticar al usuario usando el servicio de autenticación.
        """
        if not usuario or not contrasena:
            self.login_fallido.emit("El nombre de usuario y la contraseña no pueden estar vacíos.")
            return

        usuario_autenticado = self.auth_service.autenticar_usuario(usuario, contrasena)

        if usuario_autenticado:
            self.login_exitoso.emit(usuario_autenticado)
        else:
            self.login_fallido.emit("Credenciales incorrectas. Por favor, intente de nuevo.")