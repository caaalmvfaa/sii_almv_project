import uuid
import datetime
from typing import List
from sqlalchemy import select, func

from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.nutricion.dto import ProgramacionMensualDTO, SalidaRequerimientoDTO, ArticuloContratoSimpleDTO
from sigvcf.core.domain.models import ProgramacionMensual, SalidaRequerimiento, ArticuloContrato

class NutricionService:
    """
    Servicio de aplicación para el módulo de Nutrición.
    Orquesta la planificación de necesidades y la generación de requerimientos.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def obtener_articulos_disponibles(self) -> List[ArticuloContratoSimpleDTO]:
        """
        Obtiene una lista de DTOs de todos los artículos de contrato disponibles.
        """
        with self.uow:
            articulos = self.uow.articulos_contrato.list()
            return [ArticuloContratoSimpleDTO.from_orm(a) for a in articulos]

    def guardar_programacion_mensual(self, programacion_dto: ProgramacionMensualDTO) -> ProgramacionMensualDTO:
        """
        Guarda (crea o actualiza) la programación de un artículo para un mes específico.
        """
        with self.uow:
            # Buscar eficientemente si ya existe una programación para este artículo y mes
            programacion = self.uow.programaciones_mensuales.find_one_by(
                articulo_contrato_id=programacion_dto.articulo_contrato_id,
                mes_anho=programacion_dto.mes_anho
            )

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
        Valida si la cantidad solicitada para un artículo en un mes es viable
        contra el contrato, calculando el total programado eficientemente.
        """
        with self.uow:
            articulo = self.uow.articulos_contrato.get(articulo_id)
            if not articulo:
                raise ValueError(f"Artículo con id {articulo_id} no encontrado.")

            # 1. Calcular el total ya programado de forma eficiente.
            # Se selecciona solo la columna necesaria en lugar de objetos completos.
            # La suma se realiza en Python ya que sumar valores de un campo JSON
            # no es una operación estándar de SQL y varía por dialecto.
            stmt = select(ProgramacionMensual.cantidades_por_dia).where(
                ProgramacionMensual.articulo_contrato_id == articulo_id
            )
            lista_de_cantidades_por_dia = self.uow.session.execute(stmt).scalars().all()
            
            total_ya_programado = sum(
                sum(cantidades.values()) for cantidades in lista_de_cantidades_por_dia if cantidades
            )

            # 2. Calcular el disponible real.
            # Es el máximo del contrato menos lo ya consumido (despachado) y menos
            # lo que está en otras programaciones pendientes.
            disponible_real = articulo.cant_maxima - articulo.cant_consumida - total_ya_programado
            
            # 3. La validación es si la nueva cantidad para este mes cabe en lo que queda.
            return cantidad_total_mes <= disponible_real
