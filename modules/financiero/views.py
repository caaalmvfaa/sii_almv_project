# sigvcf/modules/financiero/views.py
from typing import List
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QTableView, QPushButton,
    QMessageBox, QHeaderView, QHBoxLayout, QSpinBox, QLabel
)

from sigvcf.modules.financiero.viewmodels import FinancieroViewModel
from sigvcf.core.domain.models import EntradaBodega
from sigvcf.modules.financiero.dto import RegistroContableDTO

# --- Modelos de Tabla Personalizados ---

class ExpedientesTableModel(QAbstractTableModel):
    def __init__(self, data: List[EntradaBodega] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID Entrada", "Folio R.B.", "ID Orden Compra", "Fecha Recepción"]

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            expediente = self._data[index.row()]
            if index.column() == 0: return expediente.id
            if index.column() == 1: return expediente.folio_rb
            if index.column() == 2: return expediente.orden_compra_id
            if index.column() == 3: return expediente.fecha_recepcion.strftime('%Y-%m-%d %H:%M')
        return None

    def get_id_at_row(self, row: int) -> int | None:
        if 0 <= row < len(self._data):
            return self._data[row].id
        return None

class PolizasTableModel(QAbstractTableModel):
    def __init__(self, data: List[RegistroContableDTO] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID Póliza", "ID Entrada", "Asiento Contable", "Fecha", "Contador ID"]

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            poliza = self._data[index.row()]
            if index.column() == 0: return poliza.id
            if index.column() == 1: return poliza.entrada_bodega_id
            if index.column() == 2: return poliza.asiento_contable
            if index.column() == 3: return poliza.fecha_contabilizacion.strftime('%Y-%m-%d')
            if index.column() == 4: return poliza.contador_id
        return None

    def get_id_at_row(self, row: int) -> int | None:
        if 0 <= row < len(self._data):
            return self._data[row].id
        return None

# --- Vista Principal del Módulo Financiero ---

class FinancieroView(QWidget):
    def __init__(self, view_model: FinancieroViewModel, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setWindowTitle("Módulo de Recursos Financieros")
        self._setup_ui()
        self._connect_signals()
        self.vm.cargar_bandejas()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Sección 1: Bandeja del Contador ---
        contador_group = QGroupBox("Bandeja del Contador")
        contador_layout = QVBoxLayout(contador_group)
        
        contador_layout.addWidget(QLabel("<b>Expedientes Pendientes de Verificación (Estado: RECIBIDA)</b>"))
        self.expedientes_table = QTableView()
        self.expedientes_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.expedientes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        contador_layout.addWidget(self.expedientes_table)

        contador_actions = QHBoxLayout()
        self.verificar_button = QPushButton("Verificar Expediente Seleccionado")
        self.generar_poliza_button = QPushButton("Generar Póliza para Expediente")
        self.contador_id_spinbox = QSpinBox()
        self.contador_id_spinbox.setRange(1, 999)
        contador_actions.addWidget(self.verificar_button)
        contador_actions.addStretch()
        contador_actions.addWidget(QLabel("ID del Contador:"))
        contador_actions.addWidget(self.contador_id_spinbox)
        contador_actions.addWidget(self.generar_poliza_button)
        contador_layout.addLayout(contador_actions)
        main_layout.addWidget(contador_group)

        # --- Sección 2: Bandeja de Aprobación (Jefatura) ---
        jefatura_group = QGroupBox("Bandeja de Aprobación (Jefatura)")
        jefatura_layout = QVBoxLayout(jefatura_group)

        jefatura_layout.addWidget(QLabel("<b>Pólizas Pendientes de Aprobación (Estado: VERIFICADO)</b>"))
        self.polizas_table = QTableView()
        self.polizas_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.polizas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        jefatura_layout.addWidget(self.polizas_table)

        self.aprobar_button = QPushButton("Aprobar Póliza Seleccionada")
        jefatura_layout.addWidget(self.aprobar_button, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(jefatura_group)

    def _connect_signals(self):
        # Vista -> ViewModel
        self.verificar_button.clicked.connect(self._on_verificar)
        self.generar_poliza_button.clicked.connect(self._on_generar_poliza)
        self.aprobar_button.clicked.connect(self._on_aprobar_poliza)

        # ViewModel -> Vista
        self.vm.expedientes_pendientes_cargados.connect(self._update_expedientes_table)
        self.vm.polizas_pendientes_cargadas.connect(self._update_polizas_table)
        self.vm.operacion_finalizada.connect(self._show_status_message)

    def _on_verificar(self):
        model = self.expedientes_table.model()
        selection = self.expedientes_table.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un expediente de la tabla.")
            return
        entrada_id = model.get_id_at_row(selection.currentIndex().row())
        self.vm.verificar_expediente_seleccionado(entrada_id)

    def _on_generar_poliza(self):
        model = self.expedientes_table.model()
        selection = self.expedientes_table.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un expediente para generar su póliza.")
            return
        entrada_id = model.get_id_at_row(selection.currentIndex().row())
        contador_id = self.contador_id_spinbox.value()
        self.vm.generar_poliza(entrada_id, contador_id)

    def _on_aprobar_poliza(self):
        model = self.polizas_table.model()
        selection = self.polizas_table.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione una póliza para aprobar.")
            return
        poliza_id = model.get_id_at_row(selection.currentIndex().row())
        self.vm.aprobar_poliza_seleccionada(poliza_id)

    def _update_expedientes_table(self, expedientes: List[EntradaBodega]):
        model = ExpedientesTableModel(expedientes)
        self.expedientes_table.setModel(model)

    def _update_polizas_table(self, polizas: List[RegistroContableDTO]):
        model = PolizasTableModel(polizas)
        self.polizas_table.setModel(model)

    def _show_status_message(self, message: str):
        if "Error" in message:
            QMessageBox.warning(self, "Error", message)
        else:
            QMessageBox.information(self, "Información", message)