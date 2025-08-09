# sigvcf/modules/juridico/dto.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

class ReporteIncumplimientoCreateDTO(BaseModel):
    """
    DTO para registrar un nuevo reporte de incumplimiento.
    """
    contrato_id: int
    tipo: str  # Ej: 'CALIDAD', 'ATRASO'
    estado: str  # Ej: 'PENDIENTE', 'EN_ANALISIS'
    descripcion: str

class ReporteIncumplimientoDTO(ReporteIncumplimientoCreateDTO):
    """
    DTO completo para representar un reporte de incumplimiento.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)

class PenalizacionDTO(BaseModel):
    """
    DTO para devolver el resultado del cálculo de una penalización.
    """
    orden_id: int
    dias_atraso: int
    monto_penalizacion: float
    calculo_detalle: str