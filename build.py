# build.spec

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=['.'], # Asegura que la raíz del proyecto esté en el path de Python
    binaries=[],
    datas=[
        ('styles.qss', '.'), # Añade el archivo de estilos a la raíz del paquete
        ('assets', 'assets'), # Añade la carpeta de íconos
        ('expedientes_data', 'expedientes_data') # Añade el directorio de datos
    ],
    hiddenimports=[
        # Añadir todos los módulos que PyInstaller podría no encontrar
        'sigvcf.auth.services',
        'sigvcf.auth.viewmodels',
        'sigvcf.modules.almacen.services',
        'sigvcf.modules.almacen.viewmodels',
        'sigvcf.modules.nutricion.services',
        'sigvcf.modules.nutricion.viewmodels',
        'sigvcf.modules.juridico.services',
        'sigvcf.modules.juridico.viewmodels',
        'sigvcf.modules.administrativo.services',
        'sigvcf.modules.administrativo.viewmodels',
        'sigvcf.modules.financiero.services',
        'sigvcf.modules.financiero.viewmodels',
        'sigvcf.modules.proveedores.services',
        'sigvcf.modules.proveedores.viewmodels',
        # Plugins de PySide6 que a veces son necesarios
        'PySide6.QtSql',
        'PySide6.QtNetwork'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SIG-VCF', # El nombre del ejecutable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # MUY IMPORTANTE: Falso para aplicaciones GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico', # Ruta al ícono de la aplicación
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SIG-VCF_App', # El nombre de la carpeta de salida en 'dist'
)
``````sh
# build.sh
#!/bin/bash

echo "--- Limpiando compilaciones anteriores ---"
rm -rf build/
rm -rf dist/
# No eliminamos el spec porque es nuestro archivo de configuración principal
# rm -f *.spec

echo "--- Ejecutando PyInstaller con build.spec ---"
pyinstaller build.spec

echo "--- Proceso de construcción finalizado ---"
echo "La aplicación empaquetada se encuentra en la carpeta 'dist/SIG-VCF_App'."
echo "Para ejecutarla, navegue a ese directorio y corra el ejecutable 'SIG-VCF'."