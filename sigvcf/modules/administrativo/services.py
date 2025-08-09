import os
import shutil
import webbrowser
from typing import List
from sqlalchemy.orm import joinedload

from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.administrativo.dto import ContratoDTO, OrdenCompraDTO
from sigvcf.modules.proveedores.dto import ProveedorDTO
from sigvcf.core.domain.models import Contrato, ArticuloContrato, OrdenDeCompra, Proveedor

class AdministrativoService:
    """
    Servicio de aplicación para el módulo Administrativo.
    Orquesta los casos de uso relacionados con la gestión de contratos y aprobación de compras.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def _map_dto_to_entity(self, dto: ContratoDTO, entity: Contrato):
        """
        Función de ayuda para mapear los datos de un ContratoDTO a una entidad Contrato.
        """
        entity.codigo_licitacion = dto.codigo_licitacion
        entity.expediente_path = dto.expediente_path
        entity.fecha_inicio = dto.fecha_inicio
        entity.fecha_fin = dto.fecha_fin
        entity.proveedor_id = dto.proveedor_id
        entity.articulos = [
            ArticuloContrato(**art.model_dump()) for art in dto.articulos
        ]

    def crear_o_actualizar_contrato(self, contrato_dto: ContratoDTO) -> ContratoDTO:
        """
        Crea un nuevo contrato o actualiza uno existente junto con sus artículos.
        """
        with self.uow:
            if not self.uow.proveedores.get(contrato_dto.proveedor_id):
                raise ValueError(f"Proveedor con id {contrato_dto.proveedor_id} no encontrado.")

            if contrato_dto.id:
                contrato = self.uow.contratos.get(contrato_dto.id)
                if not contrato:
                    raise ValueError(f"Contrato con id {contrato_dto.id} no encontrado para actualizar.")
                
                self.uow.session.query(ArticuloContrato).filter(
                    ArticuloContrato.contrato_id == contrato.id
                ).delete(synchronize_session=False)
            else:
                contrato = Contrato()
                self.uow.contratos.add(contrato)

            self._map_dto_to_entity(contrato_dto, contrato)
            self.uow.commit()
            return ContratoDTO.from_orm(contrato)

    def listar_contratos(self) -> List[ContratoDTO]:
        """Recupera una lista de todos los contratos con sus relaciones básicas."""
        with self.uow:
            contratos = self.uow.session.query(Contrato).options(
                joinedload(Contrato.proveedor)
            ).all()
            return [ContratoDTO.from_orm(c) for c in contratos]

    def obtener_contrato_por_id(self, contrato_id: int) -> ContratoDTO | None:
        """Obtiene un contrato específico por su ID, precargando sus artículos."""
        with self.uow:
            contrato = self.uow.session.query(Contrato).options(
                joinedload(Contrato.articulos),
                joinedload(Contrato.proveedor)
            ).filter(Contrato.id == contrato_id).one_or_none()
            return ContratoDTO.from_orm(contrato) if contrato else None

    def listar_proveedores(self) -> List[ProveedorDTO]:
        """Recupera una lista de todos los proveedores."""
        with self.uow:
            proveedores = self.uow.proveedores.list()
            return [ProveedorDTO.from_orm(p) for p in proveedores]

    def guardar_archivo_expediente(self, contrato_id: int, ruta_origen: str) -> str:
        """Copia un archivo de expediente a una carpeta gestionada y devuelve la ruta relativa."""
        if not os.path.exists(ruta_origen):
            raise FileNotFoundError(f"El archivo de origen no existe: {ruta_origen}")
        
        nombre_original = os.path.basename(ruta_origen)
        nombre_destino = f"contrato_{contrato_id}_{nombre_original}"
        ruta_destino_relativa = os.path.join("expedientes_data", nombre_destino)
        
        os.makedirs("expedientes_data", exist_ok=True)
        shutil.copy(ruta_origen, ruta_destino_relativa)
        
        return ruta_destino_relativa

    def abrir_archivo_expediente(self, ruta_relativa: str):
        """Abre un archivo de expediente usando el programa predeterminado del sistema."""
        if not ruta_relativa or not ruta_relativa.strip():
            raise ValueError("No hay ninguna ruta de expediente especificada.")
        
        ruta_absoluta = os.path.realpath(ruta_relativa)
        if not os.path.exists(ruta_absoluta):
            raise FileNotFoundError(f"No se encontró el archivo en la ruta '{ruta_absoluta}'.")
        
        webbrowser.open(f"file://{ruta_absoluta}")

    def aprobar_orden_de_compra(self, orden_id: int) -> None:
        """Aprueba una orden de compra que está en estado 'BORRADOR'."""
        with self.uow:
            orden = self.uow.ordenes_de_compra.get(orden_id)
            if not orden:
                raise ValueError(f"Orden de compra con id {orden_id} no encontrada.")
            if orden.estado != 'BORRADOR':
                raise ValueError(f"La orden {orden_id} no está en estado 'BORRADOR', sino '{orden.estado}'.")
            
            orden.estado = 'APROBADA'
            self.uow.commit()

    def listar_ordenes_pendientes_aprobacion(self) -> List[OrdenCompraDTO]:
        """Devuelve una lista de todas las órdenes de compra en estado 'BORRADOR'."""
        with self.uow:
            ordenes_pendientes = self.uow.ordenes_de_compra.find(estado='BORRADOR')
            return [OrdenCompraDTO.from_orm(o) for o in ordenes_pendientes]

