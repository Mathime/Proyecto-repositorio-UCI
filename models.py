from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    idusuarios = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(45))
    apellido_usuario = Column(String(50))
    telefono_usuario = Column(String(45))
    documento_usuario = Column(String(45))
    direccion_usuario = Column(String(45))
    matricula_usuario = Column(String(45))
    rol_usuario = Column(String(45))
    contra = Column(String(50))
    correo_usuario = Column(String(50))

    auditorias = relationship("Auditoria", back_populates="usuario")


class Auditoria(Base):
    __tablename__ = "auditoria"
    
    idauditoria = Column(Integer, primary_key=True, index=True)
    fecha_auditoria = Column(DateTime)
    descripcion_auditoria = Column(String(45))
    usuario_id = Column(Integer, ForeignKey("usuarios.idusuarios"))

    usuario = relationship("Usuario", back_populates="auditorias")


class Facultad(Base):
    __tablename__ = "facultades"
    
    idfacultades = Column(Integer, primary_key=True, index=True)
    nombre_facultad = Column(String(45))
    
    carreras = relationship("Carrera", back_populates="facultad")
    proyectos_relaciones = relationship("FacultadProyecto",
    back_populates="facultad")

class Carrera(Base):
    __tablename__ = "carreras"
    
    idCarreras = Column(Integer, primary_key=True, index=True)
    nombre_carrera = Column(String(45))
    facultades_idfacultades = Column(Integer, ForeignKey("facultades.idfacultades"))
    
    facultad = relationship("Facultad", back_populates="carreras")
    cursos = relationship("Curso", back_populates="carrera")


class Curso(Base):
    __tablename__ = "cursos"
    
    idCursos = Column(Integer, primary_key=True, index=True)
    nombre_curso = Column(String(45))
    carreras_idCarreras = Column(Integer, ForeignKey("carreras.idCarreras"))
    
    carrera = relationship("Carrera", back_populates="cursos")
    materias = relationship("Materia", back_populates="curso")


class Materia(Base):
    __tablename__ = "materias"
    
    idMaterias = Column(Integer, primary_key=True, index=True)
    nombre_materia = Column(String(45))
    cursos_idCursos = Column(Integer, ForeignKey("cursos.idCursos"))
    
    curso = relationship("Curso", back_populates="materias")

class Proyecto(Base):
    __tablename__ = 'proyecto'
    idProyecto = Column(Integer, primary_key=True, index=True)
    nombreProyecto = Column(String(255), nullable=False)
    facultades_relaciones = relationship("FacultadProyecto",
    back_populates="proyecto")

class FacultadProyecto(Base):
    __tablename__ = 'facultad_proyecto'
    
    facultad_id = Column(Integer, ForeignKey('facultades.idfacultades'), primary_key=True)
    proyecto_id = Column(Integer, ForeignKey('proyecto.idProyecto'), primary_key=True)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    descripcion = Column(String(255))
    
    facultad = relationship("Facultad", back_populates="proyectos_relaciones")
    proyecto = relationship("Proyecto", back_populates="facultades_relaciones")
