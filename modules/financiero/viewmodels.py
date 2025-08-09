# sigvcf/modules/financiero/viewmodels.py
from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot

from sigvcf.containers import Container
from sigvcf.modules.financiero.services import FinancieroService
from sigvcf.modules.financiero.dto import RegistroContableDTO
from sigvcf.core.domain.models import EntradaBodega, RegistroContable

class FinancieroViewModel(QObject):
    """
    ViewModel para el módulo de Recursos Financieros.
    Orquesta el flujo de trabajo de verificación y aprobación contable.
    """
    # --- Señales (Salidas hacia la Vista) ---
    expedientes_pendientes_cargados = Signal(list)
    polizas_pendientes_cargadas = Signal(list)
    operacion_finalizada = Signal(str)

    @inject
    def __init__(
        self,
        financiero_service: FinancieroService = Provide[Container.financiero_service],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.financiero_service = financiero_service

    # --- Slots (Entradas desde la Vista) ---

    @Slot()
    def cargar_bandejas(self):
        """Carga los datos para ambas bandejas (Contador y Jefatura)."""
        self._cargar_expedientes_pendientes()
        self._cargar_polizas_pendientes()

    def _cargar_expedientes_pendientes(self):
        """Carga las entradas de bodega que están en estado 'RECIBIDA'."""
        try:
            with self.financiero_service.uow:
                todas_las_entradas = self.financiero_service.uow.entradas_bodega.list()
                expedientes_pendientes = [
                    e for e in todas_las_entradas if e.orden_de_compra.estado == 'RECIBIDA'
                ]
                self.expedientes_pendientes_cargados.emit(expedientes_pendientes)
        except Exception as e:
            self.operacion_finalizada.emit(f"Error al cargar expedientes: {e}")

    def _cargar_polizas_pendientes(self):
        """Carga los registros contables cuya orden asociada está 'VERIFICADA'."""
        try:
            with self.financiero_service.uow:
                todos_los_registros = self.financiero_service.uow.registros_contables.list()
                polizas_pendientes = [
                    r for r in todos_los_registros if r.entrada_bodega.orden_de_compra.estado == 'VERIFICADO'
                ]
                # Convertir a DTO para la vista
                polizas_dto = [RegistroContableDTO.from_orm(p) for p in polizas_pendientes]
                self.polizas_pendientes_cargadas.emit(polizas_dto)
        except Exception as e:
            self.operacion_finalizada.emit(f"Error al cargar pólizas: {e}")

    @Slot(int)
    def verificar_expediente_seleccionado(self, entrada_id: int):
        """Invoca al servicio para marcar un expediente como verificado."""
        try:
            self.financiero_service.verificar_expediente(entrada_id)
            self.operacion_finalizada.emit(f"Expediente de entrada {entrada_id} verificado con éxito.")
            self.cargar_bandejas() # Recargar ambas listas
        except Exception as e:
            self.operacion_finalizada.emit(f"Error al verificar expediente: {e}")

    @Slot(int, int)
    def generar_poliza(self, entrada_id: int, contador_id: int):
        """Invoca al servicio para generar una póliza contable."""
        try:
            self.financiero_service.generar_poliza_contable(entrada_id, contador_id)
            self.operacion_finalizada.emit(f"Póliza generada para la entrada {entrada_id}.")
            self.cargar_bandejas()
        except Exception as e:
            self.operacion_finalizada.emit(f"Error al generar la póliza: {e}")

    @Slot(int)
    def aprobar_poliza_seleccionada(self, poliza_id: int):
        """Invoca al servicio para aprobar una póliza, liberándola para pago."""
        try:
            self.financiero_service.aprobar_poliza(poliza_id)
            self.operacion_finalizada.emit(f"Póliza {poliza_id} aprobada y liberada para pago.")
            self.cargar_bandejas()
        except Exception as e:
            self.operacion_finalizada.emit(f"Error al aprobar la póliza: {e}")