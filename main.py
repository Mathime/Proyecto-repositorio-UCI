from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Form, Depends, HTTPException,Request, Response
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

app = FastAPI()
ADMIN_USERNAME = "20241988"
ADMIN_PASSWORD = "admin123"

Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory='static'), name="static") # type: ignore

@app.get("/admin", response_class=HTMLResponse)
def inicio(request:Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/vista_alumnos", response_class=HTMLResponse)
async def alumno(request: Request):
    return templates.TemplateResponse("vista_alumnos.html", {"request": request})

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
def registrar_proyecto(request: Request, mensaje: str = None, db: Session = Depends(get_db)):
    facultades = db.query(Facultad).all()  
    return templates.TemplateResponse("registrar_proyecto.html", {"request": request, "facultades": facultades, "mensaje": mensaje})


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
    descripcion: str = Form(...),
    fecha_asignacion: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        nuevo_proyecto = Proyecto(nombreProyecto=nombreProyecto)
        db.add(nuevo_proyecto)
        db.commit()
        db.refresh(nuevo_proyecto)
        if fecha_asignacion:
            fecha_asignacion = datetime.strptime(fecha_asignacion, "%Y-%m-%dT%H:%M")

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
    
    # Redirigir según el rol del usuario
    if usuario.rol_usuario == "Docente":
        return RedirectResponse(url="/docentes", status_code=302)
    elif usuario.rol_usuario == "Estudiante":
        return RedirectResponse(url="/vista_alumnos", status_code=302)
    else:
        raise HTTPException(status_code=403, detail="Rol no permitido")

    
