import abc
from sqlalchemy.orm import Session, sessionmaker
from sigvcf.infrastructure.persistence import repositories

class IUnitOfWork(abc.ABC):
    """Interfaz abstracta para la Unidad de Trabajo con repositorios como propiedades."""

    @property
    @abc.abstractmethod
    def roles(self) -> repositories.RolRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def usuarios(self) -> repositories.UsuarioRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def proveedores(self) -> repositories.ProveedorRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def contratos(self) -> repositories.ContratoRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def articulos_contrato(self) -> repositories.ArticuloContratoRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def programaciones_mensuales(self) -> repositories.ProgramacionMensualRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def salidas_requerimiento(self) -> repositories.SalidaRequerimientoRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def ordenes_de_compra(self) -> repositories.OrdenDeCompraRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def entradas_bodega(self) -> repositories.EntradaBodegaRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def reportes_incumplimiento(self) -> repositories.ReporteIncumplimientoRepository:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def registros_contables(self) -> repositories.RegistroContableRepository:
        raise NotImplementedError

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
    """
    Implementación de la Unidad de Trabajo con SQLAlchemy y repositorios lazy-loaded.
    """
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
        self._repositories = {}

    def __enter__(self):
        self.session: Session = self.session_factory()
        # Limpiar el caché de repositorios para esta nueva sesión
        self._repositories.clear()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, traceback):
        super().__exit__(exc_type, exc_val, traceback)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def _get_repository(self, name: str, repo_class: type) -> any:
        """Función de ayuda genérica para obtener/crear un repositorio."""
        if name not in self._repositories:
            self._repositories[name] = repo_class(self.session)
        return self._repositories[name]

    @property
    def roles(self) -> repositories.RolRepository:
        return self._get_repository("roles", repositories.RolRepository)

    @property
    def usuarios(self) -> repositories.UsuarioRepository:
        return self._get_repository("usuarios", repositories.UsuarioRepository)

    @property
    def proveedores(self) -> repositories.ProveedorRepository:
        return self._get_repository("proveedores", repositories.ProveedorRepository)

    @property
    def contratos(self) -> repositories.ContratoRepository:
        return self._get_repository("contratos", repositories.ContratoRepository)

    @property
    def articulos_contrato(self) -> repositories.ArticuloContratoRepository:
        return self._get_repository("articulos_contrato", repositories.ArticuloContratoRepository)

    @property
    def programaciones_mensuales(self) -> repositories.ProgramacionMensualRepository:
        return self._get_repository("programaciones_mensuales", repositories.ProgramacionMensualRepository)

    @property
    def salidas_requerimiento(self) -> repositories.SalidaRequerimientoRepository:
        return self._get_repository("salidas_requerimiento", repositories.SalidaRequerimientoRepository)

    @property
    def ordenes_de_compra(self) -> repositories.OrdenDeCompraRepository:
        return self._get_repository("ordenes_de_compra", repositories.OrdenDeCompraRepository)

    @property
    def entradas_bodega(self) -> repositories.EntradaBodegaRepository:
        return self._get_repository("entradas_bodega", repositories.EntradaBodegaRepository)



    @property
    def reportes_incumplimiento(self) -> repositories.ReporteIncumplimientoRepository:
        return self._get_repository("reportes_incumplimiento", repositories.ReporteIncumplimientoRepository)

    @property
    def registros_contables(self) -> repositories.RegistroContableRepository:
        return self._get_repository("registros_contables", repositories.RegistroContableRepository)
