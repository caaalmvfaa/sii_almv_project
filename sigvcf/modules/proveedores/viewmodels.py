from dependency_injector.wiring import inject, Provide
from PySide6.QtCore import QObject, Signal, Slot

 # Eliminado import directo de Container para evitar ciclo
from sigvcf.modules.proveedores.services import ProveedorService
from sigvcf.modules.proveedores.dto import EstadoEntregaDTO

class ProveedorViewModel(QObject):
    """
    ViewModel para el portal de Proveedores.
    Maneja la lógica de la UI para la consulta de órdenes, carga de facturas y seguimiento.
    """
    # --- Señales (Salidas hacia la Vista) ---
    ordenes_cargadas = Signal(list)
    estado_entrega_obtenido = Signal(object) # Emite EstadoEntregaDTO o None
    exito = Signal(str)
    error = Signal(str)

    @inject
    def __init__(
        self,
        proveedor_service: ProveedorService = Provide["Container.proveedor_service"],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.proveedor_service = proveedor_service

    # --- Slots (Entradas desde la Vista) ---

    @Slot(int)
    def cargar_ordenes_pendientes(self, proveedor_id: int):
        """
        Carga las órdenes de compra pendientes para un proveedor específico.
        """
        if proveedor_id <= 0:
            self.error.emit("ID de proveedor no válido.")
            return
        try:
            ordenes = self.proveedor_service.consultar_ordenes_pendientes(proveedor_id)
            self.ordenes_cargadas.emit(ordenes)
        except Exception as e:
            self.error.emit(f"Error al cargar órdenes: {e}")

    @Slot(int, int, str)
    def subir_factura_xml(self, orden_id: int, proveedor_id: int, contenido_xml: str):
        """
        Intenta subir el contenido de una factura XML para una orden de compra.
        """
        if orden_id <= 0 or not contenido_xml.strip():
            self.error.emit("Debe proporcionar un ID de orden y contenido XML.")
            return
        try:
            self.proveedor_service.cargar_factura_xml(orden_id, proveedor_id, contenido_xml)
            self.exito.emit(f"Factura para la orden {orden_id} cargada con éxito. El estado ha sido actualizado.")
            # Recargar la lista de órdenes para reflejar el cambio de estado
            self.cargar_ordenes_pendientes(proveedor_id)
        except Exception as e:
            self.error.emit(f"Error al subir la factura: {e}")

    @Slot(str, int)
    def rastrear_entrega(self, folio_rb: str, proveedor_id: int):
        """
        Consulta el estado de una entrega utilizando su Folio R.B.
        """
        if not folio_rb.strip():
            self.error.emit("Debe proporcionar un Folio R.B. para rastrear.")
            return
        try:
            estado = self.proveedor_service.consultar_estado_entrega(folio_rb, proveedor_id)
            self.estado_entrega_obtenido.emit(estado)
        except Exception as e:
            self.error.emit(f"Error al rastrear la entrega: {e}")
            self.estado_entrega_obtenido.emit(None) # Limpiar la vista en caso de error