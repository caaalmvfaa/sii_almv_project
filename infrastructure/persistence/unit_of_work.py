# sigvcf/infrastructure/persistence/unit_of_work.py
import abc
from sqlalchemy.orm import Session, sessionmaker
from sigvcf.infrastructure.persistence import repositories

class IUnitOfWork(abc.ABC):
    """Interfaz abstracta para la Unidad de Trabajo."""
    roles: repositories.RolRepository
    usuarios: repositories.UsuarioRepository
    proveedores: repositories.ProveedorRepository
    contratos: repositories.ContratoRepository
    articulos_contrato: repositories.ArticuloContratoRepository
    programaciones_mensuales: repositories.ProgramacionMensualRepository
    salidas_requerimiento: repositories.SalidaRequerimientoRepository
    ordenes_de_compra: repositories.OrdenDeCompraRepository
    entradas_bodega: repositories.EntradaBodegaRepository
    reportes_incumplimiento: repositories.ReporteIncumplimientoRepository
    registros_contables: repositories.RegistroContableRepository

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type:
            self.rollback()
        else:
            self.commit()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError

class SqlAlchemyUnitOfWork(IUnitOfWork):
    """Implementación de la Unidad de Trabajo con SQLAlchemy."""
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def __enter__(self):
        self.session: Session = self.session_factory()
        
        # Instanciar repositorios
        self.roles = repositories.RolRepository(self.session)
        self.usuarios = repositories.UsuarioRepository(self.session)
        self.proveedores = repositories.ProveedorRepository(self.session)
        self.contratos = repositories.ContratoRepository(self.session)
        self.articulos_contrato = repositories.ArticuloContratoRepository(self.session)
        self.programaciones_mensuales = repositories.ProgramacionMensualRepository(self.session)
        self.salidas_requerimiento = repositories.SalidaRequerimientoRepository(self.session)
        self.ordenes_de_compra = repositories.OrdenDeCompraRepository(self.session)
        self.entradas_bodega = repositories.EntradaBodegaRepository(self.session)
        self.reportes_incumplimiento = repositories.ReporteIncumplimientoRepository(self.session)
        self.registros_contables = repositories.RegistroContableRepository(self.session)
        
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, traceback):
        super().__exit__(exc_type, exc_val, traceback)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()