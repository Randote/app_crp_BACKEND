from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import Session
from app.database import Base

class ProcesoSupervisor(Base):
    __tablename__ = "procesos_supervisores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_proceso = Column(String(150), unique=True, nullable=False, index=True)
    supervisor_nombre = Column(String(150), nullable=False)
    supervisor_email = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    @classmethod
    def obtener_todos(cls, db: Session):
        """Retorna todos los registros de procesos y supervisores."""
        return db.query(cls).all()

    @classmethod
    def obtener_por_id(cls, db: Session, supervisor_id: int):
        """Busca un registro por su ID único."""
        return db.query(cls).filter(cls.id == supervisor_id).first()

    @classmethod
    def obtener_por_proceso(cls, db: Session, proceso: str):
        """Busca un registro por el nombre del proceso."""
        return db.query(cls).filter(cls.nombre_proceso == proceso).first()
    
    @classmethod
    def obtener_activo_por_proceso(cls, db: Session, proceso: str):
        """Retorna el registro del supervisor solo si el proceso está activo."""
        return db.query(cls).filter(
            cls.nombre_proceso == proceso,
            cls.activo == True
        ).first()

    @classmethod
    def esta_activo_por_email(cls, db: Session, email: str) -> bool:
        """Verifica si el supervisor tiene al menos un registro asociado y activo."""
        if not email:
            return False
        supervisor = db.query(cls).filter(
            cls.supervisor_email == email, 
            cls.activo == True
        ).first()
        return supervisor is not None