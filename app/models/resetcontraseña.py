import random
import bcrypt
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, Session
from app.database import Base


class PasswordResetCode(Base):
    __tablename__ = "digitos_contraseña"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    codigo_hash = Column(String(100), nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario")

    @classmethod
    def generar(cls, db: Session, usuario_id: int, minutos_validez: int = 5):
        """
        Genera un código de 6 dígitos, BORRA cualquier código anterior de este
        usuario (ya no aplica, lo reemplaza este) y guarda el HASH del nuevo
        (nunca el código en texto plano). Devuelve (entrada, codigo_plano).
        """
        codigo = f"{random.randint(0, 999999):06d}"
        codigo_hash = bcrypt.hashpw(codigo.encode(), bcrypt.gensalt()).decode()

        db.query(cls).filter(cls.usuario_id == usuario_id).delete(synchronize_session=False)

        entrada = cls(
            usuario_id=usuario_id,
            codigo_hash=codigo_hash,
            expira_en=datetime.now(timezone.utc) + timedelta(minutes=minutos_validez),
        )
        db.add(entrada)
        db.commit()
        db.refresh(entrada)
        return entrada, codigo

    @classmethod
    def verificar(cls, db: Session, usuario_id: int, codigo_plano: str) -> "PasswordResetCode | None":
        """
        Busca entre los códigos vigentes (no expirados) de este usuario
        uno cuyo hash coincida con el código que mandó el usuario.
        Como generar() borra los anteriores, normalmente hay a lo sumo 1.
        """
        candidatos = (
            db.query(cls)
            .filter(cls.usuario_id == usuario_id)
            .order_by(cls.creado_en.desc())
            .all()
        )
        ahora = datetime.now(timezone.utc)
        for c in candidatos:
            if c.expira_en < ahora:
                continue
            if bcrypt.checkpw(codigo_plano.encode(), c.codigo_hash.encode()):
                return c
        return None

    @classmethod
    def limpiar_expirados(cls, db: Session) -> int:
        """
        Borra los códigos que ya expiraron sin usarse. Pensado para
        correr periódicamente vía scheduler. Devuelve cuántos borró.
        """
        borrados = (
            db.query(cls)
            .filter(cls.expira_en < datetime.now(timezone.utc))
            .delete(synchronize_session=False)
        )
        db.commit()
        return borrados