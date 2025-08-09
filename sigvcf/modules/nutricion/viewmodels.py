import logging
from PySide6.QtCore import QObject, Signal, Slot, QDate
from dependency_injector.wiring import inject, Provide
from typing import Dict, List

from sigvcf.containers import Container
from sigvcf.modules.nutricion.services import NutricionService
from sigvcf.modules.nutricion.dto import ProgramacionMensualDTO, ArticuloContratoSimpleDTO

logger = logging.getLogger(__name__)

class NutricionViewModel(QObject):
    articulos_cargados = Signal(list)
    requerimiento_generado = Signal(object)
    exito = Signal(str)
    error = Signal(str)

    @inject
    def __init__(
        self,
        nutricion_service: NutricionService = Provide[Container.nutricion_service],
        parent: QObject | None = None
    ):
        super().__init__(parent)
        self.nutricion_service = nutricion_service

    @Slot()
    def cargar_articulos_disponibles(self):
        """Carga DTOs de artículos disponibles llamando al servicio de nutrición."""
        logger.info("ViewModel: Cargando artículos disponibles para nutrición.")
        try:
            # La lógica de consulta y conversión a DTO se delega al servicio.
            articulos_dto = self.nutricion_service.obtener_articulos_disponibles()
            self.articulos_cargados.emit(articulos_dto)
        except Exception as e:
            msg = f"Error al cargar artículos: {e}"
            logger.error(f"ViewModel: {msg}", exc_info=True)
            self.error.emit(msg)

    @Slot(int, int)
    def validar_disponibilidad_para_mes(self, articulo_id: int, cantidad_total_mes: int):
        logger.info(f"ViewModel: Validando disponibilidad para artículo {articulo_id}, cantidad {cantidad_total_mes}.")
        try:
            if not self.nutricion_service.validar_disponibilidad_articulo(articulo_id, cantidad_total_mes):
                self.exito.emit(f"Advertencia: La cantidad total excede lo disponible en el contrato.")
        except Exception as e:
            logger.error("ViewModel: Error de validación.", exc_info=True)
            self.error.emit(f"Error de validación: {e}")
            
    @Slot(dict)
    def guardar_programacion(self, programacion_data: Dict):
        logger.info(f"ViewModel: Guardando programación: {programacion_data}")
        try:
            dto = ProgramacionMensualDTO(**programacion_data)
            self.nutricion_service.guardar_programacion_mensual(dto)
            self.exito.emit("Programación mensual guardada con éxito.")
        except Exception as e:
            msg = f"Error al guardar: {e}"
            logger.error(f"ViewModel: {msg}", exc_info=True)
            self.error.emit(msg)

    @Slot(object, int)
    def generar_requerimiento(self, fecha_mes: QDate, usuario_id: int):
        logger.info(f"ViewModel: Generando requerimiento para mes {fecha_mes.toString('yyyy-MM')}.")
        try:
            # Convierte QDate a datetime.date antes de pasarlo al servicio
            fecha_python = fecha_mes.toPython()
            dto = self.nutricion_service.generar_requerimiento_consolidado(fecha_python, usuario_id)
            self.requerimiento_generado.emit(dto)
            self.exito.emit("Requerimiento consolidado generado con éxito.")
        except Exception as e:
            msg = f"Error al generar requerimiento: {e}"
            logger.error(f"ViewModel: {msg}", exc_info=True)
            self.error.emit(msg)

