# sigvcf/modules/almacen/views_3d.py
import logging
from PySide6.QtCore import QSize
from PySide6.QtGui import QVector3D, QColor
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DRender import Qt3DRender
from PySide6.Qt3DExtras import Qt3DExtras

from sigvcf.modules.almacen.dto import StockStatusDTO

logger = logging.getLogger(__name__)

class Warehouse3DView(Qt3DExtras.Qt3DWindow):
    """
    Ventana de Qt3D que renderiza una visualización del inventario del almacén.
    """
    def __init__(self):
        super().__init__()
        self.setTitle("Visualización 3D del Almacén")
        self.defaultFrameGraph().setClearColor(QColor.fromRgbF(0.1, 0.1, 0.15, 1.0))

        # --- Escena Raíz ---
        self.root_entity = Qt3DCore.QEntity()
        self.stock_items_root = Qt3DCore.QEntity(self.root_entity) # Entidad para agrupar items de stock

        # --- Cámara ---
        camera_entity = self.camera()
        camera_entity.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 1000.0)
        camera_entity.setPosition(QVector3D(0, 10, 25.0))
        camera_entity.setUpVector(QVector3D(0, 1, 0))
        camera_entity.setViewCenter(QVector3D(0, 0, 0))

        # --- Controlador de Cámara ---
        cam_controller = Qt3DExtras.QOrbitCameraController(self.root_entity)
        cam_controller.setLinearSpeed(20.0)
        cam_controller.setLookSpeed(180.0)
        cam_controller.setCamera(camera_entity)

        # --- Luz ---
        light_entity = Qt3DCore.QEntity(self.root_entity)
        light = Qt3DRender.QPointLight(light_entity)
        light.setColor(QColor("white"))
        light.setIntensity(1)
        light_transform = Qt3DCore.QTransform(light_entity)
        light_transform.setTranslation(QVector3D(0, 20, 20))
        light_entity.addComponent(light)
        light_entity.addComponent(light_transform)

        # --- Materiales y Mallas reutilizables ---
        self.shelf_material = Qt3DExtras.QPhongMaterial(self.root_entity)
        self.shelf_material.setDiffuse(QColor.fromRgbF(0.4, 0.4, 0.4, 1.0))
        self.shelf_mesh = Qt3DExtras.QCuboidMesh()
        self.shelf_mesh.setXExtent(8)
        self.shelf_mesh.setYExtent(0.2)
        self.shelf_mesh.setZExtent(2)

        self.item_material = Qt3DExtras.QPhongMaterial(self.root_entity)
        self.item_material.setDiffuse(QColor.fromRgbF(0.2, 0.5, 0.8, 1.0))
        self.item_mesh = Qt3DExtras.QCuboidMesh() # Tamaño 1x1x1 por defecto

        self.setRootEntity(self.root_entity)

    def update_stock(self, stock_data: list[StockStatusDTO]):
        """
        Limpia y redibuja la escena 3D con los datos de stock actualizados.
        """
        logger.info(f"Actualizando la vista 3D con {len(stock_data)} tipos de artículos.")
        
        # Limpiar items de stock anteriores
        self.stock_items_root.setParent(None)
        del self.stock_items_root
        self.stock_items_root = Qt3DCore.QEntity(self.root_entity)

        # Posiciones iniciales para dibujar las estanterías
        x_pos, z_pos = -15, -10
        row_count = 0

        for i, stock_item in enumerate(stock_data):
            # --- Crear Estantería ---
            shelf_entity = Qt3DCore.QEntity(self.stock_items_root)
            shelf_transform = Qt3DCore.QTransform()
            shelf_transform.setTranslation(QVector3D(x_pos, 0, z_pos))
            shelf_entity.addComponent(self.shelf_mesh)
            shelf_entity.addComponent(self.shelf_material)
            shelf_entity.addComponent(shelf_transform)

            # --- Crear Items de Stock (Cajas) ---
            # Simulación: apilar cajas en la estantería
            items_per_row = 7
            item_x_start = x_pos - 3.5
            item_z = z_pos
            
            # Normalizar la cantidad para que no sea excesiva visualmente
            display_quantity = min(stock_item.stock_disponible // 10, 50) # 1 caja por cada 10 unidades, max 50 cajas

            for j in range(display_quantity):
                item_entity = Qt3DCore.QEntity(shelf_entity) # Hijo de la estantería
                item_transform = Qt3DCore.QTransform()
                
                row = j // items_per_row
                col = j % items_per_row
                
                item_y = 0.1 + 1.05 * row # 0.1 para estar sobre la estantería, 1.05 por altura de caja
                item_x = item_x_start + 1.05 * col

                item_transform.setTranslation(QVector3D(item_x, item_y, item_z))
                
                item_entity.addComponent(self.item_mesh)
                item_entity.addComponent(self.item_material)
                item_entity.addComponent(item_transform)

            # Actualizar posición para la siguiente estantería
            x_pos += 10
            row_count += 1
            if row_count >= 4: # 4 estanterías por fila
                row_count = 0
                x_pos = -15
                z_pos += 5

