# sigvcf/modules/almacen/dto.py
from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Optional, List
from datetime import date, datetime

# --- DTOs para Órdenes de Compra ---

class OrdenCompraCreateDTO(BaseModel):
    """DTO para crear una nueva orden de compra."""
    contrato_id: int
    fecha_entrega_programada: date

class OrdenCompraDTO(OrdenCompraCreateDTO):
    """DTO completo para representar una orden de compra."""
    id: int
    estado: str
    
    model_config = ConfigDict(from_attributes=True)

# --- DTOs para Entradas de Bodega ---

class EntradaBodegaCreateDTO(BaseModel):
    """DTO para registrar una nueva entrada de mercancía."""
    orden_compra_id: int
    factura_xml_path: str
    recepcionista_id: int

class EntradaBodegaDTO(EntradaBodegaCreateDTO):
    """DTO completo para representar una entrada de bodega."""
    id: int
    folio_rb: str
    fecha_recepcion: datetime

    model_config = ConfigDict(from_attributes=True)

# --- DTOs para Salidas de Requerimiento ---

class SalidaRequerimientoDTO(BaseModel):
    """DTO para representar una salida de requerimiento."""
    id: int
    qr_id: str
    usuario_solicitante_id: int
    fecha_generacion: datetime
    estado: str

    model_config = ConfigDict(from_attributes=True)

# --- DTO para Control de Inventario ---

class StockStatusDTO(BaseModel):
    """DTO para visualizar el estado del stock de un artículo."""
    clave_articulo: str
    descripcion: str
    cant_maxima: int
    cant_consumida: int

    @computed_field
    @property
    def stock_disponible(self) -> int:
        return self.cant_maxima - self.cant_consumida

    model_config = ConfigDict(from_attributes=True)