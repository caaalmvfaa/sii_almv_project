### FILE: sigvcf/core/domain/models.py

import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Float,
    Text,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Rol(Base):
    __tablename__ = 'rol'
    id = Column(Integer, primary_key=True)
    nombre_rol = Column(String, nullable=False, unique=True)
    permisos = Column(JSON)
    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    rol_id = Column(Integer, ForeignKey('rol.id'))
    rol = relationship("Rol", back_populates="usuarios")
    programaciones_mensuales = relationship("ProgramacionMensual", back_populates="usuario")
    salidas_requerimiento = relationship("SalidaRequerimiento", back_populates="usuario_solicitante")
    entradas_bodega_recepcionadas = relationship("EntradaBodega", back_populates="recepcionista", foreign_keys='EntradaBodega.recepcionista_id')
    registros_contables_creados = relationship("RegistroContable", back_populates="contador", foreign_keys='RegistroContable.contador_id')

class Proveedor(Base):
    __tablename__ = 'proveedor'
    id = Column(Integer, primary_key=True)
    razon_social = Column(String, nullable=False)
    rfc = Column(String, nullable=False, unique=True)
    email_contacto = Column(String)
    contratos = relationship("Contrato", back_populates="proveedor")

class Contrato(Base):
    __tablename__ = 'contrato'
    id = Column(Integer, primary_key=True)
    codigo_licitacion = Column(String, nullable=False, unique=True)
    expediente_path = Column(String)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    proveedor_id = Column(Integer, ForeignKey('proveedor.id'))
    proveedor = relationship("Proveedor", back_populates="contratos")
    articulos = relationship("ArticuloContrato", back_populates="contrato")
    ordenes_de_compra = relationship("OrdenDeCompra", back_populates="contrato")
    reportes_incumplimiento = relationship("ReporteIncumplimiento", back_populates="contrato")

class ArticuloContrato(Base):
    __tablename__ = 'articulo_contrato'
    id = Column(Integer, primary_key=True)
    contrato_id = Column(Integer, ForeignKey('contrato.id'))
    clave_articulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    unidad_medida = Column(String, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    cant_maxima = Column(Integer, nullable=False)
    cant_consumida = Column(Integer, default=0)
    clasificacion = Column(String)
    contrato = relationship("Contrato", back_populates="articulos")
    programaciones_mensuales = relationship("ProgramacionMensual", back_populates="articulo_contrato")

class ProgramacionMensual(Base):
    __tablename__ = 'programacion_mensual'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id'))
    articulo_contrato_id = Column(Integer, ForeignKey('articulo_contrato.id'))
    mes_anho = Column(Date, nullable=False)
    cantidades_por_dia = Column(JSON, nullable=False)
    usuario = relationship("Usuario", back_populates="programaciones_mensuales")
    articulo_contrato = relationship("ArticuloContrato", back_populates="programaciones_mensuales")

class SalidaRequerimiento(Base):
    __tablename__ = 'salida_requerimiento'
    id = Column(Integer, primary_key=True)
    qr_id = Column(String, unique=True)
    usuario_solicitante_id = Column(Integer, ForeignKey('usuario.id'))
    fecha_generacion = Column(DateTime, default=datetime.datetime.utcnow)
    estado = Column(String, nullable=False)
    usuario_solicitante = relationship("Usuario", back_populates="salidas_requerimiento")

class OrdenDeCompra(Base):
    __tablename__ = 'orden_de_compra'
    id = Column(Integer, primary_key=True)
    contrato_id = Column(Integer, ForeignKey('contrato.id'))
    fecha_entrega_programada = Column(Date, nullable=False)
    estado = Column(String, nullable=False)
    contrato = relationship("Contrato", back_populates="ordenes_de_compra")
    entrada_bodega = relationship("EntradaBodega", back_populates="orden_de_compra", uselist=False)

class EntradaBodega(Base):
    __tablename__ = 'entrada_bodega'
    id = Column(Integer, primary_key=True)
    folio_rb = Column(String, unique=True)
    orden_compra_id = Column(Integer, ForeignKey('orden_de_compra.id'))
    fecha_recepcion = Column(DateTime, default=datetime.datetime.utcnow)
    factura_xml_path = Column(String)
    recepcionista_id = Column(Integer, ForeignKey('usuario.id'))
    orden_de_compra = relationship("OrdenDeCompra", back_populates="entrada_bodega")
    recepcionista = relationship("Usuario", back_populates="entradas_bodega_recepcionadas", foreign_keys=[recepcionista_id])
    registro_contable = relationship("RegistroContable", back_populates="entrada_bodega", uselist=False)

class ReporteIncumplimiento(Base):
    __tablename__ = 'reporte_incumplimiento'
    id = Column(Integer, primary_key=True)
    contrato_id = Column(Integer, ForeignKey('contrato.id'))
    tipo = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    descripcion = Column(Text)
    contrato = relationship("Contrato", back_populates="reportes_incumplimiento")

class RegistroContable(Base):
    __tablename__ = 'registro_contable'
    id = Column(Integer, primary_key=True)
    entrada_bodega_id = Column(Integer, ForeignKey('entrada_bodega.id'))
    asiento_contable = Column(String, nullable=False)
    fecha_contabilizacion = Column(DateTime, default=datetime.datetime.utcnow)
    contador_id = Column(Integer, ForeignKey('usuario.id'))
    entrada_bodega = relationship("EntradaBodega", back_populates="registro_contable")
    contador = relationship("Usuario", back_populates="registros_contables_creados", foreign_keys=[contador_id])