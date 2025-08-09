from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot, QDate
from PySide6.QtWidgets import QFileDialog, QWidget
from typing import List, Dict, Any

 # Eliminado import directo de Container para evitar ciclo
from sigvcf.modules.administrativo.services import AdministrativoService
from sigvcf.modules.administrativo.dto import ContratoDTO, ArticuloContratoDTO
from sigvcf.modules.proveedores.dto import ProveedorDTO

class ContratoViewModel(QObject):
    """
    ViewModel para la gestión de Contratos.
    Orquesta la interacción entre la Vista (UI) y el Servicio de Aplicación.
    """
    contratos_changed = Signal(list)
    proveedores_changed = Signal(list)
    contrato_actual_changed = Signal(object)
    status_message = Signal(str)
    expediente_adjuntado = Signal(str)
    operacion_finalizada = Signal(str)  # Señal agregada para compatibilidad con la vista

    @inject
    def __init__(
        self,
        administrativo_service: AdministrativoService = Provide["Container.administrativo_service"],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self._administrativo_service = administrativo_service
        self._contrato_actual_id = None

    @Slot()
    def cargar_datos_iniciales(self):
        """Carga los datos necesarios para poblar la vista inicialmente."""
        try:
            contratos_dto = self._administrativo_service.listar_contratos()
            self.contratos_changed.emit(contratos_dto)

            proveedores_dto = self._administrativo_service.listar_proveedores()
            self.proveedores_changed.emit(proveedores_dto)
        except Exception as e:
            self.status_message.emit(f"Error al cargar datos: {e}")

    @Slot(int)
    def seleccionar_contrato(self, contrato_id: int):
        """Carga los detalles completos de un contrato para su edición."""
        self._contrato_actual_id = contrato_id
        try:
            contrato_dto = self._administrativo_service.obtener_contrato_por_id(contrato_id)
            if contrato_dto:
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
            expediente_path="",
            fecha_inicio=QDate.currentDate().toPython(),
            fecha_fin=QDate.currentDate().addYears(1).toPython(),
            proveedor_id=0,
            articulos=[]
        )
        self.contrato_actual_changed.emit(nuevo_contrato)

    @Slot(dict)
    def guardar_contrato_actual(self, contrato_data: Dict[str, Any]):
        """Recibe los datos del formulario y los persiste a través del servicio."""
        try:
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
            
            self._administrativo_service.crear_o_actualizar_contrato(contrato_dto)
            self.status_message.emit("Contrato guardado con éxito.")
            self.cargar_datos_iniciales()
        except Exception as e:
            self.status_message.emit(f"Error al guardar el contrato: {e}")

    @Slot(QWidget)
    def adjuntar_expediente(self, parent_widget: QWidget):
        """Abre un diálogo para seleccionar un archivo y delega su guardado al servicio."""
        if self._contrato_actual_id is None:
            self.status_message.emit("Guarde el contrato antes de adjuntar un expediente.")
            return

        ruta_origen, _ = QFileDialog.getOpenFileName(parent_widget, "Seleccionar Expediente", "", "Documentos PDF (*.pdf);;Todos los archivos (*)")
        
        if ruta_origen:
            try:
                ruta_relativa = self._administrativo_service.guardar_archivo_expediente(
                    self._contrato_actual_id, ruta_origen
                )
                self.expediente_adjuntado.emit(ruta_relativa)
                self.status_message.emit(f"Expediente adjuntado.")
            except Exception as e:
                self.status_message.emit(f"Error al adjuntar archivo: {e}")

    @Slot(str)
    def abrir_expediente(self, ruta_relativa: str):
        """Delega la apertura del archivo de expediente al servicio."""
        try:
            self._administrativo_service.abrir_archivo_expediente(ruta_relativa)
        except Exception as e:
            self.status_message.emit(f"No se pudo abrir el archivo: {e}")
