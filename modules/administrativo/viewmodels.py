# sigvcf/modules/administrativo/viewmodels.py
import os
import shutil
import webbrowser
from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot, QDate
from PySide6.QtWidgets import QFileDialog, QWidget
from typing import List, Dict, Any

from containers import Container
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
    expediente_adjuntado = Signal(str) # Nueva señal

    @inject
    def __init__(
        self,
        admin_service: AdministrativoService = Provide[Container.administrativo_service],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self._admin_service = admin_service
        self._contrato_actual_id = None

    @Slot()
    def cargar_datos_iniciales(self):
        """Carga los datos necesarios para poblar la vista inicialmente."""
        try:
            with self._admin_service.uow:
                contratos = self._admin_service.uow.contratos.list()
                contratos_dto = [ContratoDTO.from_orm(c) for c in contratos]
                self.contratos_changed.emit(contratos_dto)

                # Asumiendo que el servicio puede listar proveedores
                proveedores = [p for p in self._admin_service.uow.proveedores.list()]
                proveedores_dto = [ProveedorDTO(id=p.id, razon_social=p.razon_social, rfc=p.rfc, email_contacto=p.email_contacto) for p in proveedores]
                self.proveedores_changed.emit(proveedores_dto)
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
            
            self._admin_service.crear_o_actualizar_contrato(contrato_dto)
            self.status_message.emit("Contrato guardado con éxito.")
            self.cargar_datos_iniciales()
        except Exception as e:
            self.status_message.emit(f"Error al guardar el contrato: {e}")

    @Slot(QWidget)
    def adjuntar_expediente(self, parent_widget: QWidget):
        """Abre un diálogo para seleccionar un archivo y lo copia a la carpeta de datos."""
        if self._contrato_actual_id is None:
            self.status_message.emit("Guarde el contrato antes de adjuntar un expediente.")
            return

        ruta_origen, _ = QFileDialog.getOpenFileName(parent_widget, "Seleccionar Expediente", "", "Documentos PDF (*.pdf);;Todos los archivos (*)")
        
        if ruta_origen:
            try:
                nombre_original = os.path.basename(ruta_origen)
                nombre_destino = f"contrato_{self._contrato_actual_id}_{nombre_original}"
                ruta_destino_relativa = os.path.join("expedientes_data", nombre_destino)
                
                # Crear directorio si no existe
                os.makedirs("expedientes_data", exist_ok=True)
                
                shutil.copy(ruta_origen, ruta_destino_relativa)
                self.expediente_adjuntado.emit(ruta_destino_relativa)
                self.status_message.emit(f"Expediente '{nombre_original}' adjuntado.")
            except Exception as e:
                self.status_message.emit(f"Error al adjuntar archivo: {e}")

    @Slot(str)
    def abrir_expediente(self, ruta_relativa: str):
        """Abre el archivo del expediente con el programa predeterminado del sistema."""
        if not ruta_relativa or not ruta_relativa.strip():
            self.status_message.emit("No hay ningún expediente adjunto para este contrato.")
            return
        
        try:
            ruta_absoluta = os.path.realpath(ruta_relativa)
            if os.path.exists(ruta_absoluta):
                webbrowser.open(f"file://{ruta_absoluta}")
            else:
                self.status_message.emit(f"Error: No se encontró el archivo en la ruta '{ruta_absoluta}'.")
        except Exception as e:
            self.status_message.emit(f"No se pudo abrir el archivo: {e}")