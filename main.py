# main.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QListWidget,
    QStackedWidget, QSizePolicy, QDialog
)

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

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación con navegación por módulos y control de acceso por roles.
    """
    def __init__(self, usuario: Usuario, container: Container):
        super().__init__()
        self.usuario = usuario
        self.container = container
        self.setWindowTitle(f"SIG-VCF - Usuario: {self.usuario.nombre} (Rol: {self.usuario.rol.nombre_rol})")
        self.setGeometry(100, 100, 1280, 720)

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

    def _setup_modules_based_on_role(self):
        """
        Instancia y muestra los módulos a los que el usuario tiene acceso según su rol.
        """
        all_modules = {
            "Gestión de Contratos": (self.container.contrato_view_model, ContratosView),
            "Planificación Nutricional": (self.container.nutricion_view_model, NutricionView),
            "Control de Almacén": (self.container.almacen_view_model, AlmacenView),
            "Gestión Jurídica": (self.container.juridico_view_model, JuridicoView),
            "Recursos Financieros": (self.container.financiero_view_model, FinancieroView),
            "Portal de Proveedores": (self.container.proveedor_view_model, ProveedorView),
        }

        # Mapeo de roles a los nombres de los módulos que pueden ver
        role_permissions = {
            'Admin': list(all_modules.keys()),
            'Nutricionista': ["Planificación Nutricional"],
            'Almacenista': ["Control de Almacén"],
            'Contador': ["Recursos Financieros"],
            'Proveedor': ["Portal de Proveedores"],
        }

        user_role = self.usuario.rol.nombre_rol
        allowed_modules = role_permissions.get(user_role, [])

        for name, (vm_factory, view_class) in all_modules.items():
            if name in allowed_modules:
                self.nav_list.addItem(name)
                view_model = vm_factory()
                view_widget = view_class(view_model)
                self.view_stack.addWidget(view_widget)

class Application:
    """Clase que gestiona el ciclo de vida de la aplicación."""
    def __init__(self, container: Container):
        self.container = container
        self.main_window = None
        self.authenticated_user = None

    def run(self):
        login_vm = self.container.login_view_model()
        login_vm.login_exitoso.connect(self._on_login_success)
        
        login_view = LoginView(view_model=login_vm)
        
        # exec() es bloqueante. El código no continuará hasta que el diálogo se cierre.
        if login_view.exec() == QDialog.DialogCode.Accepted:
            # Si el login fue exitoso, el usuario ya está guardado en self.authenticated_user
            self.main_window = MainWindow(usuario=self.authenticated_user, container=self.container)
            self.main_window.show()
            return True
        return False

    def _on_login_success(self, usuario: Usuario):
        self.authenticated_user = usuario

def main() -> None:
    app = QApplication(sys.argv)
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
        # El usuario cerró la ventana de login sin autenticarse
        sys.exit(0)

if __name__ == "__main__":
    main()