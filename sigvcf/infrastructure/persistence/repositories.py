
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
