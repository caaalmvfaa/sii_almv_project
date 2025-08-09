# sigvcf/modules/financiero/services.py
import datetime
from sigvcf.infrastructure.persistence.unit_of_work import IUnitOfWork
from sigvcf.modules.financiero.dto import RegistroContableDTO, RegistroContableCreateDTO
from sigvcf.core.domain.models import RegistroContable

class FinancieroService:
    """
    Servicio de aplicación para el módulo de Recursos Financieros.
    Orquesta la verificación de expedientes y la contabilidad gubernamental.
    """
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def verificar_expediente(self, entrada_id: int) -> None:
        """
        Marca un expediente de entrada como verificado.
        En este modelo, la verificación es un paso de proceso que habilita la
        generación de la póliza. Cambiamos el estado de la orden de compra
        asociada para reflejar este avance.
        """
        with self.uow:
            entrada = self.uow.entradas_bodega.get(entrada_id)
            if not entrada:
                raise ValueError(f"Entrada de bodega con id {entrada_id} no encontrada.")
            
            orden = entrada.orden_de_compra
            if orden.estado != 'RECIBIDA':
                raise ValueError(f"La orden de compra asociada {orden.id} no está en estado 'RECIBida'.")

            orden.estado = 'VERIFICADO'
            self.uow.commit()
            # En un sistema real, se podría registrar un log de auditoría de esta acción.

    def generar_poliza_contable(self, entrada_id: int, contador_id: int) -> RegistroContableDTO:
        """
        Genera la póliza contable (RegistroContable) para una entrada de bodega
        que ya ha sido verificada.
        """
        with self.uow:
            entrada = self.uow.entradas_bodega.get(entrada_id)
            if not entrada:
                raise ValueError(f"Entrada de bodega con id {entrada_id} no encontrada.")
            
            if entrada.orden_de_compra.estado != 'VERIFICADO':
                raise ValueError(f"El expediente de la entrada {entrada_id} aún no ha sido verificado.")

            if entrada.registro_contable:
                raise ValueError(f"La entrada {entrada_id} ya tiene una póliza contable asociada.")

            # --- Simulación del Motor de Contabilidad Gubernamental ---
            # En un sistema real, esta lógica sería compleja, consultando catálogos
            # de cuentas y aplicando reglas de la LGCG (Ley General de Contabilidad Gubernamental).
            asiento_contable = (
                f"POLIZA-DEVENGO-{datetime.date.today().year}-"
                f"CARGO:6151-Inventario/{entrada.folio_rb};"
                f"ABONO:2112-Cuentas por Pagar a Corto Plazo/{entrada.orden_de_compra.proveedor.rfc}"
            )
            # --- Fin de la simulación ---

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
        La Jefatura aprueba la póliza, liberando la factura para pago.
        Esto se refleja cambiando el estado de la orden de compra a 'PAGO_EN_TRAMITE'.
        """
        with self.uow:
            registro = self.uow.registros_contables.get(registro_contable_id)
            if not registro:
                raise ValueError(f"Registro contable con id {registro_contable_id} no encontrado.")

            orden = registro.entrada_bodega.orden_de_compra
            if orden.estado != 'VERIFICADO':
                 raise ValueError(f"La póliza no puede ser aprobada si la orden no está 'VERIFICADA'. Estado actual: {orden.estado}")

            orden.estado = 'PAGO_EN_TRAMITE'
            self.uow.commit()