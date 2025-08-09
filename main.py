### FILE: main.py

import sys
import logging
import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QListWidget,
    QStackedWidget, QSizePolicy, QDialog
)
from PySide6.QtGui import QIcon

# Importar el contenedor y el usuario
from containers import Container
from sigvcf.core.domain.models import Usuario

# Importar vistas
from sigvcf.auth.views import LoginView
from sigvcf.modules.almacen.views import AlmacenView
from sigvcf.modules.nutricion.views import NutricionView
from sigvcf.modules.juridico.views import JuridicoView
from sigvcf.modules.administrativo.views import ContratosView
from sigvcf.modules.financiero.views import FinancieroView
from sigvcf.modules.proveedores.views import ProveedorView

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación con navegación por módulos y control de acceso por roles.
    """
    def __init__(self, usuario: dict, container: Container):
        super().__init__()
        self.usuario = usuario
        self.container = container
        self.setWindowTitle(f"SIG-VCF - Usuario: {self.usuario['nombre']} (Rol: {self.usuario['rol']['nombre_rol']})")
        self.setGeometry(100, 100, 1280, 720)

        # Establecer el ícono de la ventana principal
        try:
            self.setWindowIcon(QIcon("assets/app_icon.png"))
        except:
            logger.warning("No se pudo cargar el ícono 'assets/app_icon.png'")


        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.nav_list = QListWidget()
        self.nav_list.setMaximumWidth(220)
        self.nav_list.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.nav_list)

        self.view_stack = QStackedWidget()
        main_layout.addWidget(self.view_stack)

        self._setup_modules_based_on_role()

        self.nav_list.currentRowChanged.connect(self.view_stack.setCurrentIndex)
        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)
        logger.info("MainWindow inicializada y mostrada.")

    def _setup_modules_based_on_role(self):
        all_modules = {
            "Gestión de Contratos": (self.container.contrato_view_model, ContratosView),
            "Planificación Nutricional": (self.container.nutricion_view_model, NutricionView),
            "Control de Almacén": (self.container.almacen_view_model, AlmacenView),
            "Gestión Jurídica": (self.container.juridico_view_model, JuridicoView),
            "Recursos Financieros": (self.container.financiero_view_model, FinancieroView),
            "Portal de Proveedores": (self.container.proveedor_view_model, ProveedorView),
        }
        icon_map = {
            "Gestión de Contratos": "fa5s.file-signature",
            "Planificación Nutricional": "fa5s.apple-alt",
            "Control de Almacén": "fa5s.boxes",
            "Gestión Jurídica": "fa5s.gavel",
            "Recursos Financieros": "fa5s.file-invoice-dollar",
            "Portal de Proveedores": "fa5s.truck"
        }
        # Permisos por rol
        role_permissions = {
            'Admin': list(all_modules.keys()),
            'Nutricionista': ["Planificación Nutricional"],
            'Almacenista': ["Control de Almacén"],
            'Contador': ["Recursos Financieros"],
            'Proveedor': ["Portal de Proveedores"],
        }
        user_role = self.usuario['rol']['nombre_rol']
        allowed_modules = role_permissions.get(user_role, [])
        logger.info(f"Configurando módulos para el rol '{user_role}'. Módulos permitidos: {allowed_modules}")
        for name, (vm_factory, view_class) in all_modules.items():
            if name in allowed_modules:
                icon_name = icon_map.get(name, "fa5s.question-circle")
                icon = qta.icon(icon_name, color='#f0f0f0', color_active='#66b2ff')
                list_item = self.nav_list.addItem(name)
                # La API de QListWidget cambió, ahora se añade el item y luego se le asigna el ícono
                self.nav_list.item(self.nav_list.count() - 1).setIcon(icon)
                view_model = vm_factory()
                view_widget = view_class(view_model)
                self.view_stack.addWidget(view_widget)


class Application:
    def __init__(self, container: Container):
        self.container = container
        self.main_window = None
        self.authenticated_user = None

    def run(self):
        logger.info("Iniciando el ciclo de vida de la aplicación. Mostrando pantalla de login.")
        login_vm = self.container.login_view_model()
        login_vm.login_exitoso.connect(self._on_login_success)
        
        login_view = LoginView(view_model=login_vm)
        
        if login_view.exec() == QDialog.DialogCode.Accepted and self.authenticated_user is not None:
            self.main_window = MainWindow(usuario=self.authenticated_user, container=self.container)
            self.main_window.show()
            return True # Indica que la app principal debe correr
        logger.info("El usuario cerró la ventana de login o no se autenticó correctamente. La aplicación terminará.")
        return False # Indica que la app debe cerrarse

    def _on_login_success(self, usuario_dict):
        # Permitir tanto objeto Usuario como dict
        nombre_usuario = None
        if isinstance(usuario_dict, dict):
            nombre_usuario = usuario_dict.get('nombre', str(usuario_dict))
        else:
            nombre_usuario = getattr(usuario_dict, 'nombre', str(usuario_dict))
        logger.info(f"Login exitoso para el usuario '{nombre_usuario}'.")
        self.authenticated_user = usuario_dict

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log", mode='w'),
            logging.StreamHandler()
        ]
    )
    
    app = QApplication(sys.argv)
    
    try:
        with open("styles.qss", "r") as f:
            _style = f.read()
            app.setStyleSheet(_style)
    except FileNotFoundError:
        logging.warning("No se encontró el archivo 'styles.qss'. Se usará el estilo por defecto.")

    container = Container()
    container.wire(
        modules=[
            sys.modules[__name__], 
            "sigvcf.auth.viewmodels", 
            "sigvcf.modules.almacen.viewmodels",
            "sigvcf.modules.nutricion.viewmodels", 
            "sigvcf.modules.juridico.viewmodels",
            "sigvcf.modules.administrativo.viewmodels", 
            "sigvcf.modules.financiero.viewmodels",
            "sigvcf.modules.proveedores.viewmodels",
        ]
    )

    app_manager = Application(container)
    if app_manager.run():
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()