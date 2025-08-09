# sigvcf/modules/administrativo/views.py
import sys
from typing import List, Dict, Any
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTableView, QPushButton, QGroupBox,
    QFormLayout, QLineEdit, QComboBox, QDateEdit, QMessageBox, QLabel
)

from sigvcf.modules.administrativo.viewmodels import ContratoViewModel
from sigvcf.modules.administrativo.dto import ContratoDTO, ArticuloContratoDTO
from sigvcf.modules.proveedores.dto import ProveedorDTO

# --- Modelos de Tabla Personalizados ---

class ContratosTableModel(QAbstractTableModel):
    def __init__(self, data: List[ContratoDTO] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID", "Cód. Licitación", "Proveedor ID", "Inicio", "Fin"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            contrato = self._data[index.row()]
            if index.column() == 0: return contrato.id
            if index.column() == 1: return contrato.codigo_licitacion
            if index.column() == 2: return contrato.proveedor_id
            if index.column() == 3: return str(contrato.fecha_inicio)
            if index.column() == 4: return str(contrato.fecha_fin)
        return None

    def get_id_at_row(self, row: int) -> int | None:
        if 0 <= row < len(self._data):
            return self._data[row].id
        return None

class ArticulosTableModel(QAbstractTableModel):
    def __init__(self, data: List[ArticuloContratoDTO] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["Clave", "Descripción", "Unidad", "Precio", "Cant. Máx", "Clasif."]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]

    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            articulo = self._data[index.row()]
            if index.column() == 0: return articulo.clave_articulo
            if index.column() == 1: return articulo.descripcion
            if index.column() == 2: return articulo.unidad_medida
            if index.column() == 3: return articulo.precio_unitario
            if index.column() == 4: return articulo.cant_maxima
            if index.column() == 5: return articulo.clasificacion
        return None

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            articulo = self._data[index.row()]
            try:
                if index.column() == 0: articulo.clave_articulo = str(value)
                elif index.column() == 1: articulo.descripcion = str(value)
                elif index.column() == 2: articulo.unidad_medida = str(value)
                elif index.column() == 3: articulo.precio_unitario = float(value)
                elif index.column() == 4: articulo.cant_maxima = int(value)
                elif index.column() == 5: articulo.clasificacion = str(value)
                else: return False
                self.dataChanged.emit(index, index)
                return True
            except (ValueError, TypeError):
                return False
        return False

    def get_all_articles_as_dicts(self) -> List[Dict]:
        return [art.model_dump() for art in self._data]

    def add_empty_row(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data.append(ArticuloContratoDTO(clave_articulo="", descripcion="", unidad_medida="", precio_unitario=0.0, cant_maxima=0, clasificacion=""))
        self.endInsertRows()

    def remove_row(self, row: int):
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(QModelIndex(), row, row)
            self._data.pop(row)
            self.endRemoveRows()

# --- Vista Principal del Módulo ---

class ContratosView(QWidget):
    def __init__(self, view_model: ContratoViewModel, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setWindowTitle("Gestión de Contratos")
        self._setup_ui()
        self._connect_signals()
        self.vm.cargar_datos_iniciales()

    def _setup_ui(self):
        # Layout principal
        main_layout = QHBoxLayout(self)

        # Panel izquierdo: Lista de contratos
        left_panel = QVBoxLayout()
        self.contracts_table = QTableView()
        self.contracts_table.setSelectionBehavior(QTableView.SelectRows)
        self.contracts_table.setSelectionMode(QTableView.SingleSelection)
        self.new_contract_button = QPushButton("Nuevo Contrato")
        left_panel.addWidget(QLabel("Contratos Existentes"))
        left_panel.addWidget(self.contracts_table)
        left_panel.addWidget(self.new_contract_button)
        main_layout.addLayout(left_panel, 1)

        # Panel derecho: Formulario de edición
        right_panel = QGroupBox("Detalle del Contrato")
        form_layout = QVBoxLayout(right_panel)
        
        # Formulario de datos del contrato
        self.form = QFormLayout()
        self.codigo_licitacion_edit = QLineEdit()
        self.proveedor_combo = QComboBox()
        self.fecha_inicio_edit = QDateEdit(calendarPopup=True)
        self.fecha_fin_edit = QDateEdit(calendarPopup=True)
        self.form.addRow("Cód. Licitación:", self.codigo_licitacion_edit)
        self.form.addRow("Proveedor:", self.proveedor_combo)
        self.form.addRow("Fecha Inicio:", self.fecha_inicio_edit)
        self.form.addRow("Fecha Fin:", self.fecha_fin_edit)
        form_layout.addLayout(self.form)

        # Tabla de artículos
        form_layout.addWidget(QLabel("Artículos del Contrato"))
        self.articles_table = QTableView()
        form_layout.addWidget(self.articles_table)
        
        # Botones para artículos
        article_buttons_layout = QHBoxLayout()
        self.add_article_button = QPushButton("Añadir Artículo")
        self.remove_article_button = QPushButton("Quitar Artículo")
        article_buttons_layout.addWidget(self.add_article_button)
        article_buttons_layout.addWidget(self.remove_article_button)
        form_layout.addLayout(article_buttons_layout)

        # Botones de acción
        action_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.save_button)
        form_layout.addLayout(action_buttons_layout)

        main_layout.addWidget(right_panel, 2)

    def _connect_signals(self):
        # Conexiones Vista -> ViewModel
        self.new_contract_button.clicked.connect(self.vm.crear_nuevo_contrato)
        self.contracts_table.selectionModel().selectionChanged.connect(self._on_contract_selected)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.add_article_button.clicked.connect(self._on_add_article)
        self.remove_article_button.clicked.connect(self._on_remove_article)

        # Conexiones ViewModel -> Vista
        self.vm.contratos_changed.connect(self._update_contracts_table)
        self.vm.proveedores_changed.connect(self._update_proveedores_combo)
        self.vm.contrato_actual_changed.connect(self._populate_form)
        self.vm.status_message.connect(lambda msg: QMessageBox.information(self, "Información", msg))

    # --- Slots de la Vista ---

    def _on_contract_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes: return
        row = indexes[0].row()
        model = self.contracts_table.model()
        contrato_id = model.get_id_at_row(row)
        if contrato_id:
            self.vm.seleccionar_contrato(contrato_id)

    def _on_save_clicked(self):
        proveedor_id = self.proveedor_combo.currentData()
        if not proveedor_id:
            QMessageBox.warning(self, "Dato Faltante", "Debe seleccionar un proveedor.")
            return

        articles_model = self.articles_table.model()
        contrato_data = {
            "codigo_licitacion": self.codigo_licitacion_edit.text(),
            "proveedor_id": proveedor_id,
            "fecha_inicio": self.fecha_inicio_edit.date().toPython(),
            "fecha_fin": self.fecha_fin_edit.date().toPython(),
            "articulos": articles_model.get_all_articles_as_dicts() if articles_model else []
        }
        self.vm.guardar_contrato_actual(contrato_data)

    def _on_add_article(self):
        model = self.articles_table.model()
        if isinstance(model, ArticulosTableModel):
            model.add_empty_row()

    def _on_remove_article(self):
        model = self.articles_table.model()
        selection = self.articles_table.selectionModel()
        if isinstance(model, ArticulosTableModel) and selection.hasSelection():
            row_to_remove = selection.currentIndex().row()
            model.remove_row(row_to_remove)

    def _update_contracts_table(self, contratos: List[ContratoDTO]):
        model = ContratosTableModel(contratos)
        self.contracts_table.setModel(model)
        self.contracts_table.resizeColumnsToContents()

    def _update_proveedores_combo(self, proveedores: List[ProveedorDTO]):
        self.proveedor_combo.clear()
        self.proveedor_combo.addItem("Seleccione un proveedor...", None)
        for p in proveedores:
            self.proveedor_combo.addItem(f"{p.razon_social} (ID: {p.id})", p.id)

    def _populate_form(self, contrato: ContratoDTO):
        self.codigo_licitacion_edit.setText(contrato.codigo_licitacion)
        self.fecha_inicio_edit.setDate(QDate.fromString(str(contrato.fecha_inicio), "yyyy-MM-dd"))
        self.fecha_fin_edit.setDate(QDate.fromString(str(contrato.fecha_fin), "yyyy-MM-dd"))
        
        index = self.proveedor_combo.findData(contrato.proveedor_id)
        self.proveedor_combo.setCurrentIndex(index if index != -1 else 0)

        articles_model = ArticulosTableModel(contrato.articulos)
        self.articles_table.setModel(articles_model)
        self.articles_table.resizeColumnsToContents()