### FILE: sigvcf/modules/proveedores/services.py

from typing import List
from sqlalchemy.orm import joinedload

from sigvcf.core.domain.models import OrdenDeCompra, Contrato
from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.proveedores.dto import OrdenCompraProveedorDTO, EstadoEntregaDTO

class ProveedorService:
    """
    Servicio de aplicación para el módulo de Proveedores.
    Ofrece una interfaz para que los proveedores interactúen con el sistema.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def consultar_ordenes_pendientes(self, proveedor_id: int) -> List[OrdenCompraProveedorDTO]:
        """
        Consulta las órdenes de compra que están aprobadas y pendientes de entrega
        para un proveedor específico.
        """
        with self.uow:
            proveedor = self.uow.proveedores.get(proveedor_id)
            if not proveedor:
                raise ValueError(f"Proveedor con id {proveedor_id} no encontrado.")

            estados_pendientes = ['APROBADA', 'FACTURA_CARGADA']

            # Consulta única y eficiente con JOIN explícito y carga eager de la relación
            # para evitar el problema N+1.
            ordenes = self.uow.session.query(OrdenDeCompra)\
                .join(Contrato, OrdenDeCompra.contrato_id == Contrato.id)\
                .filter(Contrato.proveedor_id == proveedor_id)\
                .filter(OrdenDeCompra.estado.in_(estados_pendientes))\
                .options(joinedload(OrdenDeCompra.contrato))\
                .all()

            ordenes_dto = [
                OrdenCompraProveedorDTO(
                    id=orden.id,
                    codigo_licitacion_contrato=orden.contrato.codigo_licitacion,
                    fecha_entrega_programada=orden.fecha_entrega_programada,
                    estado=orden.estado
                ) for orden in ordenes
            ]
            
            return ordenes_dto

    def cargar_factura_xml(self, orden_id: int, proveedor_id: int, xml_content: str) -> None:
        """
        Permite a un proveedor cargar el XML de una factura para una orden de compra.
        Valida la propiedad y el estado de la orden.
        En un sistema real, el xml_content se guardaría en un sistema de archivos
        y la ruta se asociaría a la orden. Aquí, simulamos el proceso cambiando el estado.
        """
        with self.uow:
            orden = self.uow.ordenes_de_compra.get(orden_id)
            if not orden:
                raise ValueError(f"Orden de compra con id {orden_id} no encontrada.")
            
            # Validar que la orden pertenece al proveedor que realiza la acción
            if orden.contrato.proveedor_id != proveedor_id:
                raise PermissionError("El proveedor no tiene permiso sobre esta orden de compra.")

            if orden.estado != 'APROBADA':
                raise ValueError(f"La factura solo puede cargarse para órdenes en estado 'APROBADA'. Estado actual: {orden.estado}")

            # --- Simulación de validación y guardado de XML ---
            if not xml_content.strip().startswith('<') or not xml_content.strip().endswith('>'):
                 raise ValueError("Contenido XML no válido.")
            # En un sistema real:
            # 1. Parsear el XML y validar su estructura (CFDI).
            # 2. Validar que los datos del XML coincidan con la orden de compra.
            # 3. Guardar el archivo en una ubicación segura (ej. S3, disco local).
            #    factura_path = file_storage.save(f"facturas/{orden_id}.xml", xml_content)
            # 4. Asociar 'factura_path' a la orden (requeriría un campo en el modelo).
            # --- Fin de la simulación ---

            # Cambiar el estado para indicar que la factura está lista para la recepción física
            orden.estado = 'FACTURA_CARGADA'
            self.uow.commit()

    def consultar_estado_entrega(self, folio_rb: str, proveedor_id: int) -> EstadoEntregaDTO:
        """
        Permite a un proveedor consultar el estado de una entrega específica
        usando el Folio de Recibo de Bodega (R.B.).
        """
        with self.uow:
            entradas = self.uow.entradas_bodega.find(folio_rb=folio_rb)
            if not entradas:
                raise ValueError(f"No se encontró ninguna entrega con el folio '{folio_rb}'.")
            
            entrada = entradas[0]
            
            # Validar que la entrega pertenece a una orden del proveedor
            if entrada.orden_de_compra.contrato.proveedor_id != proveedor_id:
                raise PermissionError("El proveedor no tiene permiso para consultar este folio.")

            return EstadoEntregaDTO(
                folio_rb=entrada.folio_rb,
                fecha_recepcion=entrada.fecha_recepcion,
                estado_orden_compra=entrada.orden_de_compra.estado
            )