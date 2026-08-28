from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, extract
from sqlalchemy.orm import relationship, Session
from app.database import Base


class EstatusAccion(Base):
    __tablename__ = "estatus_acciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_accion_accion_id = Column(Integer, ForeignKey("plan_accion_acciones.id", ondelete="CASCADE"),nullable=False, unique=True, index=True)
    tipo_hallazgo = Column(String(40), nullable=True,)
    tipo_accion = Column(String(40), nullable=True,)
    estatus = Column(String(20), nullable=False,)  
    observaciones = Column(Text, nullable=True)
    actualizado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    plan_accion_accion = relationship("PlanAccionAccion", back_populates="estatus_accion")
    actualizado_por = relationship("Usuario")

    @classmethod
    def crear_por_defecto(cls, db: Session, plan_accion_accion_id: int) -> "EstatusAccion":
        """
        Se crea automáticamente junto con cada PlanAccionAccion, con
        valores por defecto. Normalización la actualiza después vía PATCH.
        """
        nuevo = cls(
            plan_accion_accion_id=plan_accion_accion_id,
            estatus="Abierto",
        )
        db.add(nuevo)
        return nuevo

    @classmethod
    def actualizar(cls, db: Session, plan_accion_accion_id: int, usuario_id: int, **campos) -> "EstatusAccion":
        """
        Actualiza el estatus de una acción específica. Solo Normalización
        (usuarios con login) puede llamar a esto, vía su propio endpoint.
        """
        estatus_accion = (
            db.query(cls)
            .filter(cls.plan_accion_accion_id == plan_accion_accion_id)
            .first()
        )
        if not estatus_accion:
            raise ValueError("No existe un registro de estatus para esta acción.")

        for campo, valor in campos.items():
            if valor is not None:
                setattr(estatus_accion, campo, valor)

        estatus_accion.actualizado_por_id = usuario_id
        db.commit()
        db.refresh(estatus_accion)
        return estatus_accion
    
    
    @classmethod
    def contar_por_mes_y_campo(cls, db: Session, campo: str, anio: int):
        from app.models.planaccion import PlanAccionAccion  # import local, evita el ciclo

        columna = getattr(cls, campo)

        resultados = (
            db.query(
                extract('month', PlanAccionAccion.fecha).label('mes'),
                columna.label('valor'),
                func.count(cls.id).label('cantidad')
            )
            .join(PlanAccionAccion, cls.plan_accion_accion_id == PlanAccionAccion.id)
            .filter(extract('year', PlanAccionAccion.fecha) == anio)
            .filter(columna.isnot(None))
            .group_by('mes', columna)
            .all()
        )
        return resultados
    
    @classmethod
    def contar_no_conformidades_por_proceso(cls, db: Session, solo_abiertas: bool = False):
        from app.models.accionescorrectivas import AccionCorrectiva
        from app.models.planaccion import PlanAccionGrupo, PlanAccionAccion

        query = (
            db.query(
                AccionCorrectiva.proceso_afectado,
                func.count(cls.id).label("cantidad")
            )
            .join(PlanAccionAccion, cls.plan_accion_accion_id == PlanAccionAccion.id)
            .join(PlanAccionGrupo, PlanAccionAccion.grupo_id == PlanAccionGrupo.id)
            .join(AccionCorrectiva, PlanAccionGrupo.accion_correctiva_id == AccionCorrectiva.id)
            .filter(cls.tipo_hallazgo == "No Conforme")
        )

        if solo_abiertas:
            query = query.filter(cls.estatus == "Abierto")

        return dict(query.group_by(AccionCorrectiva.proceso_afectado).all())