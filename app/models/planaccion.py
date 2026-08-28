from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship, Session
from app.database import Base
from app.models.estados import EstatusAccion
from sqlalchemy import func, case, and_
from datetime import date


class PlanAccionGrupo(Base):
    __tablename__ = "plan_accion_grupos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    accion_correctiva_id = Column(Integer, ForeignKey("acciones_correctivas.id", ondelete="CASCADE"), nullable=False, index=True)
    causa_raiz_numero = Column(Integer, nullable=True)
    orden = Column(Integer, nullable=False, default=0)

    accion_correctiva = relationship("AccionCorrectiva", back_populates="plan_accion_grupos")
    acciones = relationship("PlanAccionAccion", back_populates="grupo", cascade="all, delete-orphan", order_by="PlanAccionAccion.orden")

    @classmethod
    def crear(cls, db: Session, accion_correctiva_id: int, acciones: list, causa_raiz_numero: int = None, orden: int = 0) -> "PlanAccionGrupo":
        nuevo = cls(
            accion_correctiva_id=accion_correctiva_id,
            causa_raiz_numero=causa_raiz_numero,
            orden=orden,
        )
        db.add(nuevo)
        db.flush()

        for i, item in enumerate(acciones or []):
            nueva_accion = PlanAccionAccion(
                grupo_id=nuevo.id,
                descripcion=item.get("descripcion"),
                fecha=item.get("fecha"),
                responsable=item.get("responsable"),
                email=item.get("email"),
                metodologia_descripcion=item.get("metodologia_descripcion"),
                metodologia_fecha=item.get("metodologia_fecha"),
                metodologia_responsable=item.get("metodologia_responsable"),
                metodologia_email=item.get("metodologia_email"),
                orden=i,
            )
            db.add(nueva_accion)
            db.flush()

            EstatusAccion.crear_por_defecto(db, plan_accion_accion_id=nueva_accion.id)

        return nuevo


class PlanAccionAccion(Base):
    __tablename__ = "plan_accion_acciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grupo_id = Column(Integer, ForeignKey("plan_accion_grupos.id", ondelete="CASCADE"),nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    fecha = Column(Date, nullable=True)
    responsable = Column(String(150), nullable=True)
    email = Column(String(255), nullable=True)
    metodologia_descripcion = Column(Text, nullable=True)
    metodologia_fecha = Column(Date, nullable=True)
    metodologia_responsable = Column(String(150), nullable=True)
    metodologia_email = Column(String(255), nullable=True)
    orden = Column(Integer, nullable=False, default=0)

    grupo = relationship("PlanAccionGrupo", back_populates="acciones")
    estatus_accion = relationship("EstatusAccion", back_populates="plan_accion_accion",uselist=False, cascade="all, delete-orphan")
    

    @classmethod
    def contar_por_estado(cls, db):
        """Devuelve (abiertas, cerradas, vencidas) contando tareas del plan de acción."""
        hoy = date.today()

        resultado = (
            db.query(
                func.count(
                    case((and_(EstatusAccion.estatus == "Abierto", cls.fecha >= hoy), 1))
                ).label("abiertas"),
                func.count(
                    case((EstatusAccion.estatus == "Cerrado", 1))
                ).label("cerradas"),
                func.count(
                    case((and_(EstatusAccion.estatus == "Abierto", cls.fecha < hoy), 1))
                ).label("vencidas"),
            )
            .select_from(cls)
            .join(EstatusAccion, EstatusAccion.plan_accion_accion_id == cls.id)
            .one()
        )

        return resultado
    
    
    @classmethod
    def contar_total(cls, db: Session):
        return db.query(cls).count()
    
