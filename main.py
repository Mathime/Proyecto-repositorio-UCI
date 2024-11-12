from datetime import datetime, timezone
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, Form, Depends, HTTPException,Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
import models
from models import Usuario, Curso, Carrera, Materia, Proyecto, FacultadProyecto, Facultad, Auditoria
from starlette.templating import Jinja2Templates
from database import get_db, Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
from fastapi import Depends
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
from starlette.middleware.sessions import SessionMiddleware
from models import proyectos_estudiantes
app = FastAPI()
ADMIN_USERNAME = "20241988"
ADMIN_PASSWORD = "admin123"
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory='static'), name="static") # type: ignore

# Añadir un middleware para gestionar sesiones
app.add_middleware(SessionMiddleware, secret_key="mysecret")

@app.get("/dashboard")
async def dashboard(request: Request):
    # Verificar si el usuario está autenticado
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    return {"message": "Bienvenido al dashboard"}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    # Obtener todos los proyectos
    proyectos = db.query(Proyecto).all()
    return templates.TemplateResponse("vista_global.html", {
        "request": request,
        "proyectos": proyectos
    })
@app.get("/proyecto/detalle/{proyecto_id}", response_class=HTMLResponse)
async def detalle_proyecto(proyecto_id: int, request: Request, db: Session = Depends(get_db)):
    # Buscar el proyecto por ID
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == proyecto_id).first()
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Obtener el docente y los estudiantes relacionados al proyecto
    docente = proyecto.docente
    estudiantes = proyecto.estudiantes

    return templates.TemplateResponse("detalle_proyecto.html", {
        "request": request,
        "proyecto": proyecto,
        "docente": docente,
        "estudiantes": estudiantes,
        "fecha_asignacion": proyecto.facultades_relaciones[0].fecha_asignacion if proyecto.facultades_relaciones else None
    })
@app.get("/actividades_proyectos_docente", response_class=HTMLResponse)
async def actividades_proyectos_docente(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]

    # Verificar si el usuario es un docente
    docente = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Docente").first()
    if not docente:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    # Ajustar la consulta para usar select_from()
    actividades = db.query(Auditoria).join(Proyecto, Proyecto.idProyecto == Auditoria.proyecto_id).filter(
        Proyecto.docente_id == docente.idusuarios
    ).select_from(Auditoria).order_by(Auditoria.fecha_auditoria.desc()).all()

    return templates.TemplateResponse("actividades_proyectos_docente.html", {
        "request": request,
        "actividades": actividades
    })


@app.get("/auditoria", response_class=HTMLResponse)
async def mostrar_auditorias(request: Request, db: Session = Depends(get_db)):
    auditorias = db.query(Auditoria).all()
    return templates.TemplateResponse("vista_auditoria.html", {
        "request": request,
        "auditorias": auditorias
    })

@app.get("/perfil", response_class=HTMLResponse)
async def ver_perfil(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]
    alumno = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Estudiante").first()

    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    return templates.TemplateResponse("editar_perfilal.html", {
        "request": request,
        "usuario": alumno
    })
@app.get("/perfildoc", response_class=HTMLResponse)
async def ver_perfil1(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]
    docente = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Docente").first()

    if not docente:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    return templates.TemplateResponse("editar_perfildoc.html", {
        "request": request,
        "usuario": docente
    })



@app.get("/logout")
async def logout(request: Request):
    # Eliminar la sesión del usuario
    request.session.clear()
    
    # Redirigir al usuario a la página de inicio de sesión
    return RedirectResponse(url="/login", status_code=302)

@app.get("/admin", response_class=HTMLResponse)
def inicio(request:Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.get("/proyectos_estudiantes", response_class=HTMLResponse)
async def proyectos_estudiantes1(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]
    estudiante = db.query(Usuario).filter(
        Usuario.idusuarios == usuario_id,
        Usuario.rol_usuario == "Estudiante"
    ).first()

    if not estudiante:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    # Obtener los proyectos asociados al estudiante
    proyectos = db.query(Proyecto).join(proyectos_estudiantes).filter(
        proyectos_estudiantes.c.estudiante_id == estudiante.idusuarios
    ).all()

    if not proyectos:
        print("No se encontraron proyectos para este estudiante.")  # Depuración

    return templates.TemplateResponse("estudiante_proyectos.html", {
        "request": request,
        "proyectos": proyectos,  # Asegúrate de que esta variable esté pasando correctamente
        "estudiante": estudiante
    })

@app.get("/proyecto/actualizar_estudiante/{proyecto_id}", response_class=HTMLResponse)
async def mostrar_formulario_actualizar_proyecto(
    proyecto_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    print("Proyecto ID recibido:", proyecto_id)
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]

    # Verificar si el usuario es un estudiante
    estudiante = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Estudiante").first()
    if not estudiante:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")


    # Buscar el proyecto en base al estudiante asignado y al ID del proyecto
    proyecto = db.query(Proyecto).join(proyectos_estudiantes).filter(
        Proyecto.idProyecto == proyecto_id,
        proyectos_estudiantes.c.estudiante_id == estudiante.idusuarios
    ).first()

    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado o no autorizado para este estudiante")

    return templates.TemplateResponse("estudiante_proyectos.html", {
        "request": request,
        "proyecto": proyecto
    })


@app.get("/proyectos_docentes", response_class=HTMLResponse)
async def proyectos_asignados(request: Request, db: Session = Depends(get_db)):
    # Verificar si el usuario está autenticado
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]
    
    # Verificar si el usuario es un docente
    docente = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Docente").first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado o no autorizado")

    # Obtener solo los proyectos asignados al docente autenticado
    proyectos = db.query(Proyecto).filter(Proyecto.docente_id == docente.idusuarios).all()

    # Obtener la lista de estudiantes (opcional, si es necesario)
    estudiantes = db.query(Usuario).filter(Usuario.rol_usuario == "Estudiante").all()

    return templates.TemplateResponse("docente_proyectos.html", {
        "request": request,
        "proyectos": proyectos,
        "estudiantes": estudiantes
    })

@app.get("/vista_docente", response_class=HTMLResponse)
async def vista_asignaralumnos(request: Request, db: Session = Depends(get_db)):
    # Verificar si el usuario está autenticado
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]

    # Obtener el docente autenticado basado en la sesión
    docente = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Docente").first()

    if not docente:
        raise HTTPException(status_code=403, detail="Acceso no autorizado o el usuario no es un docente")

    # Proyectos asignados al docente
    proyectos = db.query(Proyecto).filter(Proyecto.docente_id == docente.idusuarios).all()

    # Todos los estudiantes
    estudiantes = db.query(Usuario).filter(Usuario.rol_usuario == "Estudiante").all()

    return templates.TemplateResponse("vista_docente.html", {
        "request": request,
        "docente": docente,
        "proyectos": proyectos,
        "estudiantes": estudiantes
    })



@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/vista_alumnos", response_class=HTMLResponse)
async def vista_alumno(request: Request, db: Session = Depends(get_db)):
    # Verificar si el usuario está autenticado
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")

    usuario_id = request.session["user_id"]

    # Obtener el alumno autenticado basado en la sesión
    alumno = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Estudiante").first()

    if not alumno:
        raise HTTPException(status_code=403, detail="Acceso no autorizado o el usuario no es un estudiante")

    # Obtener los proyectos asociados al alumno
    proyectos = db.query(Proyecto).join(proyectos_estudiantes).filter(proyectos_estudiantes.c.estudiante_id == alumno.idusuarios).all()

    return templates.TemplateResponse("vista_alumnos.html", {
        "request": request,
        "alumno": alumno,
        "proyectos": proyectos
    })





##
@app.get("/facultades", response_class=HTMLResponse)
def leer_facultades(request: Request, db: Session = Depends(get_db)):
    facultades = db.query(models.Facultad).all()
    return templates.TemplateResponse("lista_facu.html", {"request": request, "facultades": facultades})


@app.get("/register", response_class=HTMLResponse)
def mostrar_formulario_registro(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/registrar_facu", response_class=HTMLResponse)
def mostrar_formulario_facultad(request: Request):
    return templates.TemplateResponse("registrar_facultad.html", {"request": request})


@app.get("/carreras", response_class=HTMLResponse)
def mostrar_formulario_carrera(request: Request, mensaje: str = None, db: Session = Depends(get_db)):
    facultades = db.query(models.Facultad).all()
    return templates.TemplateResponse("registrar_carrera.html", {"request": request, "facultades": facultades, "mensaje": mensaje})

@app.get("/registrar_curso", response_class=HTMLResponse)
def mostrar_formulario_curso(request: Request, db: Session = Depends(get_db)):
    carreras = db.query(Carrera).all()  # Obtener todas las carreras disponibles
    return templates.TemplateResponse("registrar_curso.html", {"request": request, "carreras": carreras})

@app.get("/registrar_materia", response_class=HTMLResponse)
async def mostrar_formulario_materia(request: Request, db: Session = Depends(get_db)):
    carreras = db.query(Carrera).all()
    return templates.TemplateResponse("registrar_materia.html", {"request": request, "carreras": carreras})

@app.get("/proyecto/list", response_class=HTMLResponse)
async def list_proyectos(request: Request, db: Session =
Depends(get_db)):
    proyectos = db.query(Proyecto).all()
    return templates.TemplateResponse("proyecto_list.html",
{"request": request, "proyectos": proyectos})

@app.get("/proyecto/registrar", response_class=HTMLResponse)
def registrar_proyecto(request: Request, db: Session = Depends(get_db)):
    facultades = db.query(Facultad).all()
    docentes = db.query(Usuario).filter(Usuario.rol_usuario == "Docente").all()
    cursos = db.query(Curso).all()
    return templates.TemplateResponse("registrar_proyecto.html", {
        "request": request,
        "facultades": facultades,
        "docentes": docentes,
        "cursos": cursos
        
    })

@app.get("/docente/proyectos", response_class=HTMLResponse)
async def proyectos_docente(request: Request, db: Session = Depends(get_db)):
    # Verificar si el usuario está autenticado mediante la sesión
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # Obtener el ID del usuario desde la sesión
    usuario_id = request.session["user_id"]

    # Verificar si el usuario es un docente
    docente = db.query(Usuario).filter(Usuario.idusuarios == usuario_id, Usuario.rol_usuario == "Docente").first()
    if not docente:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    # Obtener los proyectos asignados al docente
    proyectos = db.query(Proyecto).filter(Proyecto.docente_id == docente.idusuarios).all()
    estudiantes = db.query(Usuario).filter(Usuario.rol_usuario == "Estudiante").all()

    return templates.TemplateResponse("docente_proyectos.html", {
        "request": request,
        "proyectos": proyectos,
        "estudiantes": estudiantes
    })

@app.post("/auditoria/registrar")
async def registrar_auditoria(
    descripcion: str,
    usuario_id: int,
    db: Session = Depends(get_db)
):
    # Si el usuario es admin, cambia el `usuario_id` al ID constante de `admin`

    nueva_auditoria = Auditoria(
        fecha_auditoria=datetime.utcnow(),
        descripcion_auditoria=descripcion,
        usuario_id=usuario_id
    )
    db.add(nueva_auditoria)
    db.commit()
    return {"message": "Auditoría registrada exitosamente."}


@app.post("/proyecto/editar_descripcion/{proyecto_id}")
async def editar_descripcion_proyecto(
    proyecto_id: int,
    request: Request,  # Argumento obligatorio primero
    descripcion: str = Form(...),  # Argumento con valor por defecto después
    db: Session = Depends(get_db)
):
    # Buscar el proyecto por ID
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == proyecto_id).first()
    

    # Verificar si el proyecto existe
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    print("Contenido de la sesión antes de redirigir:", request.session)


    # Actualizar la descripción
    proyecto.descripcion = descripcion
    db.commit()

    # Redirigir a la vista de gestión de proyectos del docente
    return RedirectResponse(url="/docente/proyectos", status_code=302)


@app.post("/register")
async def registrar_usuario(
    request: Request,
    nombre: str = Form(...),
    apellido: str = Form(...),
    ci: str = Form(...),
    telefono: str = Form(...),
    direccion: str = Form(...),
    rol: str = Form(...),
    correo: str = Form(...),
    password: str = Form(...),
    matricula: Optional[str] = Form(None),  
    db: Session = Depends(get_db)
):
    nuevo_usuario = Usuario(
        nombre_usuario=nombre,
        apellido_usuario=apellido,
        documento_usuario=ci,
        telefono_usuario=telefono,
        direccion_usuario=direccion,
        rol_usuario=rol,
        correo_usuario=correo,
        contra=password  
    )
    
    if rol == "Estudiante" and matricula:
        nuevo_usuario.matricula_usuario = matricula

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    await registrar_auditoria(
        descripcion=f"Usuario '{nombre} {apellido}' registrado",
        usuario_id=request.session.get("user_id"),
        db=db
    )
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/proyecto/asignar_estudiantes/{proyecto_id}")
async def asignar_estudiantes_proyecto(
    proyecto_id: int,
    estudiantes_ids: List[int] = Form(...),
    db: Session = Depends(get_db)
):
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    estudiantes = db.query(Usuario).filter(Usuario.idusuarios.in_(estudiantes_ids)).all()
    proyecto.estudiantes.extend(estudiantes)
    db.commit()

    return RedirectResponse(url="/docente/proyectos", status_code=302)

import os
@app.post("/proyecto/actualizar_estudiante/{proyecto_id}", response_class=HTMLResponse)
async def actualizar_proyecto_estudiante(
    request: Request,
    proyecto_id: int,
    descripcion: str = Form(...),
    fotos: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    proyecto = db.query(Proyecto).filter(Proyecto.idProyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    if descripcion:
        proyecto.descripcion = descripcion

    # Verificar y crear el directorio si no existe
    directorio_proyecto = f"static/proyectos/{proyecto_id}"
    if not os.path.exists(directorio_proyecto):
        os.makedirs(directorio_proyecto)

    # Guardar las fotos
    rutas_fotos = []
    for foto in fotos:
        ruta_foto = os.path.join(directorio_proyecto, foto.filename)
        with open(ruta_foto, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        rutas_fotos.append(ruta_foto)

    # Actualizar la ruta de fotos en la base de datos (agregar nuevas fotos a las existentes)
    if proyecto.ruta_foto:
        proyecto.ruta_foto += ";" + ";".join(rutas_fotos)
    else:
        proyecto.ruta_foto = ";".join(rutas_fotos)

    db.commit()

    # Pasar un mensaje de éxito y los proyectos actualizados al contexto de la plantilla
    return templates.TemplateResponse("estudiante_proyectos.html", {
        "request": request,
        "proyectos": [proyecto],
        "success_message": "Actualización exitosa"
    })


@app.get("/docentes", response_class=HTMLResponse)
def listar_docentes(request: Request, db: Session = Depends(get_db)):
    docentes = db.query(Usuario).filter(Usuario.rol_usuario == 'Docente').all()

    return templates.TemplateResponse("docentes.html", {"request": request, "usuarios": docentes})

@app.get("/alumnos", response_class=HTMLResponse)
def listar_estudiantes(request: Request, db: Session = Depends(get_db)):
    estudiantes = db.query(Usuario).filter(Usuario.rol_usuario == 'Estudiante').all()

    return templates.TemplateResponse("alumnos.html", {"request": request, "usuarios": estudiantes})
@app.get("/edit_user/{user_id}", response_class=HTMLResponse)
async def mostrar_formulario_editar(request: Request, user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.idusuarios == user_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return templates.TemplateResponse("editar_alumnos.html", {"request": request, "usuario": usuario})
@app.get("/edit_user1/{user_id}", response_class=HTMLResponse)
async def mostrar_formulario_edita(request: Request, user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.idusuarios == user_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return templates.TemplateResponse("edit_user.html", {"request": request, "usuario": usuario})
@app.post("/edit_user/{user_id}")
async def editar_usuario(
    request:Request,
    user_id: int,
    nombre: str = Form(...),
    apellido: str = Form(...),
    telefono: str = Form(...),
    matricula: str = Form(...),
    direccion: str = Form(...),
    ci: str = Form(...),  
    rol: str = Form(...),
    correo: str = Form(...),
    password: str = Form(None),  
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.idusuarios == user_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.nombre_usuario = nombre
    usuario.apellido_usuario = apellido
    usuario.telefono_usuario = telefono
    usuario.direccion_usuario = direccion
    usuario.matricula_usuario = matricula
    usuario.rol_usuario = rol
    usuario.correo_usuario = correo
    usuario.documento_usuario = ci  
    if password:  
        usuario.contra = password

    db.commit()
    await registrar_auditoria(
        descripcion=f"Usuario '{nombre} {apellido}' editado",
        usuario_id=request.session.get("user_id"),
        db=db
    )
    if rol == 'Docente':
        return RedirectResponse(url="/docentes", status_code=302)
    elif rol == 'Estudiante':
        return RedirectResponse(url="/alumnos", status_code=302)
    else:
        raise HTTPException(status_code=400, detail="Rol no válido")
    
@app.post("/editar_alumnos/{user_id}")
async def editar_usuario1(
    user_id: int,
    request: Request,  # Para acceder a la sesión
    nombre: str = Form(...),
    apellido: str = Form(...),
    telefono: str = Form(...),
    direccion: str = Form(...),
    correo: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verificar si el usuario está autenticado
    if "user_id" not in request.session or request.session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    usuario = db.query(Usuario).filter(Usuario.idusuarios == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actualizar los datos del usuario
    usuario.nombre_usuario = nombre
    usuario.apellido_usuario = apellido
    usuario.telefono_usuario = telefono
    usuario.direccion_usuario = direccion
    usuario.correo_usuario = correo

    db.commit()
    return RedirectResponse(url="/vista_alumnos", status_code=302)

@app.post("/editar_docentes/{user_id}")
async def editar_docente(
    user_id: int,
    request: Request,  # Para acceder a la sesión
    nombre: str = Form(...),
    apellido: str = Form(...),
    telefono: str = Form(...),
    direccion: str = Form(...),
    correo: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verificar si el usuario está autenticado y si es el mismo que intenta editar su perfil
    if "user_id" not in request.session or request.session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    # Buscar al docente en la base de datos
    usuario = db.query(Usuario).filter(Usuario.idusuarios == user_id, Usuario.rol_usuario == "Docente").first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    # Actualizar los datos del usuario
    usuario.nombre_usuario = nombre
    usuario.apellido_usuario = apellido
    usuario.telefono_usuario = telefono
    usuario.direccion_usuario = direccion
    usuario.correo_usuario = correo

    db.commit()
    return RedirectResponse(url="/vista_docente", status_code=302)



@app.post("/delete_user/{user_id}")
async def eliminar_usuario(request:Request,user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.idusuarios == user_id).first()  
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nombre_usuario = f"{usuario.nombre_usuario} {usuario.apellido_usuario}"

    db.delete(usuario)
    db.commit()

    # Registrar auditoría
    await registrar_auditoria(
        descripcion=f"Usuario '{nombre_usuario}' eliminado",
        usuario_id=request.session.get("user_id") ,
        db=db
    )

    return RedirectResponse(url="/admin", status_code=302)

@app.post("/registrar_facu")
def registrar_facultad(facultad: str = Form(...), db: Session = Depends(get_db)):
    nueva_facu = models.Facultad(nombre_facultad=facultad)
    db.add(nueva_facu)
    db.commit()
    db.refresh(nueva_facu)
    return RedirectResponse(url="/admin", status_code=302)
@app.post("/carreras")
def registrar_carrera(
    nombre_carrera: str = Form(...),
    facultad_id: int = Form(...),
    db: Session = Depends(get_db)
):
    nueva_carrera = models.Carrera(
        nombre_carrera=nombre_carrera,
        facultades_idfacultades=facultad_id
    )
    
    db.add(nueva_carrera)
    db.commit()
    db.refresh(nueva_carrera)
    url = "/carreras?mensaje=Registro%20exitoso"
    return RedirectResponse(url=url, status_code=302)
@app.post("/registrar_curso")
async def registrar_curso(request: Request, nombre_curso: str = Form(...), carrera_id: int = Form(...), db: Session = Depends(get_db)):
    nuevo_curso = Curso(
        nombre_curso=nombre_curso,
        carreras_idCarreras=carrera_id
    )
    db.add(nuevo_curso)
    db.commit()
    db.refresh(nuevo_curso)
    
    carreras = db.query(Carrera).all()

    return templates.TemplateResponse("registrar_curso.html", {
        "request": request,
        "success_message": "El curso ha sido registrado exitosamente.",
        "carreras": carreras
    })
@app.post("/registrar_materia")
async def registrar_materia(
    nombre_materia: str = Form(...),
    cursos_idCursos: int = Form(...),
    db: Session = Depends(get_db)
):
    nueva_materia = Materia(
        nombre_materia=nombre_materia,
        cursos_idCursos=cursos_idCursos
    )
    db.add(nueva_materia)
    db.commit()
    db.refresh(nueva_materia)
    
    return RedirectResponse(url="/admin", status_code=302)
@app.post("/proyecto/create")
async def create_proyecto(
    request: Request,
    nombreProyecto: str = Form(...),
    facultades_ids: List[int] = Form(...),
    docente_id: int = Form(...),
    curso_id: int = Form(...),
    descripcion: str = Form(...),
    fecha_asignacion: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # Crear el proyecto con el docente asignado y curso
        nuevo_proyecto = Proyecto(
            nombreProyecto=nombreProyecto,
            descripcion=descripcion,
            docente_id=docente_id,
            curso_id=curso_id  # Asegúrate de que el modelo Proyecto tenga el campo curso_id
        )
        db.add(nuevo_proyecto)
        db.commit()
        db.refresh(nuevo_proyecto)
        await registrar_auditoria(
            descripcion=f"Proyecto '{nombreProyecto}' creado por el usuario {request.session['user_id']}",
            usuario_id=request.session.get("user_id") ,
            db=db
        )
        if fecha_asignacion:
            fecha_asignacion = datetime.strptime(fecha_asignacion, "%Y-%m-%dT%H:%M")

        # Crear las relaciones con las facultades
        for facultad_id in facultades_ids:
            facultad_proyecto_relacion = FacultadProyecto(
                facultad_id=facultad_id,
                proyecto_id=nuevo_proyecto.idProyecto,
                descripcion=descripcion,
                fecha_asignacion=fecha_asignacion or datetime.utcnow()
            )
            db.add(facultad_proyecto_relacion)

        db.commit()

        return templates.TemplateResponse("registrar_proyecto.html", {
            "request": request,
            "success_message": "El proyecto ha sido registrado exitosamente."
        })

    except Exception as e:
        db.rollback()  # Revertir los cambios si ocurre un error
        return templates.TemplateResponse("registrar_proyecto.html", {
            "request": request,
            "error_message": f"Error al registrar el proyecto: {str(e)}"
        })


@app.post("/login")
async def logearse(
    request: Request,
    ci: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verificar si es el Admin
    if ci == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session['user_id'] = 'admin'  # Guardar un identificador para el admin
        request.session['rol_usuario'] = 'Admin'  # Guardar el rol del admin
        return RedirectResponse(url="/admin", status_code=302)
    
    # Verificar en la base de datos
    usuario = db.query(Usuario).filter(Usuario.documento_usuario == ci).first()

    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    # Comparar la contraseña directamente en texto plano (mejor usar bcrypt o similar)
    if password != usuario.contra:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # Agregar los datos del usuario a la sesión
    request.session['user_id'] = usuario.idusuarios
    request.session['nombre_usuario'] = usuario.nombre_usuario
    request.session['rol_usuario'] = usuario.rol_usuario

    # Redirigir según el rol del usuario
    if usuario.rol_usuario == "Docente":
        return RedirectResponse(url="/vista_docente", status_code=302)
    elif usuario.rol_usuario == "Estudiante":
        return RedirectResponse(url="/vista_alumnos", status_code=302)
    else:
        raise HTTPException(status_code=403, detail="Rol no permitido")

    
