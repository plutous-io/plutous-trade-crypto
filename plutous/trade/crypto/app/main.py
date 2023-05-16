from fastapi import APIRouter


app = APIRouter(prefix="/crypto", tags=["crypto"])


@app.get("/")
async def root():
    return {"message": "Hello World"}
