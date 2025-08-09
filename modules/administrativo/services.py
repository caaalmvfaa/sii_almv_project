# sigvcf/modules/administrativo/services.py
from typing import List
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
                
                # Borrar artículos existentes para una actualización simple
                for art in list(contrato.articulos):
                    self.uow.session.delete(art)
            else:
                contrato = Contrato()
                self.uow.contratos.add(contrato)

            # Mapear DTO a entidad
            contrato.codigo_licitacion = contrato_dto.codigo_licitacion
            contrato.expediente_path = contrato_dto.expediente_path
            contrato.fecha_inicio = contrato_dto.fecha_inicio
            contrato.fecha_fin = contrato_dto.fecha_fin
            contrato.proveedor_id = contrato_dto.proveedor_id
            
            # Mapear artículos
            for art_dto in contrato_dto.articulos:
                contrato.articulos.append(ArticuloContrato(
                    clave_articulo=art_dto.clave_articulo,
                    descripcion=art_dto.descripcion,
                    unidad_medida=art_dto.unidad_medida,
                    precio_unitario=art_dto.precio_unitario,
                    cant_maxima=art_dto.cant_maxima,
                    clasificacion=art_dto.clasificacion
                ))

            self.uow.commit()
            
            return ContratoDTO.from_orm(contrato)

    def listar_proveedores(self) -> List[ProveedorDTO]:
        """
        Recupera una lista de todos los proveedores.
        """
        with self.uow:
            proveedores = self.uow.proveedores.list()
            return [ProveedorDTO.from_orm(p) for p in proveedores]

    def aprobar_orden_de_compra(self, orden_id: int) -> None:
        """
        Aprueba una orden de compra que está en estado 'BORRADOR'.
        """
        with self.uow:
            orden = self.uow.ordenes_de_compra.get(orden_id)
            if not orden:
                raise ValueError(f"Orden de compra con id {orden_id} no encontrada.")
            
            if orden.estado != 'BORRADOR':
                raise ValueError(f"La orden {orden_id} no está en estado 'BORRADOR', sino '{orden.estado}'.")
            
            orden.estado = 'APROBADA'
            
            # En un sistema real, aquí se dispararía un evento o se llamaría a un servicio de notificación.
            # Ejemplo: self.notification_service.notificar_aprobacion_a_proveedor(orden)
            
            self.uow.commit()

    def listar_ordenes_pendientes_aprobacion(self) -> List[OrdenCompraDTO]:
        """
        Devuelve una lista de todas las órdenes de compra en estado 'BORRADOR'.
        """
        with self.uow:
            ordenes_pendientes = self.uow.ordenes_de_compra.find(estado='BORRADOR')
            return [OrdenCompraDTO.from_orm(o) for o in ordenes_pendientes]