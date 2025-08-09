import abc
from typing import Generic, List, Type, TypeVar
from sqlalchemy.orm import Session

T = TypeVar("T")

class AbstractRepository(abc.ABC, Generic[T]):
    """
    Interfaz abstracta para un patrón de repositorio genérico.
    """
    @abc.abstractmethod
    def add(self, model: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, id) -> T | None:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def find(self, **kwargs) -> List[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def find_one_by(self, **kwargs) -> T | None:
        """
        Busca un único registro que coincida con los criterios.
        """
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository[T]):
    """
    Implementación concreta del patrón de repositorio usando SQLAlchemy.
    """
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def add(self, model: T) -> None:
        self.session.add(model)

    def get(self, id) -> T | None:
        return self.session.get(self.model, id)

    def list(self) -> List[T]:
        return self.session.query(self.model).all()

    def find(self, **kwargs) -> List[T]:
        return self.session.query(self.model).filter_by(**kwargs).all()

    def find_one_by(self, **kwargs) -> T | None:
        """
        Implementación eficiente para buscar un único registro.
        Utiliza one_or_none() para evitar excepciones si no se encuentra
        o si se encuentran múltiples registros.
        """
        return self.session.query(self.model).filter_by(**kwargs).one_or_none()

### FILE: sigvcf/infrastructure/persistence/repositories.py
from sqlalchemy.orm import Session
from sigvcf.infrastructure.persistence.repository import SQLAlchemyRepository
from sigvcf.core.domain.models import (
    Rol,
    Usuario,
    Proveedor,
    Contrato,
    ArticuloContrato,
    OrdenDeCompra,
    EntradaBodega,
    RegistroContable,
    ProgramacionMensual,
    SalidaRequerimiento,
    ReporteIncumplimiento,
)

class RolRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, Rol)

class UsuarioRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, Usuario)

class ProveedorRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, Proveedor)

class ContratoRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, Contrato)

class ArticuloContratoRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, ArticuloContrato)

class OrdenDeCompraRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, OrdenDeCompra)

class EntradaBodegaRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, EntradaBodega)

class RegistroContableRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, RegistroContable)

class ProgramacionMensualRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, ProgramacionMensual)

class SalidaRequerimientoRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, SalidaRequerimiento)

class ReporteIncumplimientoRepository(SQLAlchemyRepository):
    def __init__(self, session: Session):
        super().__init__(session, ReporteIncumplimiento)
