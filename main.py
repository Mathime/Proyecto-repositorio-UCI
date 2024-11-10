from datetime import datetime, timezone
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, Form, Depends, HTTPException,Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
import models
from models import Usuario, Curso, Carrera, Materia, Proyecto, FacultadProyecto, Facultad
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
    docente = db.query(Usuario).filter(Usuario.rol_usuario == "Docente").first()  # Ajusta esto según tu autenticación
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    proyectos = db.query(Proyecto).filter(Proyecto.docente_id == docente.idusuarios).all()
    estudiantes = db.query(Usuario).filter(Usuario.rol_usuario == "Estudiante").all()

    return templates.TemplateResponse("docente_proyectos.html", {
        "request": request,
        "proyectos": proyectos,
        "estudiantes": estudiantes
    })

@app.get("/vista_docente", response_class=HTMLResponse)
async def vista_asignaralumnos(request: Request, db: Session = Depends(get_db)):
    docente = db.query(Usuario).filter(Usuario.rol_usuario == "Docente").first()  # Ajusta esto para el docente autenticado
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
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
    # Obtén al primer usuario con el rol de "Estudiante" (ajusta esto según tu lógica)
    alumno = db.query(Usuario).filter(Usuario.rol_usuario == "Estudiante").first()
    
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

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

    return templates.TemplateResponse("registrar_proyecto.html", {
        "request": request,
        "facultades": facultades,
        "docentes": docentes
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
    rutas_fotos = []
    for foto in fotos:
        ruta_foto = f"static/proyectos/{proyecto_id}/{foto.filename}"
        with open(ruta_foto, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        rutas_fotos.append(ruta_foto)

    # Actualizar la ruta de fotos en la base de datos (agregar nuevas fotos a las existentes)
    if proyecto.ruta_foto:
        print("Rutas de imágenes a mostrar:", proyecto.ruta_foto.split(';'))

    else:
        proyecto.ruta_foto = ";".join(rutas_fotos)

    db.commit()

    # Consultar los proyectos asociados al estudiante nuevamente
    usuario_id = request.session.get("user_id")
    estudiante = db.query(Usuario).filter(
        Usuario.idusuarios == usuario_id,
        Usuario.rol_usuario == "Estudiante"
    ).first()

    proyectos_actualizados = db.query(Proyecto).join(proyectos_estudiantes).filter(
        proyectos_estudiantes.c.estudiante_id == usuario_id
    ).all()

    # Pasar un mensaje de éxito y los proyectos actualizados al contexto de la plantilla
    return templates.TemplateResponse("estudiante_proyectos.html", {
        "request": request,
        "proyectos": proyectos_actualizados,
        "estudiante": estudiante,
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
    if rol == 'Docente':
        return RedirectResponse(url="/docentes", status_code=302)
    elif rol == 'Estudiante':
        return RedirectResponse(url="/alumnos", status_code=302)
    else:
        raise HTTPException(status_code=400, detail="Rol no válido")
@app.post("/delete_user/{user_id}")
async def eliminar_usuario(user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.idusuarios == user_id).first()  
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
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
    descripcion: str = Form(...),
    fecha_asignacion: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # Crear el proyecto con el docente asignado
        nuevo_proyecto = Proyecto(
            nombreProyecto=nombreProyecto,
            descripcion=descripcion,
            docente_id=docente_id
        )
        db.add(nuevo_proyecto)
        db.commit()
        db.refresh(nuevo_proyecto)
        
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
        return RedirectResponse(url="/admin", status_code=302)
    
    # Verificar en la base de datos
    usuario = db.query(Usuario).filter(Usuario.documento_usuario == ci).first()

    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    # Comparar la contraseña directamente en texto plano
    if password != usuario.contra:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    request.session['user_id'] = usuario.idusuarios  # Agregar el user_id
    request.session['nombre_usuario'] = usuario.nombre_usuario

    # Redirigir según el rol del usuario
    if usuario.rol_usuario == "Docente":
        return RedirectResponse(url="/vista_docente", status_code=302)
    elif usuario.rol_usuario == "Estudiante":
        return RedirectResponse(url="/vista_alumnos", status_code=302)
    else:
        raise HTTPException(status_code=403, detail="Rol no permitido")

    
