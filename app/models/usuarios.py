from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session
from app.database import Base
from passlib.context import CryptContext
from typing import Optional, List, Dict, Any
import unicodedata

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ficha = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    usuario = Column(String(200), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    cargo = Column(String(100), nullable=False)
    permisos = Column(ARRAY(String), nullable=True, server_default="{}")
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    def set_password(self, password_plano: str) -> None:
        """Hashea la contraseña y la guarda en password_hash."""
        self.password_hash = pwd_context.hash(password_plano)


    def verify_password(self, password_plano: str) -> bool:
        """Verifica si la contraseña plana coincide con el hash guardado."""
        return pwd_context.verify(password_plano, self.password_hash)


    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Actualiza los atributos del usuario desde un diccionario.
        Si viene 'password', la hashea automáticamente.
        Omite campos que no existen en el modelo.
        """
        for key, value in data.items():
            if key == "password":
                self.set_password(value)
            elif hasattr(self, key):
                setattr(self, key, value)


    @staticmethod
    def _normalizar(texto: str) -> str:
        """Quita tildes/ñ y pasa a minúsculas, para usarlo en el username."""
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
        return texto.lower()


    @classmethod
    def generar_usuario_unico(cls, db_session, nombre: str, apellido: str, excluir_id: int = None) -> str:
        """
        Genera un nombre de usuario a partir del PRIMER nombre y PRIMER apellido.
        Si ya existe, le agrega un número al final hasta encontrar uno libre.
        """
        primer_nombre = cls._normalizar(nombre.strip().split()[0])
        primer_apellido = cls._normalizar(apellido.strip().split()[0])
        base = f"{primer_nombre}_{primer_apellido}"

        candidato = base
        contador = 1
        while True:
            query = db_session.query(cls).filter(cls.usuario == candidato)
            if excluir_id:
                query = query.filter(cls.id != excluir_id)
            if not query.first():
                return candidato
            contador += 1
            candidato = f"{base}{contador}"


    @classmethod
    def crear(cls, db_session, **kwargs) -> "Usuario":
        """
        Crea un NUEVO usuario en la BD.
        """
        password = kwargs.pop("password", None)
        if not password:
            raise ValueError("La contraseña es obligatoria para crear un usuario")

        nuevo = cls(**kwargs)
        nuevo.set_password(password)

        db_session.add(nuevo)
        db_session.commit()
        db_session.refresh(nuevo)
        return nuevo


    @classmethod
    def actualizar(cls, db_session, usuario_id: int, **kwargs) -> "Usuario":
        """
        Actualiza un usuario EXISTENTE.
        """
        usuario = db_session.query(cls).filter(cls.id == usuario_id).first()
        if not usuario:
            raise ValueError(f"Usuario con id {usuario_id} no encontrado")

        password = kwargs.pop("password", None)
        if password:
            usuario.set_password(password)

        # Si cambia nombre o apellido, regeneramos el username automáticamente
        if "nombre" in kwargs or "apellido" in kwargs:
            nuevo_nombre = kwargs.get("nombre", usuario.nombre)
            nuevo_apellido = kwargs.get("apellido", usuario.apellido)
            kwargs["usuario"] = cls.generar_usuario_unico(
                db_session, nuevo_nombre, nuevo_apellido, excluir_id=usuario.id
            )

        for key, value in kwargs.items():
            if hasattr(usuario, key):
                setattr(usuario, key, value)

        db_session.commit()
        db_session.refresh(usuario)
        return usuario


    @classmethod
    def obtener_por_id(cls, db_session, usuario_id: int) -> Optional["Usuario"]:
        """Busca un usuario por ID, retorna None si no existe."""
        return db_session.query(cls).filter(cls.id == usuario_id).first()


    @classmethod
    def obtener_por_usuario(cls, db_session, nombre_usuario: str) -> Optional["Usuario"]:
        """Busca por nombre de usuario."""
        return db_session.query(cls).filter(cls.usuario == nombre_usuario).first()


    @classmethod
    def obtener_por_email(cls, db_session, email: str) -> Optional["Usuario"]:
        """Busca por email."""
        return db_session.query(cls).filter(cls.email == email).first()

    @classmethod
    def obtener_todos_emails(cls, db_session) -> list[str]:
        """Devuelve el email únicamente de los usuarios activos."""
        resultados = db_session.query(cls.email).filter(cls.activo == True).all()
        return [email for (email,) in resultados]


    @classmethod
    def obtener_por_ficha(cls, db_session, ficha: str) -> Optional["Usuario"]:
        """Busca un usuario por ficha."""
        return db_session.query(cls).filter(cls.ficha == ficha).first()


    @classmethod
    def obtener_todos(cls, db_session, solo_activos: bool = True) -> List["Usuario"]:
        """Devuelve los usuarios registrados, por defecto solo los activos."""
        query = db_session.query(cls)
        if solo_activos:
            query = query.filter(cls.activo == True)
        return query.order_by(cls.nombre, cls.apellido).all()


    @classmethod
    def filtrar_activos_por_emails(cls, db: Session, emails: list[str]):
        """Filtra y retorna solo los usuarios activos que coincidan con la lista de correos."""
        if not emails:
            return []
        return db.query(cls).filter(cls.email.in_(emails), cls.activo == True).all()

    @classmethod
    def esta_activo_por_email(cls, db: Session, email: str) -> bool:
        """Verifica si el usuario existe y su estatus activo es True."""
        if not email:
            return False
        usuario = db.query(cls).filter(cls.email == email, cls.activo == True).first()
        return usuario is not None
    
