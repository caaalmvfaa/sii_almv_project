# sigvcf/modules/juridico/views.py
import qtawesome as qta
from typing import List
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QTableView, QSpinBox, QPushButton, QComboBox, QTextEdit,
    QLabel, QMessageBox, QHeaderView
)

from sigvcf.modules.juridico.viewmodels import JuridicoViewModel
from sigvcf.modules.juridico.dto import ReporteIncumplimientoDTO, PenalizacionDTO

# --- Modelo de Tabla para Reportes ---

class ReportesTableModel(QAbstractTableModel):
    def __init__(self, data: List[ReporteIncumplimientoDTO] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID", "Contrato ID", "Tipo", "Estado", "Descripción"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            reporte = self._data[index.row()]
            if index.column() == 0: return reporte.id
            if index.column() == 1: return reporte.contrato_id
            if index.column() == 2: return reporte.tipo
            if index.column() == 3: return reporte.estado
            if index.column() == 4: return reporte.descripcion
        return None

# --- Vista Principal del Módulo Jurídico ---

class JuridicoView(QWidget):
    def __init__(self, view_model: JuridicoViewModel, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setWindowTitle("Módulo de Coordinación Jurídica")
        self._setup_ui()
        self._connect_signals()
        self.vm.cargar_reportes_pendientes()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Sección 1: Gestión de Incumplimientos ---
        gestion_group = QGroupBox("Gestión de Incumplimientos")
        gestion_layout = QVBoxLayout(gestion_group)

        self.reportes_table = QTableView()
        self.reportes_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.reportes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        gestion_layout.addWidget(QLabel("Reportes Pendientes:"))
        gestion_layout.addWidget(self.reportes_table)

        nuevo_reporte_group = QGroupBox("Registrar Nuevo Incumplimiento")
        form_layout = QFormLayout(nuevo_reporte_group)
        self.contrato_id_spinbox = QSpinBox()
        self.contrato_id_spinbox.setRange(1, 999999)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(['CALIDAD', 'ATRASO', 'ADMINISTRATIVO'])
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(['PENDIENTE', 'EN_ANALISIS', 'RESUELTO'])
        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setPlaceholderText("Describa detalladamente el incumplimiento...")
        self.registrar_button = QPushButton("Registrar Incumplimiento")
        self.registrar_button.setIcon(qta.icon('fa5s.check-circle', color='white'))
        
        form_layout.addRow("ID del Contrato:", self.contrato_id_spinbox)
        form_layout.addRow("Tipo de Incumplimiento:", self.tipo_combo)
        form_layout.addRow("Estado Inicial:", self.estado_combo)
        form_layout.addRow("Descripción:", self.descripcion_edit)
        form_layout.addRow(self.registrar_button)
        gestion_layout.addWidget(nuevo_reporte_group)
        
        main_layout.addWidget(gestion_group)

        # --- Sección 2: Calculadora de Penalizaciones ---
        calculadora_group = QGroupBox("Calculadora de Penalizaciones por Atraso")
        calc_layout = QFormLayout(calculadora_group)
        
        self.orden_id_spinbox = QSpinBox()
        self.orden_id_spinbox.setRange(1, 999999)
        self.calcular_button = QPushButton("Calcular Penalización")
        self.calcular_button.setIcon(qta.icon('fa5s.calculator', color='white'))
        
        self.dias_atraso_label = QLabel("---")
        self.monto_penalizacion_label = QLabel("---")
        self.detalle_calculo_label = QLabel("---")
        
        calc_layout.addRow("ID de Orden de Compra:", self.orden_id_spinbox)
        calc_layout.addRow(self.calcular_button)
        calc_layout.addRow(QLabel("<b>Resultado del Cálculo:</b>"))
        calc_layout.addRow("Días de Atraso:", self.dias_atraso_label)
        calc_layout.addRow("Monto de Penalización ($):", self.monto_penalizacion_label)
        calc_layout.addRow("Detalle:", self.detalle_calculo_label)
        
        main_layout.addWidget(calculadora_group)

    def _connect_signals(self):
        self.registrar_button.clicked.connect(self._on_registrar_incumplimiento)
        self.calcular_button.clicked.connect(self._on_calcular_penalizacion)

        self.vm.reportes_cargados.connect(self._update_reportes_table)
        self.vm.penalizacion_calculada.connect(self._display_penalizacion_result)
        self.vm.operacion_finalizada.connect(self._show_status_message)

    def _on_registrar_incumplimiento(self):
        reporte_data = {
            "contrato_id": self.contrato_id_spinbox.value(),
            "tipo": self.tipo_combo.currentText(),
            "estado": self.estado_combo.currentText(),
            "descripcion": self.descripcion_edit.toPlainText()
        }
        self.vm.registrar_incumplimiento(reporte_data)
        self.descripcion_edit.clear()

    def _on_calcular_penalizacion(self):
        orden_id = self.orden_id_spinbox.value()
        self.vm.calcular_penalizacion(orden_id)

    def _update_reportes_table(self, reportes: List[ReporteIncumplimientoDTO]):
        model = ReportesTableModel(reportes)
        self.reportes_table.setModel(model)

    def _display_penalizacion_result(self, resultado: PenalizacionDTO | None):
        if resultado:
            self.dias_atraso_label.setText(str(resultado.dias_atraso))
            self.monto_penalizacion_label.setText(f"{resultado.monto_penalizacion:,.2f}")
            self.detalle_calculo_label.setText(resultado.calculo_detalle)
        else:
            self.dias_atraso_label.setText("---")
            self.monto_penalizacion_label.setText("---")
            self.detalle_calculo_label.setText("---")

    def _show_status_message(self, message: str):
        if "Error" in message:
            QMessageBox.warning(self, "Error", message)
        else:
            QMessageBox.information(self, "Información", message)