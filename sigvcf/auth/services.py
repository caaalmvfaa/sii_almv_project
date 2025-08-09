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

    def autenticar_usuario(self, nombre_usuario: str, contrasena: str) -> Usuario | None:
        """
        Verifica las credenciales de un usuario contra la base de datos.

        Args:
            nombre_usuario: El nombre de usuario a verificar.
            contrasena: La contraseña en texto plano.

        Returns:
            El objeto Usuario si la autenticación es exitosa, de lo contrario None.
        """
        with self.uow:
            # Buscar usuario por nombre, precargando la relación 'rol' para evitar N+1 queries.
            usuario = self.uow.session.query(Usuario).options(
                joinedload(Usuario.rol)
            ).filter_by(nombre=nombre_usuario).one_or_none()

            if not usuario:
                return None

            # --- Verificación de Contraseña Segura con bcrypt ---
            # Se compara la contraseña de entrada con el hash almacenado usando bcrypt.
            # bcrypt.checkpw maneja la sal internamente, que está incluida en el hash.
            if usuario.password_hash and bcrypt.checkpw(contrasena.encode('utf-8'), usuario.password_hash.encode('utf-8')):
                # La relación 'rol' ya está cargada gracias a joinedload.
                # La siguiente línea ya no causa una consulta adicional.
                _ = usuario.rol 
                return usuario
            
            return None
