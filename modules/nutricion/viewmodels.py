# sigvcf/modules/almacen/viewmodels.py
from PySide6.QtCore import QObject, Signal, Slot
from dependency_injector.wiring import inject, Provide
from typing import List, Dict

from sigvcf.containers import Container
from sigvcf.modules.almacen.services import AlmacenService
from sigvcf.modules.almacen.dto import (
    OrdenCompraCreateDTO,
    EntradaBodegaCreateDTO,
    StockStatusDTO,
    EntradaBodegaDTO
)

class AlmacenViewModel(QObject):
    """
    ViewModel para el módulo de Almacén.
    Gestiona la lógica de la UI para el control de inventario, entradas y salidas.
    """
    # --- Señales (Salidas hacia la Vista) ---
    stock_actualizado = Signal(list)
    entrada_registrada = Signal(object)
    despacho_completado = Signal(str)
    status_message = Signal(str)

    @inject
    def __init__(
        self,
        almacen_service: AlmacenService = Provide[Container.almacen_service],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.almacen_service = almacen_service

    @Slot()
    def cargar_estado_stock(self):
        """
        Solicita al servicio el estado actual del stock y lo emite.
        """
        try:
            stock_list = self.almacen_service.obtener_estado_stock()
            self.stock_actualizado.emit(stock_list)
        except Exception as e:
            self.status_message.emit(f"Error al cargar el stock: {e}")

    @Slot(list)
    def generar_propuestas_de_compra(self, propuestas_data: List[Dict]):
        """
        Recibe una lista de propuestas de compra desde la UI, las procesa
        y notifica el resultado.
        """
        try:
            propuestas_dto = [OrdenCompraCreateDTO(**data) for data in propuestas_data]
            ordenes_creadas = self.almacen_service.generar_propuesta_aprovisionamiento(propuestas_dto)
            self.status_message.emit(f"Se han generado {len(ordenes_creadas)} órdenes de compra en estado 'BORRADOR'.")
        except Exception as e:
            self.status_message.emit(f"Error al generar órdenes de compra: {e}")

    @Slot(dict)
    def registrar_entrada_bodega(self, entrada_data: Dict):
        """
        Recibe los datos de una nueva entrada de bodega y la registra.
        """
        try:
            entrada_dto = EntradaBodegaCreateDTO(**entrada_data)
            nueva_entrada = self.almacen_service.registrar_entrada_bodega(entrada_dto)
            self.entrada_registrada.emit(nueva_entrada)
            self.status_message.emit(f"Entrada registrada con éxito. Folio R.B.: {nueva_entrada.folio_rb}")
        except Exception as e:
            self.status_message.emit(f"Error al registrar la entrada: {e}")

    @Slot(str)
    def despachar_requerimiento_por_qr(self, qr_id: str):
        """
        Intenta despachar un requerimiento usando su código QR.
        """
        if not qr_id or not qr_id.strip():
            self.status_message.emit("El código QR no puede estar vacío.")
            return
        try:
            self.almacen_service.despachar_requerimiento(qr_id)
            self.despacho_completado.emit(f"Requerimiento '{qr_id}' despachado con éxito.")
        except Exception as e:
            self.status_message.emit(f"Error en el despacho: {e}")