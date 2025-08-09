# sigvcf/modules/administrativo/dto.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date

class ArticuloContratoDTO(BaseModel):
    """
    DTO para la creación o actualización de un artículo dentro de un contrato.
    """
    id: Optional[int] = None
    clave_articulo: str
    descripcion: str
    unidad_medida: str
    precio_unitario: float
    cant_maxima: int
    clasificacion: str

    model_config = ConfigDict(from_attributes=True)

class ContratoDTO(BaseModel):
    """
    DTO para la gestión CRUD de contratos. Incluye sus artículos asociados.
    """
    id: Optional[int] = None
    codigo_licitacion: str
    expediente_path: Optional[str] = None
    fecha_inicio: date
    fecha_fin: date
    proveedor_id: int
    articulos: List[ArticuloContratoDTO] = []

    model_config = ConfigDict(from_attributes=True)

class OrdenCompraDTO(BaseModel):
    """
    DTO para visualizar órdenes de compra, especialmente las pendientes de aprobación.
    """
    id: int
    contrato_id: int
    fecha_entrega_programada: date
    estado: str

    model_config = ConfigDict(from_attributes=True)