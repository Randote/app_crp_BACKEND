from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, Session, selectinload
from datetime import date
from app.database import Base
from app.models.ishikawa import IshikawaAnalisis
from app.models.why5 import Analisis5Porques
from app.models.planaccion import PlanAccionGrupo
from app.models.bitacora import BitacoraEntrada


class AccionCorrectiva(Base):
    __tablename__ = "acciones_correctivas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codificador = Column(String(50), nullable=False, unique=True, index=True)
    fecha_deteccion = Column(Date, nullable=False)
    proceso_afectado = Column(String(200), nullable=False)
    proceso_interaccion = Column(Text, nullable=True)
    dueno_proceso = Column(String(150), nullable=False) 
    participantes = Column(Text, nullable=True)
    origen_deteccion = Column(String(100), nullable=True)
    especificacion = Column(Text, nullable=True)
    problema_detectado = Column(Text, nullable=True)
    que_ocurre = Column(Text, nullable=True)
    cuando_ocurre = Column(Text, nullable=True)
    donde_ocurre = Column(Text, nullable=True)
    usa_ishikawa = Column(Boolean, nullable=False, default=False)
    usa_5porques = Column(Boolean, nullable=False, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    acciones_inmediatas = relationship("AccionInmediata", back_populates="accion_correctiva",cascade="all, delete-orphan", order_by="AccionInmediata.orden")
    ishikawa_analisis = relationship("IshikawaAnalisis", back_populates="accion_correctiva",uselist=False, cascade="all, delete-orphan")
    analisis_5porques = relationship("Analisis5Porques", back_populates="accion_correctiva",cascade="all, delete-orphan", order_by="Analisis5Porques.orden")
    plan_accion_grupos = relationship("PlanAccionGrupo", back_populates="accion_correctiva",cascade="all, delete-orphan", order_by="PlanAccionGrupo.orden")

    @staticmethod
    def _generar_codificador(db: Session) -> str:
        anio = date.today().year
        ultimo = (
            db.query(func.count(AccionCorrectiva.id))
            .filter(AccionCorrectiva.codificador.like(f"CRP-{anio}-%"))
            .scalar()
        )
        consecutivo = (ultimo or 0) + 1
        return f"CRP-{anio}-{consecutivo}"


    @classmethod
    def crear(cls, db: Session, acciones_inmediatas: list = None, ishikawa: dict = None, analisis_5porques: list = None, plan_accion_grupos: list = None, **kwargs) -> "AccionCorrectiva":

        if kwargs.get("fecha_deteccion") and kwargs["fecha_deteccion"] > date.today():
            raise ValueError("La fecha de detección no puede ser una fecha futura.")

        nueva = cls(codificador=cls._generar_codificador(db), **kwargs)
        db.add(nueva)
        db.flush()

        for item in (acciones_inmediatas or []):
            db.add(AccionInmediata(accion_correctiva_id=nueva.id, **item))

        if ishikawa:
            problema_enfocado = ishikawa.pop("problema_enfocado", None)
            IshikawaAnalisis.crear(
                db,
                accion_correctiva_id=nueva.id,
                problema_enfocado=problema_enfocado,
                **ishikawa  
            )
        
        for orden, causa in enumerate(analisis_5porques or []):
            Analisis5Porques.crear(
                db,
                accion_correctiva_id=nueva.id,
                causa_potencial=causa["causa_potencial"],
                porques=causa["porques"],
                orden=orden,
            )

        for orden, grupo in enumerate(plan_accion_grupos or []):
            PlanAccionGrupo.crear(
                db,
                accion_correctiva_id=nueva.id,
                causa_raiz_numero=grupo.get("causa_raiz_numero"),
                acciones=grupo["acciones"],
                orden=orden,
            )

        db.commit()
        db.refresh(nueva)
        return nueva

    @classmethod
    def obtener_por_codificador(cls, db: Session, codificador: str) -> "AccionCorrectiva | None":
            return (
                db.query(cls)
                .options(
                    selectinload(cls.acciones_inmediatas),
                    selectinload(cls.ishikawa_analisis).selectinload(IshikawaAnalisis.causas),
                    selectinload(cls.analisis_5porques).selectinload(Analisis5Porques.porques),
                    selectinload(cls.plan_accion_grupos)
                )
                .filter(cls.codificador == codificador)
                .first()
            )
            
            
  

    def actualizar(
        self,
        db: Session,
        acciones_inmediatas: list = None,
        ishikawa: dict = None,
        analisis_5porques: list = None,
        usuario=None,   # 👈 nuevo parámetro
        **kwargs
    ) -> "AccionCorrectiva":
        if kwargs.get("fecha_deteccion") and kwargs["fecha_deteccion"] > date.today():
            raise ValueError("La fecha de detección no puede ser una fecha futura.")

        for campo, valor in kwargs.items():
            setattr(self, campo, valor)

        # --- Acciones inmediatas: siempre se reemplazan ---
        for ai in list(self.acciones_inmediatas):
            db.delete(ai)
        db.flush()
        for item in (acciones_inmediatas or []):
            db.add(AccionInmediata(accion_correctiva_id=self.id, **item))

        # --- Ishikawa: solo se reemplaza si el checkbox está activo ---
        if self.usa_ishikawa:
            if self.ishikawa_analisis:
                db.delete(self.ishikawa_analisis)
                db.flush()
            if ishikawa:
                problema_enfocado = ishikawa.pop("problema_enfocado", None)
                IshikawaAnalisis.crear(
                    db,
                    accion_correctiva_id=self.id,
                    problema_enfocado=problema_enfocado,
                    **ishikawa
                )

        # --- 5 Porqués: solo se reemplaza si el checkbox está activo ---
        if self.usa_5porques:
            for causa in list(self.analisis_5porques):
                db.delete(causa)
            db.flush()
            for orden, causa in enumerate(analisis_5porques or []):
                Analisis5Porques.crear(
                    db,
                    accion_correctiva_id=self.id,
                    causa_potencial=causa["causa_potencial"],
                    porques=causa["porques"],
                    orden=orden,
                )

        # --- Bitácora: una entrada por guardado ---
        if usuario is not None:
            from app.models.bitacora import BitacoraEntrada
            nombre = f"{usuario.nombre} {usuario.apellido}"
            BitacoraEntrada.registrar_evento(
                db,
                self.id,
                usuario,
                f"{nombre} actualizó el análisis y detección de esta acción correctiva."
            )
        db.commit()
        db.refresh(self)
        return self
        

 
    @classmethod
    def contar_total(cls, db: Session):
        return db.query(cls).count()
    
    
    @classmethod
    def contar_por_proceso_afectado(cls, db: Session):
        resultados = (
            db.query(cls.proceso_afectado, func.count(cls.id))
            .group_by(cls.proceso_afectado)
            .all()
        )
        return dict(resultados)
    
    @classmethod
    def contar_por_origen_deteccion(cls, db: Session):
        resultados = (
            db.query(cls.origen_deteccion, func.count(cls.id))
            .group_by(cls.origen_deteccion)
            .all()
        )
        return dict(resultados)
    
    
    


class AccionInmediata(Base):
    __tablename__ = "acciones_inmediatas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    accion_correctiva_id = Column(Integer, ForeignKey("acciones_correctivas.id", ondelete="CASCADE"), nullable=False, index=True)
    accion = Column(Text, nullable=False)
    fecha = Column(Date, nullable=False)
    responsable = Column(String(150), nullable=False)
    estatus = Column(String(50), nullable=False)
    orden = Column(Integer, nullable=False, default=0)

    accion_correctiva = relationship("AccionCorrectiva", back_populates="acciones_inmediatas")