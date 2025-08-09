# sigvcf/infrastructure/persistence/repositories.py
import abc
from typing import List, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sigvcf.core.domain import models

T = TypeVar('T')

class AbstractRepository(Generic[T], abc.ABC):
    """
    Repositorio abstracto que define la interfaz para la persistencia de entidades.
    """
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self._model_class = model_class

    def add(self, entity: T) -> None:
        """Añade una nueva entidad a la sesión."""
        self.session.add(entity)

    def get(self, entity_id: int) -> T | None:
        """Obtiene una entidad por su ID."""
        return self.session.get(self._model_class, entity_id)

    def list(self) -> List[T]:
        """Devuelve una lista de todas las entidades."""
        return self.session.query(self._model_class).all()
        
    def find(self, **kwargs) -> List[T]:
        """Encuentra entidades que coinciden con los criterios."""
        return self.session.query(self._model_class).filter_by(**kwargs).all()

# --- Implementaciones Concretas de Repositorios ---

class RolRepository(AbstractRepository[models.Rol]):
    def __init__(self, session: Session):
        super().__init__(session, models.Rol)

class UsuarioRepository(AbstractRepository[models.Usuario]):
    def __init__(self, session: Session):
        super().__init__(session, models.Usuario)

class ProveedorRepository(AbstractRepository[models.Proveedor]):
    def __init__(self, session: Session):
        super().__init__(session, models.Proveedor)

class ContratoRepository(AbstractRepository[models.Contrato]):
    def __init__(self, session: Session):
        super().__init__(session, models.Contrato)

class ArticuloContratoRepository(AbstractRepository[models.ArticuloContrato]):
    def __init__(self, session: Session):
        super().__init__(session, models.ArticuloContrato)

class ProgramacionMensualRepository(AbstractRepository[models.ProgramacionMensual]):
    def __init__(self, session: Session):
        super().__init__(session, models.ProgramacionMensual)

class SalidaRequerimientoRepository(AbstractRepository[models.SalidaRequerimiento]):
    def __init__(self, session: Session):
        super().__init__(session, models.SalidaRequerimiento)

class OrdenDeCompraRepository(AbstractRepository[models.OrdenDeCompra]):
    def __init__(self, session: Session):
        super().__init__(session, models.OrdenDeCompra)

class EntradaBodegaRepository(AbstractRepository[models.EntradaBodega]):
    def __init__(self, session: Session):
        super().__init__(session, models.EntradaBodega)

class ReporteIncumplimientoRepository(AbstractRepository[models.ReporteIncumplimiento]):
    def __init__(self, session: Session):
        super().__init__(session, models.ReporteIncumplimiento)

class RegistroContableRepository(AbstractRepository[models.RegistroContable]):
    def __init__(self, session: Session):
        super().__init__(session, models.RegistroContable)