# sigvcf/modules/administrativo/dto.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date

class ArticuloContratoDTO(BaseModel):
    id: Optional[int] = None
    clave_articulo: str
    descripcion: str
    unidad_medida: str
    precio_unitario: float
    cant_maxima: int
    clasificacion: str

    model_config = ConfigDict(from_attributes=True)

class ContratoDTO(BaseModel):
    id: Optional[int] = None
    codigo_licitacion: str
    expediente_path: Optional[str] = None
    fecha_inicio: date
    fecha_fin: date
    proveedor_id: int
    articulos: List[ArticuloContratoDTO] = []

    model_config = ConfigDict(from_attributes=True)

class OrdenCompraDTO(BaseModel):
    id: int
    contrato_id: int
    fecha_entrega_programada: date
    estado: str

    model_config = ConfigDict(from_attributes=True)