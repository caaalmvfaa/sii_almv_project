# sigvcf/modules/almacen/views.py
import qtawesome as qta
from typing import List
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableView, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QLineEdit, QMessageBox,
    QHeaderView
)

from sigvcf.modules.almacen.viewmodels import AlmacenViewModel
from sigvcf.modules.almacen.dto import StockStatusDTO, EntradaBodegaDTO

# --- Modelo de Tabla para el Stock ---

class StockTableModel(QAbstractTableModel):
    def __init__(self, data: List[StockStatusDTO] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["Clave Artículo", "Descripción", "Contratado", "Consumido", "Disponible"]

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
            stock_item = self._data[index.row()]
            if index.column() == 0: return stock_item.clave_articulo
            if index.column() == 1: return stock_item.descripcion
            if index.column() == 2: return stock_item.cant_maxima
            if index.column() == 3: return stock_item.cant_consumida
            if index.column() == 4: return stock_item.stock_disponible
        return None

# --- Vista Principal del Módulo de Almacén ---

class AlmacenView(QWidget):
    def __init__(self, view_model: AlmacenViewModel, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setWindowTitle("Módulo de Almacén de Víveres")
        self._setup_ui()
        self._connect_signals()
        self.vm.actualizar_stock() # Carga inicial

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Pestaña 1: Control de Inventario ---
        stock_tab = QWidget()
        stock_layout = QVBoxLayout(stock_tab)
        self.stock_table = QTableView()
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.actualizar_stock_button = QPushButton("Actualizar Stock")
        self.actualizar_stock_button.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        stock_layout.addWidget(self.stock_table)
        stock_layout.addWidget(self.actualizar_stock_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.tabs.addTab(stock_tab, "Control de Inventario")

        # --- Pestaña 2: Recepción de Mercancía ---
        recepcion_tab = QWidget()
        recepcion_layout = QVBoxLayout(recepcion_tab)
        recepcion_group = QGroupBox("Registrar Nueva Entrada de Bodega")
        form_layout = QFormLayout(recepcion_group)
        self.orden_id_spinbox = QSpinBox()
        self.orden_id_spinbox.setRange(1, 999999)
        self.factura_path_edit = QLineEdit()
        self.factura_path_edit.setPlaceholderText("Ej: /path/a/factura_proveedor.xml")
        self.recepcionista_id_spinbox = QSpinBox()
        self.recepcionista_id_spinbox.setRange(1, 999)
        self.registrar_entrada_button = QPushButton("Registrar Entrada")
        self.registrar_entrada_button.setIcon(qta.icon('fa5s.dolly-flatbed', color='white'))
        form_layout.addRow("ID de Orden de Compra:", self.orden_id_spinbox)
        form_layout.addRow("Ruta de Factura XML:", self.factura_path_edit)
        form_layout.addRow("ID del Recepcionista:", self.recepcionista_id_spinbox)
        form_layout.addRow(self.registrar_entrada_button)
        recepcion_layout.addWidget(recepcion_group)
        recepcion_layout.addStretch()
        self.tabs.addTab(recepcion_tab, "Recepción de Mercancía")

        # --- Pestaña 3: Despacho por QR ---
        despacho_tab = QWidget()
        despacho_layout = QVBoxLayout(despacho_tab)
        despacho_group = QGroupBox("Despacho de Requerimientos")
        despacho_form = QFormLayout(despacho_group)
        self.qr_id_edit = QLineEdit()
        self.qr_id_edit.setPlaceholderText("Introduzca o escanee el ID del QR del requerimiento")
        self.despachar_button = QPushButton("Despachar")
        self.despachar_button.setIcon(qta.icon('fa5s.shipping-fast', color='white'))
        despacho_form.addRow("ID de QR:", self.qr_id_edit)
        despacho_form.addRow(self.despachar_button)
        despacho_layout.addWidget(despacho_group)
        despacho_layout.addStretch()
        self.tabs.addTab(despacho_tab, "Despacho por QR")

    def _connect_signals(self):
        # Vista -> ViewModel
        self.actualizar_stock_button.clicked.connect(self.vm.actualizar_stock)
        self.registrar_entrada_button.clicked.connect(self._on_registrar_entrada)
        self.despachar_button.clicked.connect(self._on_despachar)

        # ViewModel -> Vista
        self.vm.stock_actualizado.connect(self._update_stock_table)
        self.vm.operacion_finalizada.connect(self._show_status_message)
        self.vm.entrada_registrada.connect(self._confirmar_entrada)

    def _on_registrar_entrada(self):
        datos_entrada = {
            "orden_compra_id": self.orden_id_spinbox.value(),
            "factura_xml_path": self.factura_path_edit.text(),
            "recepcionista_id": self.recepcionista_id_spinbox.value()
        }
        self.vm.registrar_nueva_entrada(datos_entrada)

    def _on_despachar(self):
        qr_id = self.qr_id_edit.text()
        self.vm.despachar_por_qr(qr_id)
        self.qr_id_edit.clear()

    def _update_stock_table(self, stock_list: List[StockStatusDTO]):
        model = StockTableModel(stock_list)
        self.stock_table.setModel(model)

    def _show_status_message(self, message: str):
        if "Error" in message:
            QMessageBox.warning(self, "Error", message)
        else:
            QMessageBox.information(self, "Información", message)

    def _confirmar_entrada(self, entrada: EntradaBodegaDTO):
        QMessageBox.information(
            self, "Entrada Registrada",
            f"Se ha registrado con éxito la entrada de mercancía.\n\n"
            f"Folio R.B. Asignado: {entrada.folio_rb}\n"
            f"Fecha de Recepción: {entrada.fecha_recepcion.strftime('%Y-%m-%d %H:%M')}"
        )
        # Limpiar formulario
        self.orden_id_spinbox.setValue(1)
        self.factura_path_edit.clear()
        self.recepcionista_id_spinbox.setValue(1)