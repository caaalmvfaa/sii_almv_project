# sigvcf/modules/proveedores/views.py
import qtawesome as qta
from typing import List
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QTableView, QSpinBox, QPushButton, QPlainTextEdit, QLineEdit,
    QLabel, QMessageBox, QHeaderView
)

from sigvcf.modules.proveedores.viewmodels import ProveedorViewModel
from sigvcf.modules.proveedores.dto import OrdenCompraProveedorDTO, EstadoEntregaDTO

# --- Modelo de Tabla para Órdenes de Compra del Proveedor ---

class OrdenesProveedorTableModel(QAbstractTableModel):
    def __init__(self, data: List[OrdenCompraProveedorDTO] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID Orden", "Cód. Licitación", "Fecha Entrega", "Estado"]

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
            orden = self._data[index.row()]
            if index.column() == 0: return orden.id
            if index.column() == 1: return orden.codigo_licitacion_contrato
            if index.column() == 2: return str(orden.fecha_entrega_programada)
            if index.column() == 3: return orden.estado
        return None

# --- Vista Principal del Portal de Proveedores ---

class ProveedorView(QWidget):
    def __init__(self, view_model: ProveedorViewModel, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setWindowTitle("Portal de Proveedores")
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        proveedor_id_layout = QHBoxLayout()
        proveedor_id_layout.addWidget(QLabel("<b>Simulación: ID del Proveedor Logueado:</b>"))
        self.proveedor_id_spinbox = QSpinBox()
        self.proveedor_id_spinbox.setRange(1, 999)
        proveedor_id_layout.addWidget(self.proveedor_id_spinbox)
        proveedor_id_layout.addStretch()
        main_layout.addLayout(proveedor_id_layout)

        ordenes_group = QGroupBox("Órdenes de Compra Pendientes")
        ordenes_layout = QVBoxLayout(ordenes_group)
        self.ordenes_table = QTableView()
        self.ordenes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.actualizar_ordenes_button = QPushButton("Actualizar Lista")
        self.actualizar_ordenes_button.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        ordenes_layout.addWidget(self.ordenes_table)
        ordenes_layout.addWidget(self.actualizar_ordenes_button, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(ordenes_group)

        factura_group = QGroupBox("Cargar Factura (XML)")
        factura_layout = QFormLayout(factura_group)
        self.factura_orden_id_spinbox = QSpinBox()
        self.factura_orden_id_spinbox.setRange(1, 999999)
        self.xml_content_edit = QPlainTextEdit()
        self.xml_content_edit.setPlaceholderText("Pegue aquí el contenido completo del archivo XML de la factura...")
        self.subir_factura_button = QPushButton("Subir Factura")
        self.subir_factura_button.setIcon(qta.icon('fa5s.upload', color='white'))
        factura_layout.addRow("ID de la Orden de Compra:", self.factura_orden_id_spinbox)
        factura_layout.addRow("Contenido XML:", self.xml_content_edit)
        factura_layout.addRow(self.subir_factura_button)
        main_layout.addWidget(factura_group)

        rastreo_group = QGroupBox("Rastrear Entrega")
        rastreo_layout = QFormLayout(rastreo_group)
        self.folio_rb_edit = QLineEdit()
        self.folio_rb_edit.setPlaceholderText("Ej: RB-20231027153000-123")
        self.rastrear_button = QPushButton("Rastrear")
        self.rastrear_button.setIcon(qta.icon('fa5s.search-location', color='white'))
        self.estado_folio_label = QLabel("---")
        self.estado_fecha_label = QLabel("---")
        self.estado_orden_label = QLabel("---")
        rastreo_layout.addRow("Folio R.B. de la Entrega:", self.folio_rb_edit)
        rastreo_layout.addRow(self.rastrear_button)
        rastreo_layout.addRow("<b>Estado de la Entrega:</b>", None)
        rastreo_layout.addRow("Folio R.B.:", self.estado_folio_label)
        rastreo_layout.addRow("Fecha de Recepción:", self.estado_fecha_label)
        rastreo_layout.addRow("Estado Actual de la Orden:", self.estado_orden_label)
        main_layout.addWidget(rastreo_group)

    def _connect_signals(self):
        self.actualizar_ordenes_button.clicked.connect(self._on_cargar_ordenes)
        self.subir_factura_button.clicked.connect(self._on_subir_factura)
        self.rastrear_button.clicked.connect(self._on_rastrear_entrega)

        self.vm.ordenes_cargadas.connect(self._update_ordenes_table)
        self.vm.estado_entrega_obtenido.connect(self._display_estado_entrega)
        self.vm.operacion_finalizada.connect(self._show_status_message)

    def _on_cargar_ordenes(self):
        proveedor_id = self.proveedor_id_spinbox.value()
        self.vm.cargar_ordenes_pendientes(proveedor_id)

    def _on_subir_factura(self):
        proveedor_id = self.proveedor_id_spinbox.value()
        orden_id = self.factura_orden_id_spinbox.value()
        xml_content = self.xml_content_edit.toPlainText()
        self.vm.subir_factura_xml(orden_id, proveedor_id, xml_content)
        self.xml_content_edit.clear()

    def _on_rastrear_entrega(self):
        proveedor_id = self.proveedor_id_spinbox.value()
        folio_rb = self.folio_rb_edit.text()
        self.vm.rastrear_entrega(folio_rb, proveedor_id)

    def _update_ordenes_table(self, ordenes: List[OrdenCompraProveedorDTO]):
        model = OrdenesProveedorTableModel(ordenes)
        self.ordenes_table.setModel(model)

    def _display_estado_entrega(self, estado: EstadoEntregaDTO | None):
        if estado:
            self.estado_folio_label.setText(estado.folio_rb)
            self.estado_fecha_label.setText(estado.fecha_recepcion.strftime('%Y-%m-%d %H:%M:%S'))
            self.estado_orden_label.setText(estado.estado_orden_compra)
        else:
            self.estado_folio_label.setText("---")
            self.estado_fecha_label.setText("---")
            self.estado_orden_label.setText("---")

    def _show_status_message(self, message: str):
        if "Error" in message:
            QMessageBox.warning(self, "Error", message)
        else:
            QMessageBox.information(self, "Información", message)