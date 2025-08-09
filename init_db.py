# init_db.py
import datetime
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Asegurarse de que el script se ejecuta desde el directorio raíz del proyecto
# para que las importaciones funcionen correctamente.
# Si se ejecuta desde la raíz, 'sigvcf' estará en el path.
from sigvcf.core.domain.models import (
    Base,
    Rol,
    Usuario,
    Proveedor,
    Contrato,
    ArticuloContrato
)

# 1. Configuración de la Base de Datos
DATABASE_URL = "sqlite:///sigvcf_data.db"
engine = create_engine(DATABASE_URL, echo=True) # Echo para ver las sentencias SQL generadas

def create_database(db_engine):
    """
    Elimina la base de datos existente (si la hay) y crea todas las tablas
    definidas en los modelos de SQLAlchemy.
    """
    print("Eliminando base de datos anterior (si existe)...")
    # Eliminar el archivo si existe para un reinicio completo
    if os.path.exists("sigvcf_data.db"):
        os.remove("sigvcf_data.db")
    
    print("Creando todas las tablas...")
    Base.metadata.create_all(db_engine)
    print("Tablas creadas con éxito.")

def seed_data(session):
    """
    Puebla la base de datos con un conjunto inicial de datos de prueba.
    """
    print("Poblando la base de datos con datos de prueba...")
    try:
        # --- Crear Roles ---
        rol_admin = Rol(nombre_rol='Admin', permisos={'superuser': True})
        rol_proveedor = Rol(nombre_rol='Proveedor', permisos={'portal_access': True})
        rol_nutricion = Rol(nombre_rol='Nutricionista', permisos={'planning': True})
        rol_almacen = Rol(nombre_rol='Almacenista', permisos={'inventory': True})
        rol_contador = Rol(nombre_rol='Contador', permisos={'accounting': True})
        
        session.add_all([rol_admin, rol_proveedor, rol_nutricion, rol_almacen, rol_contador])
        session.flush() # Flush para obtener los IDs de los roles

        # --- Crear Usuarios ---
        usuario_admin = Usuario(
            nombre='Jesus',
            password_hash='123', # En un sistema real, usar bcrypt
            rol_id=rol_admin.id
        )
        usuario_nutri = Usuario(nombre='Nutri', password_hash='123', rol_id=rol_nutricion.id)
        usuario_almacen = Usuario(nombre='Almacenista', password_hash='123', rol_id=rol_almacen.id)
        usuario_conta = Usuario(nombre='Contador', password_hash='123', rol_id=rol_contador.id)

        session.add_all([usuario_admin, usuario_nutri, usuario_almacen, usuario_conta])

        # --- Crear Proveedores ---
        proveedor1 = Proveedor(
            razon_social='ALFONSO NUÑEZ DE LA O',
            rfc='DVS880101ABC',
            email_contacto='ventas@viveressureste.com'
        )
        proveedor2 = Proveedor(
            razon_social='T-MEDIC, SA DE CV',
            rfc='APG951215XYZ',
            email_contacto='contacto@alimentosgolfo.com'
        )
        session.add_all([proveedor1, proveedor2])
        session.flush() # Flush para obtener los IDs

        # --- Crear Contrato y Artículos ---
        contrato1 = Contrato(
            codigo_licitacion='LPL 01-2025',
            expediente_path='/docs/contratos/2023/LA-012.pdf',
            fecha_inicio=datetime.date(2025, 1, 1),
            fecha_fin=datetime.date(2025, 12, 31),
            proveedor_id=proveedor1.id
        )

        articulos_contrato1 = [
            ArticuloContrato(clave_articulo='AB-001', descripcion='Arroz Blanco Super Extra', unidad_medida='kg', precio_unitario=22.50, cant_maxima=5000, clasificacion='GRANOS'),
            ArticuloContrato(clave_articulo='FR-003', descripcion='Frijol Negro', unidad_medida='kg', precio_unitario=35.00, cant_maxima=8000, clasificacion='GRANOS'),
            ArticuloContrato(clave_articulo='LT-010', descripcion='Leche Entera UHT 1L', unidad_medida='pza', precio_unitario=25.80, cant_maxima=10000, clasificacion='LACTEOS'),
            ArticuloContrato(clave_articulo='EN-005', descripcion='Atún en Aceite 140g', unidad_medida='lata', precio_unitario=18.75, cant_maxima=12000, clasificacion='ENLATADOS')
        ]
        
        contrato1.articulos.extend(articulos_contrato1)
        session.add(contrato1)

        # Confirmar todos los cambios
        session.commit()
        print("Datos de prueba insertados correctamente.")

    except Exception as e:
        print(f"Ocurrió un error durante el sembrado de datos: {e}")
        session.rollback()
    finally:
        session.close()
        print("Sesión de base de datos cerrada.")


if __name__ == "__main__":
    print("--- Iniciando Script de Inicialización de Base de Datos ---")
    
    # 2. Crear la estructura de la base de datos
    create_database(engine)
    
    # 3. Crear una sesión y poblar los datos
    Session = sessionmaker(bind=engine)
    db_session = Session()
    seed_data(db_session)
    
    print("--- Script de Inicialización Finalizado ---")
