from fastapi import APIRouter

router= APIRouter()

@router.get("/")
def prueba():
    return {"message": "sdasdaasdas siiiii sadasdasdas"}