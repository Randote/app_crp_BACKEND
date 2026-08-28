from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import secrets
import hashlib
from typing import Optional
from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

REFRESH_EXPIRE = 4


class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=False, unique=True, index=True)
    refresh_token_lookup = Column(String(64), nullable=False, index=True)  # 👈 nueva columna
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    revocado = Column(Boolean, nullable=False, default=False)
    user_agent = Column(String(255), nullable=True)

    usuario = relationship("Usuario")

    @staticmethod
    def _calcular_lookup(token_plano: str) -> str:
        """Hash rápido (sha256, no bcrypt) solo para poder buscar por índice en la BD."""
        return hashlib.sha256(token_plano.encode()).hexdigest()

    @classmethod
    def crear(cls, db_session, usuario_id: int, user_agent: str = "") -> tuple["Sesion", str]:
        """
        Crea una nueva sesión para el usuario y devuelve (sesion, refresh_token_plano).
        El token plano solo existe en este momento — nunca se vuelve a poder recuperar
        una vez guardado el hash.
        """
        token_plano = secrets.token_urlsafe(48)
        token_hash = pwd_context.hash(token_plano)
        lookup_hash = cls._calcular_lookup(token_plano)
        expira_en = datetime.now(timezone.utc) + timedelta(hours=REFRESH_EXPIRE)

        nueva = cls(
            usuario_id=usuario_id,
            refresh_token_hash=token_hash,
            refresh_token_lookup=lookup_hash,
            expira_en=expira_en,
            user_agent=user_agent[:255]
        )
        db_session.add(nueva)
        db_session.commit()
        db_session.refresh(nueva)
        return nueva, token_plano

    @classmethod
    def obtener_valida_por_token(cls, db_session, refresh_token_plano: str) -> Optional["Sesion"]:
        """
        Busca la sesión directo por el índice del hash rápido (ya no recorre todas
        las filas con bcrypt), y verifica con bcrypt solo esa única fila encontrada.
        """
        lookup_hash = cls._calcular_lookup(refresh_token_plano)

        sesion = db_session.query(cls).filter(
            cls.refresh_token_lookup == lookup_hash,
            cls.revocado == False,
            cls.expira_en > datetime.now(timezone.utc)
        ).first()

        if sesion and pwd_context.verify(refresh_token_plano, sesion.refresh_token_hash):
            return sesion
        return None

    def eliminar(self, db_session) -> None:
        """Borra esta sesión de la base de datos por completo."""
        db_session.delete(self)
        db_session.commit()

    @classmethod
    def eliminar_si_expirada(cls, db_session, refresh_token_plano: str) -> bool:
        """
        Busca la sesión (activa o vencida) para este token, por el índice rápido.
        Si está vencida, la borra y devuelve True. Si no existe ninguna, devuelve False.
        """
        lookup_hash = cls._calcular_lookup(refresh_token_plano)

        sesion = db_session.query(cls).filter(cls.refresh_token_lookup == lookup_hash).first()
        if sesion:
            if sesion.expira_en <= datetime.now(timezone.utc):
                db_session.delete(sesion)
                db_session.commit()
                return True
            return False
        return False

    @classmethod
    def revocar_todas_de_usuario(cls, db_session, usuario_id: int) -> None:
        """Cierra todas las sesiones activas de un usuario (ej. 'cerrar sesión en todos los dispositivos')."""
        db_session.query(cls).filter(
            cls.usuario_id == usuario_id,
            cls.revocado == False
        ).update({"revocado": True})
        db_session.commit()