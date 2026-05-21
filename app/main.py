from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import prueba

app = FastAPI(
    title="App CRP API",
    version="1.0.0",
    root_path="/app_crp"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "funcionando"}

app.include_router(prueba.router, prefix="/api/prueba", tags=["Prueba"])