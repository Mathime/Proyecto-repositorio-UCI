from pydantic import BaseModel

class FacultadBase(BaseModel):
    nombreFacultad: str

class FacultadCreate(FacultadBase):
    pass

class Facultad(FacultadBase):
    idFacultad: int

    class Config:
        from_attributes = True


class CarreraCreate(BaseModel):
    nombreCarrera: str
    idFacultad: int

    class Config:
        from_attributes = True