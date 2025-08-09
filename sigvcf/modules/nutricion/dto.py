# sigvcf/modules/nutricion/dto.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict
from datetime import date, datetime

class ArticuloContratoSimpleDTO(BaseModel):
    """
    DTO simplificado para mostrar información básica de un artículo de contrato.
    Útil para listas desplegables en la UI.
    """
    id: int
    clave_articulo: str
    descripcion: str
    unidad_medida: str

    model_config = ConfigDict(from_attributes=True)

class ProgramacionMensualDTO(BaseModel):
    """
    DTO para crear o actualizar una programación mensual de insumos.
    """
    id: Optional[int] = None
    usuario_id: int
    articulo_contrato_id: int
    mes_anho: date  # Representa el mes/año, se recomienda usar el día 1 del mes.
    cantidades_por_dia: Dict[int, int] # Ej: {1: 100, 2: 150, ...} (día: cantidad)

    model_config = ConfigDict(from_attributes=True)

class SalidaRequerimientoDTO(BaseModel):
    """
    DTO para representar un requerimiento de salida consolidado.
    """
    id: int
    qr_id: str
    usuario_solicitante_id: int
    fecha_generacion: datetime
    estado: str

    model_config = ConfigDict(from_attributes=True)