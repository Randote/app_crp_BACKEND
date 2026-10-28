import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import prueba
from app.routers import usuarios
from app.routers import auth
from app.routers import accionescorrectivas
from app.routers import matrizbasic
from app.routers import matrizdetalle
from app.routers import planaccion
from app.routers import bitacora
from app.routers import dashboard_indicadores
from app.routers import supervisores
from app.email.scheduler import iniciar_scheduler

app = FastAPI(
    title="App CRP API",
    version="1.0.0",
    root_path="/api_crp"
)



os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

@app.on_event("startup")
async def startup_event():
    iniciar_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(prueba.router, prefix="/api/prueba", tags=["Prueba"])
app.include_router(planaccion.router, prefix="/api/plan-accion", tags=["Plan de Acción"])
app.include_router(bitacora.router, prefix="/api/bitacora", tags=["Bitácora"])
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(accionescorrectivas.router, prefix="/api/acciones-correctivas", tags=["FORMS"])
app.include_router(matrizbasic.router, prefix="/api/matrizbasic", tags=["Matriz"])
app.include_router(matrizdetalle.router, prefix="/api/matrizdetalle", tags=["Matriz"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(dashboard_indicadores.router, prefix="/api/reportes", tags=["Reportes"])
app.include_router(supervisores.router, prefix="/api/supervisores", tags=["Supervisores"])