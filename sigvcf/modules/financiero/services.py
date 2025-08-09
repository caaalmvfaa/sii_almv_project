import datetime
from typing import List
from sqlalchemy.orm import joinedload
from sqlalchemy import select

from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.financiero.dto import RegistroContableDTO, ExpedienteEntradaDTO
from sigvcf.core.domain.models import RegistroContable, EntradaBodega, OrdenDeCompra, Contrato, Proveedor

class FinancieroService:
    """
    Servicio de aplicación para el módulo de Recursos Financieros.
    Orquesta la verificación de expedientes y la contabilidad gubernamental.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def obtener_expedientes_pendientes(self) -> List[ExpedienteEntradaDTO]:
        """
        Obtiene una lista de DTOs de expedientes pendientes de verificación,
        filtrando y precargando relaciones eficientemente en la base de datos.
        """
        with self.uow:
            stmt = (
                select(EntradaBodega)
                .join(EntradaBodega.orden_de_compra)
                .options(
                    joinedload(EntradaBodega.orden_de_compra)
                    .joinedload(OrdenDeCompra.contrato)
                    .joinedload(Contrato.proveedor)
                )
                .where(OrdenDeCompra.estado == 'RECIBIDA')
            )
            # .unique() es importante para desduplicar resultados cuando se usan joins.
            resultados = self.uow.session.execute(stmt).scalars().unique().all()
            return [ExpedienteEntradaDTO.from_orm(e) for e in resultados]

    def obtener_polizas_pendientes(self) -> List[RegistroContableDTO]:
        """
        Obtiene una lista de DTOs de pólizas pendientes de aprobación,
        filtrando y precargando relaciones eficientemente en la base de datos.
        """
        with self.uow:
            stmt = (
                select(RegistroContable)
                .join(RegistroContable.entrada_bodega)
                .join(EntradaBodega.orden_de_compra)
                .options(
                    joinedload(RegistroContable.entrada_bodega)
                    .joinedload(EntradaBodega.orden_de_compra)
                    .joinedload(OrdenDeCompra.proveedor)
                )
                .where(OrdenDeCompra.estado == 'VERIFICADO')
            )
            resultados = self.uow.session.execute(stmt).scalars().unique().all()
            return [RegistroContableDTO.from_orm(r) for r in resultados]

    def verificar_expediente(self, entrada_id: int) -> None:
        """
        Marca un expediente de entrada como verificado, precargando relaciones.
        """
        with self.uow:
            entrada = self.uow.session.query(EntradaBodega).options(
                joinedload(EntradaBodega.orden_de_compra)
            ).filter(EntradaBodega.id == entrada_id).one_or_none()

            if not entrada:
                raise ValueError(f"Entrada de bodega con id {entrada_id} no encontrada.")
            
            orden = entrada.orden_de_compra
            if orden.estado != 'RECIBIDA':
                raise ValueError(f"La orden de compra asociada {orden.id} no está en estado 'RECIBida'.")

            orden.estado = 'VERIFICADO'
            self.uow.commit()

    def generar_poliza_contable(self, entrada_id: int, contador_id: int) -> RegistroContableDTO:
        """
        Genera la póliza contable para una entrada de bodega verificada, precargando relaciones.
        """
        with self.uow:
            entrada = self.uow.session.query(EntradaBodega).options(
                joinedload(EntradaBodega.orden_de_compra)
                .joinedload(OrdenDeCompra.proveedor)
            ).filter(EntradaBodega.id == entrada_id).one_or_none()

            if not entrada:
                raise ValueError(f"Entrada de bodega con id {entrada_id} no encontrada.")
            
            if entrada.orden_de_compra.estado != 'VERIFICADO':
                raise ValueError(f"El expediente de la entrada {entrada_id} aún no ha sido verificado.")

            if entrada.registro_contable:
                raise ValueError(f"La entrada {entrada_id} ya tiene una póliza contable asociada.")

            asiento_contable = (
                f"POLIZA-DEVENGO-{datetime.date.today().year}-"
                f"CARGO:6151-Inventario/{entrada.folio_rb};"
                f"ABONO:2112-Cuentas por Pagar a Corto Plazo/{entrada.orden_de_compra.proveedor.rfc}"
            )

            nuevo_registro = RegistroContable(
                entrada_bodega_id=entrada_id,
                asiento_contable=asiento_contable,
                contador_id=contador_id,
                fecha_contabilizacion=datetime.datetime.utcnow()
            )
            
            self.uow.registros_contables.add(nuevo_registro)
            self.uow.commit()

            return RegistroContableDTO.from_orm(nuevo_registro)

    def aprobar_poliza(self, registro_contable_id: int) -> None:
        """
        Aprueba la póliza, liberando la factura para pago, precargando relaciones.
        """
        with self.uow:
            registro = self.uow.session.query(RegistroContable).options(
                joinedload(RegistroContable.entrada_bodega)
                .joinedload(EntradaBodega.orden_de_compra)
            ).filter(RegistroContable.id == registro_contable_id).one_or_none()

            if not registro:
                raise ValueError(f"Registro contable con id {registro_contable_id} no encontrado.")

            orden = registro.entrada_bodega.orden_de_compra
            if orden.estado != 'VERIFICADO':
                 raise ValueError(f"La póliza no puede ser aprobada si la orden no está 'VERIFICADA'. Estado actual: {orden.estado}")

            orden.estado = 'PAGO_EN_TRAMITE'
            self.uow.commit()
