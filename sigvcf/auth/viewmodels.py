# sigvcf/auth/viewmodels.py
import logging
from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot

 # Eliminado import directo de Container para evitar ciclo
from sigvcf.auth.services import AuthService

logger = logging.getLogger(__name__)

class LoginViewModel(QObject):
    login_exitoso = Signal(object)
    login_fallido = Signal(str)

    @inject
    def __init__(
        self,
        auth_service: AuthService = Provide["Container.auth_service"],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.auth_service = auth_service

    @Slot(str, str)
    def intentar_login(self, usuario: str, contrasena: str):
        logger.info(f"ViewModel: Intentando login para el usuario '{usuario}'.")
        if not usuario or not contrasena:
            msg = "El nombre de usuario y la contraseña no pueden estar vacíos."
            logger.warning(msg)
            self.login_fallido.emit(msg)
            return

        try:
            usuario_autenticado = self.auth_service.autenticar_usuario(usuario, contrasena)
            if usuario_autenticado:
                logger.info(f"ViewModel: Login exitoso para '{usuario}'.")
                self.login_exitoso.emit(usuario_autenticado)
            else:
                logger.warning(f"ViewModel: Login fallido para '{usuario}'.")
                self.login_fallido.emit("Credenciales incorrectas. Por favor, intente de nuevo.")
        except Exception as e:
            logger.error(f"ViewModel: Error en el proceso de login: {e}", exc_info=True)
            self.login_fallido.emit("Ocurrió un error inesperado. Consulte el log de la aplicación.")
