# sigvcf/modules/administrativo/viewmodels.py
from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot, QDate
from typing import List, Dict, Any

from containers import Container
from sigvcf.modules.administrativo.services import AdministrativoService
from sigvcf.modules.administrativo.dto import ContratoDTO, ArticuloContratoDTO
# Asumimos que existe un DTO simple para proveedores y un método en el servicio para listarlos
from sigvcf.modules.proveedores.dto import ProveedorDTO

class ContratoViewModel(QObject):
    """
    ViewModel para la gestión de Contratos.
    Orquesta la interacción entre la Vista (UI) y el Servicio de Aplicación.
    """
    # --- Señales (Salidas hacia la Vista) ---
    # Emite la lista de todos los contratos para la tabla principal
    contratos_changed = Signal(list)
    # Emite la lista de proveedores para el ComboBox del formulario
    proveedores_changed = Signal(list)
    # Emite el contrato seleccionado para poblar el formulario de edición
    contrato_actual_changed = Signal(object)
    # Emite mensajes de estado para el usuario
    status_message = Signal(str)

    @inject
    def __init__(
        self,
        admin_service: AdministrativoService = Provide[Container.administrativo_service],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self._admin_service = admin_service
        # Asumimos que el servicio puede listar proveedores
        # En un caso real, se añadiría este método al servicio
        self._admin_service.listar_proveedores = self._listar_proveedores_impl
        self._contrato_actual_id = None

    def _listar_proveedores_impl(self) -> List[ProveedorDTO]:
        """Implementación temporal para listar proveedores desde la UoW."""
        with self._admin_service.uow:
            proveedores = self._admin_service.uow.proveedores.list()
            return [ProveedorDTO(id=p.id, razon_social=p.razon_social) for p in proveedores]

    # --- Slots (Entradas desde la Vista) ---

    @Slot()
    def cargar_datos_iniciales(self):
        """Carga los datos necesarios para poblar la vista inicialmente."""
        try:
            contratos = self._admin_service.uow.contratos.list() # Usamos listado simple para la tabla
            contratos_dto = [ContratoDTO.from_orm(c) for c in contratos]
            self.contratos_changed.emit(contratos_dto)

            proveedores = self._admin_service.listar_proveedores()
            self.proveedores_changed.emit(proveedores)
        except Exception as e:
            self.status_message.emit(f"Error al cargar datos: {e}")

    @Slot(int)
    def seleccionar_contrato(self, contrato_id: int):
        """Carga los detalles completos de un contrato para su edición."""
        self._contrato_actual_id = contrato_id
        try:
            with self._admin_service.uow:
                contrato = self._admin_service.uow.contratos.get(contrato_id)
                if contrato:
                    contrato_dto = ContratoDTO.from_orm(contrato)
                    self.contrato_actual_changed.emit(contrato_dto)
                else:
                    self.status_message.emit(f"No se encontró el contrato con ID {contrato_id}")
        except Exception as e:
            self.status_message.emit(f"Error al seleccionar contrato: {e}")

    @Slot()
    def crear_nuevo_contrato(self):
        """Prepara un DTO vacío para crear un nuevo contrato."""
        self._contrato_actual_id = None
        nuevo_contrato = ContratoDTO(
            codigo_licitacion="",
            fecha_inicio=QDate.currentDate().toPython(),
            fecha_fin=QDate.currentDate().addYears(1).toPython(),
            proveedor_id=0, # La vista deberá manejar esto
            articulos=[]
        )
        self.contrato_actual_changed.emit(nuevo_contrato)

    @Slot(dict)
    def guardar_contrato_actual(self, contrato_data: Dict[str, Any]):
        """Recibe los datos del formulario y los persiste a través del servicio."""
        try:
            # Convertir el diccionario de la vista a DTOs de Pydantic
            articulos_dto = [ArticuloContratoDTO(**art) for art in contrato_data.get("articulos", [])]
            contrato_dto = ContratoDTO(
                id=self._contrato_actual_id,
                codigo_licitacion=contrato_data["codigo_licitacion"],
                expediente_path=contrato_data.get("expediente_path"),
                fecha_inicio=contrato_data["fecha_inicio"],
                fecha_fin=contrato_data["fecha_fin"],
                proveedor_id=contrato_data["proveedor_id"],
                articulos=articulos_dto
            )
            
            self._admin_service.crear_o_actualizar_contrato(contrato_dto)
            self.status_message.emit("Contrato guardado con éxito.")
            self.cargar_datos_iniciales() # Recargar la lista
        except Exception as e:
            self.status_message.emit(f"Error al guardar el contrato: {e}")