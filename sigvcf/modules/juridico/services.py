from typing import List
from sqlalchemy.orm import joinedload
from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.juridico.dto import ReporteIncumplimientoDTO, ReporteIncumplimientoCreateDTO, PenalizacionDTO
from sigvcf.core.domain.models import ReporteIncumplimiento, OrdenDeCompra

class JuridicoService:
    """
    Servicio de aplicación para el módulo Jurídico.
    Orquesta la gestión de incumplimientos contractuales y penalizaciones.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def registrar_incumplimiento(self, reporte_dto: ReporteIncumplimientoCreateDTO) -> ReporteIncumplimientoDTO:
        """
        Registra un nuevo reporte de incumplimiento en el sistema.
        """
        with self.uow:
            contrato = self.uow.contratos.get(reporte_dto.contrato_id)
            if not contrato:
                raise ValueError(f"Contrato con id {reporte_dto.contrato_id} no encontrado.")

            nuevo_reporte = ReporteIncumplimiento(
                contrato_id=reporte_dto.contrato_id,
                tipo=reporte_dto.tipo,
                estado=reporte_dto.estado,
                descripcion=reporte_dto.descripcion
            )
            self.uow.reportes_incumplimiento.add(nuevo_reporte)
            self.uow.commit()

            return ReporteIncumplimientoDTO.from_orm(nuevo_reporte)

    def calcular_penalizacion_por_atraso(self, orden_id: int) -> PenalizacionDTO:
        """
        Calcula la penalización por atraso para una orden de compra específica,
        precargando las relaciones necesarias para evitar N+1 queries.
        """
        with self.uow:
            orden = self.uow.session.query(OrdenDeCompra).options(
                joinedload(OrdenDeCompra.entrada_bodega)
            ).filter(OrdenDeCompra.id == orden_id).one_or_none()

            if not orden:
                raise ValueError(f"Orden de compra con id {orden_id} no encontrada.")
            
            if not orden.entrada_bodega:
                raise ValueError(f"La orden {orden_id} aún no ha sido recibida, no se puede calcular atraso.")

            fecha_programada = orden.fecha_entrega_programada
            fecha_real = orden.entrada_bodega.fecha_recepcion.date()

            if fecha_real <= fecha_programada:
                return PenalizacionDTO(
                    orden_id=orden_id,
                    dias_atraso=0,
                    monto_penalizacion=0.0,
                    calculo_detalle="La entrega se realizó a tiempo o antes de lo programado."
                )

            dias_atraso = (fecha_real - fecha_programada).days
            
            # Lógica de penalización simplificada: 150.0 unidades monetarias por día de atraso.
            # En un sistema real, se leerían las cláusulas del contrato.
            penalizacion_por_dia = 150.0
            monto_total = dias_atraso * penalizacion_por_dia

            return PenalizacionDTO(
                orden_id=orden_id,
                dias_atraso=dias_atraso,
                monto_penalizacion=monto_total,
                calculo_detalle=f"Cálculo: {dias_atraso} días de atraso * ${penalizacion_por_dia}/día."
            )

    def listar_incumplimientos_pendientes(self) -> List[ReporteIncumplimientoDTO]:
        """
        Devuelve una lista de todos los reportes de incumplimiento que no están 'RESUELTO',
        filtrando directamente en la base de datos para mayor eficiencia.
        """
        with self.uow:
            # Filtrar directamente en la base de datos en lugar de en memoria.
            # Esto es mucho más eficiente que self.uow.reportes_incumplimiento.list().
            reportes_pendientes = self.uow.session.query(ReporteIncumplimiento).filter(
                ReporteIncumplimiento.estado != 'RESUELTO'
            ).all()
            
            return [ReporteIncumplimientoDTO.from_orm(r) for r in reportes_pendientes]
