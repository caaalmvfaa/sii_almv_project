from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict

 # Import corregido: Container está en la raíz del proyecto
 # Eliminado import directo de Container para evitar ciclo
from sigvcf.modules.almacen.services import AlmacenService
from sigvcf.modules.almacen.dto import EntradaBodegaCreateDTO

class AlmacenViewModel(QObject):
    """
    ViewModel para el módulo de Almacén.
    Gestiona la lógica de la UI para el control de inventario, entradas y salidas.
    """
    # --- Señales (Salidas hacia la Vista) ---
    stock_actualizado = Signal(list)
    entrada_registrada = Signal(object) # Emite EntradaBodegaDTO
    exito = Signal(str)
    error = Signal(str)

    @inject
    def __init__(
        self,
        almacen_service: AlmacenService = Provide["Container.almacen_service"],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.almacen_service = almacen_service

    # --- Slots (Entradas desde la Vista) ---

    @Slot()
    def actualizar_stock(self):
        """
        Solicita al servicio el estado actual del stock y lo emite.
        """
        try:
            stock_list = self.almacen_service.obtener_estado_stock()
            self.stock_actualizado.emit(stock_list)
        except Exception as e:
            self.error.emit(f"Error al cargar el stock: {e}")

    @Slot(dict)
    def registrar_nueva_entrada(self, datos_entrada: Dict):
        """
        Recibe los datos de una nueva entrada de bodega y la registra.
        """
        try:
            if not all(k in datos_entrada for k in ["orden_compra_id", "factura_xml_path", "recepcionista_id"]):
                raise ValueError("Faltan datos para registrar la entrada.")
            
            dto = EntradaBodegaCreateDTO(**datos_entrada)
            nueva_entrada = self.almacen_service.registrar_entrada_bodega(dto)
            self.entrada_registrada.emit(nueva_entrada)
            self.exito.emit("Entrada de bodega registrada con éxito.")
        except Exception as e:
            self.error.emit(f"Error al registrar la entrada: {e}")

    @Slot(str)
    def despachar_por_qr(self, qr_id: str):
        """
        Intenta despachar un requerimiento usando su código QR.
        """
        if not qr_id or not qr_id.strip():
            self.error.emit("El código QR no puede estar vacío.")
            return
        try:
            self.almacen_service.despachar_requerimiento(qr_id)
            self.exito.emit(f"Requerimiento '{qr_id}' despachado con éxito. El stock ha sido actualizado.")
            # Actualizar la vista de stock después de un despacho exitoso
            self.actualizar_stock()
        except Exception as e:
            self.error.emit(f"Error en el despacho: {e}")