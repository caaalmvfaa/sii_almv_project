import datetime
from typing import List
from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.almacen.dto import (
    OrdenCompraDTO,
    EntradaBodegaCreateDTO,
    EntradaBodegaDTO,
    StockStatusDTO,
    OrdenCompraCreateDTO
)
from sigvcf.core.domain.models import OrdenDeCompra, EntradaBodega

class AlmacenService:
    """
    Servicio de aplicación para el módulo de Almacén.
    Orquesta los casos de uso de aprovisionamiento, entradas y salidas.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def generar_propuesta_aprovisionamiento(self, propuestas: List[OrdenCompraCreateDTO]) -> List[OrdenCompraDTO]:
        """
        Crea nuevas órdenes de compra en estado 'BORRADOR' a partir de una lista de propuestas.
        Estas propuestas serían el resultado del análisis de la demanda consolidada.
        """
        ordenes_creadas = []
        with self.uow:
            for propuesta in propuestas:
                # Validar que el contrato existe
                contrato = self.uow.contratos.get(propuesta.contrato_id)
                if not contrato:
                    raise ValueError(f"Contrato con id {propuesta.contrato_id} no encontrado.")
                
                nueva_orden = OrdenDeCompra(
                    contrato_id=propuesta.contrato_id,
                    fecha_entrega_programada=propuesta.fecha_entrega_programada,
                    estado='BORRADOR' # Estado inicial para ser aprobado por el área administrativa
                )
                self.uow.ordenes_de_compra.add(nueva_orden)
                ordenes_creadas.append(nueva_orden)
            
            self.uow.commit()
            
            # Devolvemos los DTOs de las órdenes creadas
            return [OrdenCompraDTO.from_orm(oc) for oc in ordenes_creadas]

    def registrar_entrada_bodega(self, entrada_dto: EntradaBodegaCreateDTO) -> EntradaBodegaDTO:
        """
        Registra la recepción de mercancía, validando contra la orden de compra.
        Genera un Folio R.B. único.
        """
        with self.uow:
            orden_compra = self.uow.ordenes_de_compra.get(entrada_dto.orden_compra_id)
            if not orden_compra:
                raise ValueError(f"Orden de compra con id {entrada_dto.orden_compra_id} no encontrada.")
            if orden_compra.estado != 'APROBADA':
                raise ValueError(f"La orden de compra {orden_compra.id} no está en estado 'APROBADA'.")

            # Generar Folio R.B. (Recibo de Bodega)
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            folio_rb = f"RB-{timestamp}-{orden_compra.id}"

            nueva_entrada = EntradaBodega(
                folio_rb=folio_rb,
                orden_compra_id=entrada_dto.orden_compra_id,
                factura_xml_path=entrada_dto.factura_xml_path,
                recepcionista_id=entrada_dto.recepcionista_id,
                fecha_recepcion=datetime.datetime.utcnow()
            )
            
            # Cambiar estado de la orden de compra a 'RECIBIDA'
            orden_compra.estado = 'RECIBIDA'

            self.uow.entradas_bodega.add(nueva_entrada)
            self.uow.commit()
            
            return EntradaBodegaDTO.from_orm(nueva_entrada)

    def despachar_requerimiento(self, qr_id: str) -> None:
        """
        Procesa el despacho de un requerimiento escaneado por QR.
        Cambia el estado de 'PREVIA' a 'SURTIDA' y actualiza el stock consumido.
        """
        with self.uow:
            resultados = self.uow.salidas_requerimiento.find(qr_id=qr_id)
            if not resultados:
                raise ValueError(f"Requerimiento con QR ID '{qr_id}' no encontrado.")
            
            requerimiento = resultados[0]
            
            if requerimiento.estado != 'PREVIA':
                raise ValueError(f"El requerimiento '{qr_id}' no está en estado 'PREVIA' para ser despachado.")
            
            # --- Implementación de la lógica de inventario ---
            self._decrementar_stock_asociado(requerimiento)
            
            requerimiento.estado = 'SURTIDA'
            self.uow.commit()

    def _decrementar_stock_asociado(self, requerimiento):
        """
        Busca las programaciones mensuales asociadas al requerimiento y actualiza
        la cantidad consumida de cada artículo de contrato.
        """
        try:
            # El QR ID contiene el mes y año: "REQ-YYYYMM-..."
            parts = requerimiento.qr_id.split('-')
            year_month_str = parts[1]
            year = int(year_month_str[:4])
            month = int(year_month_str[4:])
            mes_requerimiento = datetime.date(year, month, 1)
        except (IndexError, ValueError):
            raise ValueError(f"Formato de QR ID '{requerimiento.qr_id}' inválido. No se pudo extraer el mes.")

        # Buscar todas las programaciones para ese mes
        programaciones_del_mes = self.uow.programaciones_mensuales.find(mes_anho=mes_requerimiento)

        if not programaciones_del_mes:
            # Podría ser un caso válido si se genera un requerimiento vacío, pero es bueno loggearlo.
            print(f"Advertencia: No se encontraron programaciones para el mes de {mes_requerimiento.strftime('%Y-%m')} al despachar el requerimiento {requerimiento.qr_id}")
            return

        for prog in programaciones_del_mes:
            cantidad_a_despachar = sum(prog.cantidades_por_dia.values())
            
            if cantidad_a_despachar > 0:
                articulo = self.uow.articulos_contrato.get(prog.articulo_contrato_id)
                if not articulo:
                    # Esto indica una inconsistencia de datos. Es importante registrarlo.
                    print(f"ERROR CRÍTICO: El artículo de contrato ID {prog.articulo_contrato_id} de una programación no fue encontrado.")
                    continue
                
                # Incrementar la cantidad consumida
                articulo.cant_consumida += cantidad_a_despachar


    def obtener_estado_stock(self) -> List[StockStatusDTO]:
        """
        Devuelve el estado actual del stock para todos los artículos de contrato.
        Esta información alimenta la visualización de inventario.
        """
        with self.uow:
            articulos = self.uow.articulos_contrato.list()
            return [StockStatusDTO.from_orm(art) for art in articulos]
