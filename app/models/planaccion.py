from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, func, case, and_
from sqlalchemy.orm import relationship, Session
from app.database import Base
from app.models.estados import EstatusAccion
from app.models.procesosupervisor import ProcesoSupervisor
from datetime import date, timedelta


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
                metodologia_descripcion=item.get("metodologia_descripcion"),
                metodologia_fecha=item.get("metodologia_fecha"),
                metodologia_responsable=item.get("metodologia_responsable"),
                metodologia_email=item.get("metodologia_email"),
                orden=i,
            )
            db.add(nueva_accion)
            db.flush()

            for j, resp in enumerate(item.get("responsables") or []):
                db.add(PlanAccionResponsable(
                    plan_accion_accion_id=nueva_accion.id,
                    nombre=resp.get("nombre"),
                    email=resp.get("email"),
                    proceso=resp.get("proceso"),
                    orden=j,
                ))

            EstatusAccion.crear_por_defecto(db, plan_accion_accion_id=nueva_accion.id)

        return nuevo


class PlanAccionAccion(Base):
    __tablename__ = "plan_accion_acciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grupo_id = Column(Integer, ForeignKey("plan_accion_grupos.id", ondelete="CASCADE"), nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    fecha = Column(Date, nullable=True)
    metodologia_descripcion = Column(Text, nullable=True)
    metodologia_fecha = Column(Date, nullable=True)
    metodologia_responsable = Column(String(150), nullable=True)
    metodologia_email = Column(String(255), nullable=True)
    orden = Column(Integer, nullable=False, default=0)

    grupo = relationship("PlanAccionGrupo", back_populates="acciones")
    estatus_accion = relationship("EstatusAccion", back_populates="plan_accion_accion", uselist=False, cascade="all, delete-orphan")
    responsables = relationship(
        "PlanAccionResponsable",
        back_populates="accion",
        cascade="all, delete-orphan",
        order_by="PlanAccionResponsable.orden"
    )

    @classmethod
    def contar_por_estado(cls, db):
        hoy = date.today()
        resultado = (
            db.query(
                func.count(case((and_(EstatusAccion.estatus == "Abierto", cls.fecha >= hoy), 1))).label("abiertas"),
                func.count(case((EstatusAccion.estatus == "Cerrado", 1))).label("cerradas"),
                func.count(case((and_(EstatusAccion.estatus == "Abierto", cls.fecha < hoy), 1))).label("vencidas"),
            )
            .select_from(cls)
            .join(EstatusAccion, EstatusAccion.plan_accion_accion_id == cls.id)
            .one()
        )
        return resultado

    @classmethod
    def contar_total(cls, db: Session):
        return db.query(cls).count()

    @classmethod
    def contar_actividades_responsable(cls, db: Session):
        hoy = date.today()
        resultados = (
            db.query(
                cls.metodologia_email,
                func.count(cls.id).label("asignadas"),
                func.count(case((EstatusAccion.estatus == "Cerrado", 1))).label("cerradas"),
                func.count(case((and_(EstatusAccion.estatus == "Abierto", cls.metodologia_fecha < hoy), 1))).label("vencidas"),
            )
            .select_from(cls)
            .join(EstatusAccion, EstatusAccion.plan_accion_accion_id == cls.id)
            .filter(cls.metodologia_email.isnot(None))
            .group_by(cls.metodologia_email)
            .all()
        )
        return resultados

    @classmethod
    def obtener_para_notificaciones(cls, db: Session, vencidas: bool = False):
        from app.models.accionescorrectivas import AccionCorrectiva
        
        hoy = date.today()
        fecha_cond = cls.fecha < hoy if vencidas else cls.fecha >= hoy

        return (
            db.query(
                PlanAccionResponsable.email.label("email"),
                PlanAccionResponsable.nombre.label("responsable"),
                cls.descripcion.label("descripcion"),
                cls.fecha.label("fecha"),
                AccionCorrectiva.codificador.label("codificador"),
            )
            .select_from(cls)
            .join(EstatusAccion, EstatusAccion.plan_accion_accion_id == cls.id)
            .join(PlanAccionResponsable, PlanAccionResponsable.plan_accion_accion_id == cls.id)
            .join(PlanAccionGrupo, PlanAccionGrupo.id == cls.grupo_id)
            .join(AccionCorrectiva, AccionCorrectiva.id == PlanAccionGrupo.accion_correctiva_id)
            .filter(
                fecha_cond,
                EstatusAccion.estatus == "Abierto",
                PlanAccionResponsable.email.isnot(None),
                PlanAccionResponsable.email != "",
            )
            .all()
        )

    @classmethod
    def obtener_verificaciones_para_notificaciones(cls, db: Session, vencidas: bool = False):
        from app.models.accionescorrectivas import AccionCorrectiva
        
        hoy = date.today()
        fecha_cond = cls.metodologia_fecha < hoy if vencidas else cls.metodologia_fecha >= hoy

        return (
            db.query(
                cls.metodologia_email.label("email"),
                cls.metodologia_responsable.label("responsable"),
                cls.metodologia_descripcion.label("descripcion"),
                cls.metodologia_fecha.label("fecha"),
                AccionCorrectiva.codificador.label("codificador"),
            )
            .select_from(cls)
            .join(EstatusAccion, EstatusAccion.plan_accion_accion_id == cls.id)
            .join(PlanAccionGrupo, PlanAccionGrupo.id == cls.grupo_id)
            .join(AccionCorrectiva, AccionCorrectiva.id == PlanAccionGrupo.accion_correctiva_id)
            .filter(
                fecha_cond,
                EstatusAccion.estatus == "Abierto",
                cls.metodologia_email.isnot(None),
                cls.metodologia_email != "",
            )
            .all()
        )

    @classmethod
    def obtener_supervisores_acciones_vencidas(cls, db: Session):
        from app.models.accionescorrectivas import AccionCorrectiva
        
        hoy = date.today()
        fecha_limite = hoy - timedelta(days=5)

        return (
            db.query(
                cls,
                PlanAccionResponsable.proceso.label("proceso"),
                PlanAccionResponsable.nombre.label("nombre_responsable"),
                PlanAccionResponsable.email.label("email_responsable"),
                ProcesoSupervisor.supervisor_nombre,
                ProcesoSupervisor.supervisor_email,
                AccionCorrectiva.codificador.label("codificador"),
            )
            .select_from(cls)
            .join(EstatusAccion, EstatusAccion.plan_accion_accion_id == cls.id)
            .join(PlanAccionResponsable, PlanAccionResponsable.plan_accion_accion_id == cls.id)
            .join(PlanAccionGrupo, PlanAccionGrupo.id == cls.grupo_id)
            .join(AccionCorrectiva, AccionCorrectiva.id == PlanAccionGrupo.accion_correctiva_id)
            .join(ProcesoSupervisor, ProcesoSupervisor.nombre_proceso == PlanAccionResponsable.proceso)
            .filter(
                EstatusAccion.estatus == "Abierto",
                cls.fecha <= fecha_limite,
                PlanAccionResponsable.proceso.isnot(None),
                PlanAccionResponsable.proceso != "",
                ProcesoSupervisor.activo == True,
            )
            .all()
        )

class PlanAccionResponsable(Base):
    __tablename__ = "plan_accion_responsables"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_accion_accion_id = Column(Integer, ForeignKey("plan_accion_acciones.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(150), nullable=True)
    email = Column(String(255), nullable=True)
    proceso = Column(String(200), nullable=True)
    orden = Column(Integer, nullable=False, default=0)
    accion = relationship("PlanAccionAccion", back_populates="responsables")