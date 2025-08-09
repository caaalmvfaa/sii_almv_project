# sigvcf/auth/services.py
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
            # Buscar usuario por nombre. find() devuelve una lista.
            usuarios_encontrados = self.uow.usuarios.find(nombre=nombre_usuario)
            if not usuarios_encontrados:
                return None
            
            usuario = usuarios_encontrados[0]

            # --- Verificación de Contraseña ---
            # En un sistema real, NUNCA se debe comparar texto plano.
            # Se debe usar una librería como bcrypt:
            # import bcrypt
            # if bcrypt.checkpw(contrasena.encode('utf-8'), usuario.password_hash.encode('utf-8')):
            #     return usuario
            #
            # Para este ejercicio, se usa una comparación simple como se solicitó.
            if usuario.password_hash == contrasena:
                # Cargar la relación de rol explícitamente si es necesario
                _ = usuario.rol 
                return usuario
            
            return None