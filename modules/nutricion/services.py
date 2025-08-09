# sigvcf/modules/nutricion/services.py
import uuid
import datetime
from typing import List
from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.nutricion.dto import ProgramacionMensualDTO, SalidaRequerimientoDTO
from sigvcf.core.domain.models import ProgramacionMensual, SalidaRequerimiento

class NutricionService:
    """
    Servicio de aplicación para el módulo de Nutrición.
    Orquesta la planificación de necesidades y la generación de requerimientos.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def guardar_programacion_mensual(self, programacion_dto: ProgramacionMensualDTO) -> ProgramacionMensualDTO:
        """
        Guarda (crea o actualiza) la programación de un artículo para un mes específico.
        """
        with self.uow:
            # Buscar si ya existe una programación para este artículo y mes
            programacion_existente_list = self.uow.programaciones_mensuales.find(
                articulo_contrato_id=programacion_dto.articulo_contrato_id,
                mes_anho=programacion_dto.mes_anho
            )
            
            programacion = programacion_existente_list[0] if programacion_existente_list else None

            if programacion:
                # Actualizar la programación existente
                programacion.cantidades_por_dia = programacion_dto.cantidades_por_dia
                programacion.usuario_id = programacion_dto.usuario_id # Actualizar quién hizo el último cambio
            else:
                # Crear una nueva programación
                articulo = self.uow.articulos_contrato.get(programacion_dto.articulo_contrato_id)
                if not articulo:
                    raise ValueError(f"Artículo con id {programacion_dto.articulo_contrato_id} no encontrado.")
                
                programacion = ProgramacionMensual(
                    usuario_id=programacion_dto.usuario_id,
                    articulo_contrato_id=programacion_dto.articulo_contrato_id,
                    mes_anho=programacion_dto.mes_anho,
                    cantidades_por_dia=programacion_dto.cantidades_por_dia
                )
                self.uow.programaciones_mensuales.add(programacion)
            
            self.uow.commit()
            return ProgramacionMensualDTO.from_orm(programacion)

    def generar_requerimiento_consolidado(self, mes: datetime.date, usuario_id: int) -> SalidaRequerimientoDTO:
        """
        Consolida todas las programaciones de un mes y genera un único
        documento de SalidaRequerimiento con un QR.
        """
        with self.uow:
            # Validar que existan programaciones para ese mes
            programaciones_del_mes = self.uow.programaciones_mensuales.find(mes_anho=mes)
            if not programaciones_del_mes:
                raise ValueError(f"No hay programaciones para el mes {mes.strftime('%Y-%m')} para consolidar.")

            # Generar un QR ID único para este requerimiento consolidado
            qr_id = f"REQ-{mes.strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"

            nuevo_requerimiento = SalidaRequerimiento(
                qr_id=qr_id,
                usuario_solicitante_id=usuario_id,
                fecha_generacion=datetime.datetime.utcnow(),
                estado='PREVIA' # Estado inicial antes de ser despachado por almacén
            )
            
            self.uow.salidas_requerimiento.add(nuevo_requerimiento)
            self.uow.commit()

            return SalidaRequerimientoDTO.from_orm(nuevo_requerimiento)

    def validar_disponibilidad_articulo(self, articulo_id: int, cantidad_total_mes: int) -> bool:
        """
        Valida en tiempo real si la cantidad solicitada para un artículo en un mes
        excede el máximo del contrato.
        """
        with self.uow:
            articulo = self.uow.articulos_contrato.get(articulo_id)
            if not articulo:
                raise ValueError(f"Artículo con id {articulo_id} no encontrado.")
            
            # La validación es contra el total del contrato, no contra el stock actual.
            # El stock se descuenta al despachar, no al programar.
            # La lógica aquí es prevenir que la suma de lo ya consumido más lo que se está
            # programando ahora exceda el máximo permitido.
            # NOTA: Una lógica más compleja podría considerar otras programaciones no surtidas.
            # Por simplicidad, validamos contra el consumo ya efectuado.
            
            disponible = articulo.cant_maxima - articulo.cant_consumida
            
            return cantidad_total_mes <= disponible