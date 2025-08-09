# sigvcf/modules/proveedores/dto.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime

class OrdenCompraProveedorDTO(BaseModel):
    """
    DTO para que el proveedor consulte sus órdenes de compra pendientes.
    Muestra la información esencial para planificar la entrega.
    """
    id: int
    codigo_licitacion_contrato: str
    fecha_entrega_programada: date
    estado: str

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class FacturaUploadDTO(BaseModel):
    """
    DTO para el proceso de carga de una factura XML por parte del proveedor.
    """
    orden_id: int
    # En un sistema real, el contenido se procesaría y guardaría,
    # aquí representamos el contenido como un string.
    xml_content: str

class EstadoEntregaDTO(BaseModel):
    """
    DTO para que el proveedor consulte el estado de una entrega ya realizada.
    """
    folio_rb: str
    fecha_recepcion: datetime
    estado_orden_compra: str
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)