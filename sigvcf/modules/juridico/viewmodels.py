from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict

 # Eliminado import directo de Container para evitar ciclo
from sigvcf.modules.juridico.services import JuridicoService
from sigvcf.modules.juridico.dto import ReporteIncumplimientoCreateDTO, PenalizacionDTO

class JuridicoViewModel(QObject):
    """
    ViewModel para el módulo Jurídico.
    Maneja la lógica de la UI para la gestión de incumplimientos y penalizaciones.
    """
    # --- Señales (Salidas hacia la Vista) ---
    reportes_cargados = Signal(list)
    penalizacion_calculada = Signal(object) # Emite un PenalizacionDTO
    exito = Signal(str)
    error = Signal(str)

    @inject
    def __init__(
        self,
        juridico_service: JuridicoService = Provide["Container.juridico_service"],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.juridico_service = juridico_service

    # --- Slots (Entradas desde la Vista) ---

    @Slot()
    def cargar_reportes_pendientes(self):
        """
        Carga la lista de incumplimientos que no están resueltos.
        """
        try:
            reportes = self.juridico_service.listar_incumplimientos_pendientes()
            self.reportes_cargados.emit(reportes)
        except Exception as e:
            self.error.emit(f"Error al cargar reportes: {e}")

    @Slot(int)
    def calcular_penalizacion(self, orden_id: int):
        """
        Solicita al servicio el cálculo de una penalización por atraso.
        """
        if orden_id <= 0:
            self.error.emit("Por favor, introduzca un ID de Orden de Compra válido.")
            return
        try:
            resultado = self.juridico_service.calcular_penalizacion_por_atraso(orden_id)
            self.penalizacion_calculada.emit(resultado)
        except Exception as e:
            self.error.emit(f"Error al calcular penalización: {e}")
            # Limpiar los resultados en la vista en caso de error
            self.penalizacion_calculada.emit(None)

    @Slot(dict)
    def registrar_incumplimiento(self, reporte_data: Dict):
        """
        Recibe los datos de un nuevo reporte desde la vista y lo registra.
        """
        try:
            reporte_dto = ReporteIncumplimientoCreateDTO(**reporte_data)
            self.juridico_service.registrar_incumplimiento(reporte_dto)
            self.exito.emit("Reporte de incumplimiento registrado con éxito.")
            # Recargar la lista para que se refleje el nuevo reporte
            self.cargar_reportes_pendientes()
        except Exception as e:
            self.error.emit(f"Error al registrar el reporte: {e}")