from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from database import Base

# Tabla de asociación para la relación de muchos a muchos entre Proyecto y Usuario (para estudiantes)
proyectos_estudiantes = Table(
    'proyectos_estudiantes', Base.metadata,
    Column('proyecto_id', Integer, ForeignKey('proyecto.idProyecto'), primary_key=True),
    Column('estudiante_id', Integer, ForeignKey('usuarios.idusuarios'), primary_key=True)
)

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
     # Relación con proyectos dirigidos (si el usuario es un docente)
    proyectos_dirigidos = relationship("Proyecto", back_populates="docente", foreign_keys="Proyecto.docente_id")
    
    # Relación con proyectos en los que es estudiante
    proyectos = relationship("Proyecto", secondary=proyectos_estudiantes, back_populates="estudiantes")


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
    descripcion = Column(String(255), nullable=True)  # Para descripciones adicionales
    ruta_foto = Column(String(255), nullable=True)  # Ruta de la foto del proyecto

    # Relación con el docente asignado
    docente_id = Column(Integer, ForeignKey("usuarios.idusuarios"))
    docente = relationship("Usuario", back_populates="proyectos_dirigidos", foreign_keys=[docente_id])

    # Relación con los estudiantes asignados
    estudiantes = relationship("Usuario", secondary=proyectos_estudiantes, back_populates="proyectos")

    # Relación con facultades
    facultades_relaciones = relationship("FacultadProyecto", back_populates="proyecto")

class FacultadProyecto(Base):
    __tablename__ = 'facultad_proyecto'
    
    facultad_id = Column(Integer, ForeignKey('facultades.idfacultades'), primary_key=True)
    proyecto_id = Column(Integer, ForeignKey('proyecto.idProyecto'), primary_key=True)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    descripcion = Column(String(255))
    
    facultad = relationship("Facultad", back_populates="proyectos_relaciones")
    proyecto = relationship("Proyecto", back_populates="facultades_relaciones")
