# sigvcf/modules/nutricion/views.py
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox,
    QDateEdit, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox,
    QHeaderView
)
from typing import List

from sigvcf.modules.nutricion.viewmodels import NutricionViewModel
from sigvcf.modules.nutricion.dto import ArticuloContratoSimpleDTO, SalidaRequerimientoDTO

class NutricionView(QWidget):
    """
    Vista para la planificación mensual de insumos del módulo de Nutrición.
    Permite a los usuarios programar cantidades diarias de artículos y generar
    requerimientos consolidados.
    """
    def __init__(self, view_model: NutricionViewModel, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setWindowTitle("Planificación de Nutrición")
        self._setup_ui()
        self._connect_signals()
        
        # Carga inicial de datos
        self.vm.cargar_articulos_disponibles()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Panel de Selección ---
        selection_group = QGroupBox("Selección de Artículo y Mes")
        selection_layout = QHBoxLayout(selection_group)
        
        self.articulo_combo = QComboBox()
        self.mes_anho_edit = QDateEdit(calendarPopup=True)
        self.mes_anho_edit.setDisplayFormat("MMMM yyyy")
        self.mes_anho_edit.setDate(QDate.currentDate())

        selection_layout.addWidget(QLabel("Artículo:"))
        selection_layout.addWidget(self.articulo_combo, 1)
        selection_layout.addWidget(QLabel("Mes de Programación:"))
        selection_layout.addWidget(self.mes_anho_edit, 1)
        main_layout.addWidget(selection_group)

        # --- Panel de Programación (Matriz) ---
        matrix_group = QGroupBox("Programación de Cantidades Diarias")
        matrix_layout = QVBoxLayout(matrix_group)
        
        self.programacion_table = QTableWidget()
        self.programacion_table.setRowCount(1)
        self.programacion_table.setColumnCount(31)
        self.programacion_table.setVerticalHeaderLabels(["Cantidad"])
        self.programacion_table.setHorizontalHeaderLabels([f"Día {i+1}" for i in range(31)])
        self.programacion_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        matrix_layout.addWidget(self.programacion_table)
        main_layout.addWidget(matrix_group)

        # --- Panel de Acciones ---
        actions_layout = QHBoxLayout()
        self.guardar_button = QPushButton("Guardar Programación")
        self.generar_req_button = QPushButton("Generar Requerimiento Consolidado")
        
        actions_layout.addStretch()
        actions_layout.addWidget(self.guardar_button)
        actions_layout.addWidget(self.generar_req_button)
        main_layout.addLayout(actions_layout)

    def _connect_signals(self):
        # Conexiones Vista -> ViewModel
        self.guardar_button.clicked.connect(self._on_guardar_clicked)
        self.generar_req_button.clicked.connect(self._on_generar_requerimiento_clicked)
        self.programacion_table.cellChanged.connect(self._on_cell_changed)

        # Conexiones ViewModel -> Vista
        self.vm.articulos_cargados.connect(self._update_articulos_combo)
        self.vm.programacion_guardada.connect(self._show_status_message)
        self.vm.requerimiento_generado.connect(self._show_requerimiento_info)

    # --- Slots de la Vista (Manejan eventos de la UI) ---

    def _on_guardar_clicked(self):
        """Recopila datos del formulario y los envía al ViewModel para guardarlos."""
        articulo_id = self.articulo_combo.currentData()
        if not articulo_id:
            QMessageBox.warning(self, "Dato Faltante", "Debe seleccionar un artículo.")
            return

        cantidades_por_dia = {}
        for day in range(self.programacion_table.columnCount()):
            item = self.programacion_table.item(0, day)
            if item and item.text().strip():
                try:
                    cantidad = int(item.text())
                    if cantidad > 0:
                        cantidades_por_dia[day + 1] = cantidad
                except ValueError:
                    QMessageBox.warning(self, "Dato Inválido", f"La cantidad para el día {day+1} no es un número válido.")
                    return
        
        # Usamos el primer día del mes para representar el mes/año
        fecha_mes = self.mes_anho_edit.date().toPython()
        primer_dia_mes = fecha_mes.replace(day=1)

        programacion_data = {
            "usuario_id": 1, # Placeholder para el ID del usuario logueado
            "articulo_contrato_id": articulo_id,
            "mes_anho": primer_dia_mes,
            "cantidades_por_dia": cantidades_por_dia
        }
        self.vm.guardar_programacion(programacion_data)

    def _on_generar_requerimiento_clicked(self):
        """Solicita la generación de un requerimiento consolidado para el mes seleccionado."""
        fecha_mes = self.mes_anho_edit.date()
        primer_dia_mes = fecha_mes.toPython().replace(day=1)
        
        reply = QMessageBox.question(
            self, "Confirmar Generación",
            f"¿Desea generar el requerimiento consolidado para {fecha_mes.toString('MMMM yyyy')}?\n"
            "Esta acción consolidará todas las programaciones del mes.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Placeholder para el ID del usuario logueado
            self.vm.generar_requerimiento(QDate(primer_dia_mes), usuario_id=1)

    def _on_cell_changed(self, row, column):
        """Se activa al editar una celda para validar la cantidad total del mes."""
        articulo_id = self.articulo_combo.currentData()
        if not articulo_id:
            return # No hacer nada si no hay artículo seleccionado

        total_mes = 0
        for day in range(self.programacion_table.columnCount()):
            item = self.programacion_table.item(0, day)
            if item and item.text().strip():
                try:
                    total_mes += int(item.text())
                except ValueError:
                    pass # Ignorar celdas no numéricas
        
        if total_mes > 0:
            self.vm.validar_disponibilidad_para_mes(articulo_id, total_mes)

    # --- Métodos que actualizan la UI en respuesta a señales del ViewModel ---

    def _update_articulos_combo(self, articulos: List[ArticuloContratoSimpleDTO]):
        """Puebla el ComboBox con la lista de artículos disponibles."""
        self.articulo_combo.blockSignals(True)
        self.articulo_combo.clear()
        self.articulo_combo.addItem("Seleccione un artículo...", None)
        for articulo in articulos:
            self.articulo_combo.addItem(f"{articulo.descripcion} ({articulo.clave_articulo})", articulo.id)
        self.articulo_combo.blockSignals(False)

    def _show_status_message(self, message: str):
        """Muestra un mensaje de estado al usuario."""
        if "Error" in message or "Advertencia" in message:
            QMessageBox.warning(self, "Atención", message)
        else:
            QMessageBox.information(self, "Información", message)

    def _show_requerimiento_info(self, req_dto: SalidaRequerimientoDTO):
        """Muestra la información del requerimiento generado."""
        QMessageBox.information(
            self, "Requerimiento Generado",
            f"Se ha generado con éxito el requerimiento de salida.\n\n"
            f"ID de QR: {req_dto.qr_id}\n"
            f"Estado: {req_dto.estado}\n"
            f"Fecha: {req_dto.fecha_generacion.strftime('%Y-%m-%d %H:%M')}\n\n"
            "Presente este código QR en el almacén para el despacho."
        )