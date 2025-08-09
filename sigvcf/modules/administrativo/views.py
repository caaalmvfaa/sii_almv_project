import sys
import qtawesome as qta
from typing import List, Dict, Any
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate, QSortFilterProxyModel, Signal
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
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
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
    
    def update_data(self, data: List[ContratoDTO]):
        self.beginResetModel()
        self._data = data
        self.endResetModel()


class ArticulosTableModel(QAbstractTableModel):
    validation_error = Signal(str)

    def __init__(self, data: List[ArticuloContratoDTO] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["Clave", "Descripción", "Unidad", "Precio", "Cant. Máx", "Clasif."]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            articulo = self._data[index.row()]
            if index.column() == 0: return articulo.clave_articulo
            if index.column() == 1: return articulo.descripcion
            if index.column() == 2: return articulo.unidad_medida
            if index.column() == 3: return articulo.precio_unitario
            if index.column() == 4: return articulo.cant_maxima
            if index.column() == 5: return articulo.clasificacion
        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            articulo = self._data[index.row()]
            column = index.column()
            header = self._headers[column]
            try:
                if column == 0: articulo.clave_articulo = str(value)
                elif column == 1: articulo.descripcion = str(value)
                elif column == 2: articulo.unidad_medida = str(value)
                elif column == 3: articulo.precio_unitario = float(value)
                elif column == 4: articulo.cant_maxima = int(value)
                elif column == 5: articulo.clasificacion = str(value)
                else: return False
                self.dataChanged.emit(index, index)
                return True
            except (ValueError, TypeError):
                expected_type = "un número entero" if column == 4 else "un número (ej: 123.45)"
                error_message = f"Valor inválido '{value}' para la columna '{header}'.\nSe esperaba {expected_type}."
                self.validation_error.emit(error_message)
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

        self.source_model = ContratosTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterKeyColumn(1)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.contracts_table.setModel(self.proxy_model)
        
        self._connect_signals()
        self.vm.cargar_datos_iniciales()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)

        left_panel = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por Cód. Licitación...")
        self.contracts_table = QTableView()
        self.contracts_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.contracts_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.contracts_table.setSortingEnabled(True)
        self.new_contract_button = QPushButton("Nuevo Contrato")
        self.new_contract_button.setIcon(qta.icon('fa5s.plus-circle', color='white'))
        
        left_panel.addWidget(QLabel("Contratos Existentes"))
        left_panel.addWidget(self.search_input)
        left_panel.addWidget(self.contracts_table)
        left_panel.addWidget(self.new_contract_button)
        main_layout.addLayout(left_panel, 1)

        right_panel = QGroupBox("Detalle del Contrato")
        form_layout = QVBoxLayout(right_panel)
        
        self.form = QFormLayout()
        self.codigo_licitacion_edit = QLineEdit()
        self.proveedor_combo = QComboBox()
        self.fecha_inicio_edit = QDateEdit(calendarPopup=True)
        self.fecha_fin_edit = QDateEdit(calendarPopup=True)
        
        # Widgets para gestión de expediente
        self.expediente_path_edit = QLineEdit()
        self.expediente_path_edit.setReadOnly(True)
        self.adjuntar_btn = QPushButton("Adjuntar...")
        self.adjuntar_btn.setIcon(qta.icon('fa5s.paperclip', color='white'))
        self.ver_btn = QPushButton("Ver")
        self.ver_btn.setIcon(qta.icon('fa5s.eye', color='white'))
        expediente_layout = QHBoxLayout()
        expediente_layout.addWidget(self.expediente_path_edit)
        expediente_layout.addWidget(self.adjuntar_btn)
        expediente_layout.addWidget(self.ver_btn)
        
        self.form.addRow("Cód. Licitación:", self.codigo_licitacion_edit)
        self.form.addRow("Proveedor:", self.proveedor_combo)
        self.form.addRow("Fecha Inicio:", self.fecha_inicio_edit)
        self.form.addRow("Fecha Fin:", self.fecha_fin_edit)
        self.form.addRow("Expediente:", expediente_layout)
        form_layout.addLayout(self.form)

        form_layout.addWidget(QLabel("Artículos del Contrato"))
        self.articles_table = QTableView()
        form_layout.addWidget(self.articles_table)
        
        article_buttons_layout = QHBoxLayout()
        self.add_article_button = QPushButton("Añadir Artículo")
        self.add_article_button.setIcon(qta.icon('fa5s.plus-circle', color='white'))
        self.remove_article_button = QPushButton("Quitar Artículo")
        self.remove_article_button.setIcon(qta.icon('fa5s.minus-circle', color='white'))
        article_buttons_layout.addWidget(self.add_article_button)
        article_buttons_layout.addWidget(self.remove_article_button)
        form_layout.addLayout(article_buttons_layout)

        action_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.save_button.setIcon(qta.icon('fa5s.save', color='white'))
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.save_button)
        form_layout.addLayout(action_buttons_layout)

        main_layout.addWidget(right_panel, 2)

    def _connect_signals(self):
        self.search_input.textChanged.connect(self.proxy_model.setFilterRegularExpression)
        self.new_contract_button.clicked.connect(self.vm.crear_nuevo_contrato)
        self.contracts_table.selectionModel().selectionChanged.connect(self._on_contract_selected)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.add_article_button.clicked.connect(self._on_add_article)
        self.remove_article_button.clicked.connect(self._on_remove_article)
        self.adjuntar_btn.clicked.connect(self._on_adjuntar_expediente)
        self.ver_btn.clicked.connect(self._on_ver_expediente)

        self.vm.contratos_changed.connect(self._update_contracts_table)
        self.vm.proveedores_changed.connect(self._update_proveedores_combo)
        self.vm.contrato_actual_changed.connect(self._populate_form)
        self.vm.status_message.connect(lambda msg: QMessageBox.information(self, "Información", msg))
        self.vm.expediente_adjuntado.connect(self.expediente_path_edit.setText)

    def _on_contract_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes: return
        
        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        row = source_index.row()
        
        contrato_id = self.source_model.get_id_at_row(row)
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
            "expediente_path": self.expediente_path_edit.text(),
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

    def _on_adjuntar_expediente(self):
        self.vm.adjuntar_expediente(self)

    def _on_ver_expediente(self):
        ruta = self.expediente_path_edit.text()
        self.vm.abrir_expediente(ruta)

    def _update_contracts_table(self, contratos: List[ContratoDTO]):
        self.source_model.update_data(contratos)
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
        self.expediente_path_edit.setText(contrato.expediente_path or "")
        
        index = self.proveedor_combo.findData(contrato.proveedor_id)
        self.proveedor_combo.setCurrentIndex(index if index != -1 else 0)

        articles_model = ArticulosTableModel(contrato.articulos)
        articles_model.validation_error.connect(self._show_validation_error)
        self.articles_table.setModel(articles_model)
        self.articles_table.resizeColumnsToContents()

    def _show_validation_error(self, message: str):
        QMessageBox.warning(self, "Error de Validación", message)
