# sigvcf/modules/financiero/dto.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date

class ExpedienteEntradaDTO(BaseModel):
    """
    DTO que representa el paquete de información de una entrada de bodega
    para ser verificado por el área financiera.
    """
    entrada_id: int
    folio_rb: str
    fecha_recepcion: datetime
    factura_xml_path: str
    orden_compra_id: int
    codigo_licitacion_contrato: str
    proveedor_rfc: str

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class RegistroContableCreateDTO(BaseModel):
    """
    DTO para la creación de un nuevo registro contable (póliza).
    """
    entrada_bodega_id: int
    contador_id: int

class RegistroContableDTO(BaseModel):
    """
    DTO completo que representa un registro contable.
    """
    id: int
    entrada_bodega_id: int
    asiento_contable: str
    fecha_contabilizacion: datetime
    contador_id: int

    model_config = ConfigDict(from_attributes=True)