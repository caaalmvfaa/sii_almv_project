from dependency_injector import containers, providers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Service Imports
from sigvcf.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from sigvcf.auth.services import AuthService
from sigvcf.modules.almacen.services import AlmacenService
from sigvcf.modules.nutricion.services import NutricionService
from sigvcf.modules.juridico.services import JuridicoService
from sigvcf.modules.administrativo.services import AdministrativoService
from sigvcf.modules.financiero.services import FinancieroService
from sigvcf.modules.proveedores.services import ProveedorService

# ViewModel Imports
from sigvcf.auth.viewmodels import LoginViewModel
from sigvcf.modules.almacen.viewmodels import AlmacenViewModel
from sigvcf.modules.nutricion.viewmodels import NutricionViewModel
from sigvcf.modules.juridico.viewmodels import JuridicoViewModel
from sigvcf.modules.administrativo.viewmodels import ContratoViewModel
from sigvcf.modules.financiero.viewmodels import FinancieroViewModel
from sigvcf.modules.proveedores.viewmodels import ProveedorViewModel


class Container(containers.DeclarativeContainer):
    """
    Contenedor de Inyección de Dependencias para la aplicación SIG-VCF.
    """
    # --- 1. Configuración ---
    config = providers.Configuration()
    config.db.url.from_value("sqlite:///sigvcf_data.db")

    # --- 2. Infraestructura ---
    db_engine = providers.Singleton(create_engine, url=config.db.url, echo=False)
    session_factory = providers.Singleton(sessionmaker, bind=db_engine, autoflush=False, autocommit=False)
    uow = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)

    # --- 3. Servicios de Aplicación ---
    auth_service = providers.Factory(AuthService, uow=uow)
    almacen_service = providers.Factory(AlmacenService, uow=uow)
    nutricion_service = providers.Factory(NutricionService, uow=uow)
    juridico_service = providers.Factory(JuridicoService, uow=uow)
    administrativo_service = providers.Factory(AdministrativoService, uow=uow)
    financiero_service = providers.Factory(FinancieroService, uow=uow)
    proveedor_service = providers.Factory(ProveedorService, uow=uow)

    # --- 4. ViewModels (Capa de Presentación) ---
    login_view_model = providers.Factory(LoginViewModel, auth_service=auth_service)
    almacen_view_model = providers.Factory(AlmacenViewModel, almacen_service=almacen_service)
    nutricion_view_model = providers.Factory(NutricionViewModel, nutricion_service=nutricion_service)
    juridico_view_model = providers.Factory(JuridicoViewModel, juridico_service=juridico_service)
    contrato_view_model = providers.Factory(ContratoViewModel, administrativo_service=administrativo_service)
    financiero_view_model = providers.Factory(FinancieroViewModel, financiero_service=financiero_service)
    proveedor_view_model = providers.Factory(ProveedorViewModel, proveedor_service=proveedor_service)
