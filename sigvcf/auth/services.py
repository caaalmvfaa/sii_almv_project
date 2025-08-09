import bcrypt
from sqlalchemy.orm import joinedload
from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.core.domain.models import Usuario

class AuthService:
    """
    Servicio de aplicación para la autenticación de usuarios.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def autenticar_usuario(self, nombre_usuario: str, contrasena: str) -> dict | None:
        """
        Verifica las credenciales de un usuario contra la base de datos.

        Args:
            nombre_usuario: El nombre de usuario a verificar.
            contrasena: La contraseña en texto plano.

        Returns:
            El objeto Usuario si la autenticación es exitosa, de lo contrario None.
        """
        with self.uow:
            # Buscar usuario por nombre usando el repositorio
            usuario = self.uow.usuarios.find_one_by(nombre=nombre_usuario)
            if not usuario:
                return None

            # --- Verificación de Contraseña Segura con bcrypt ---
            if usuario.password_hash and bcrypt.checkpw(contrasena.encode('utf-8'), usuario.password_hash.encode('utf-8')):
                usuario_dict = {
                    'id': usuario.id,
                    'nombre': usuario.nombre,
                    'rol': {
                        'id': usuario.rol.id if usuario.rol else None,
                        'nombre_rol': usuario.rol.nombre_rol if usuario.rol else None
                    }
                }
                return usuario_dict
            return None
