from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/trade")
async def trade():
    return {"message": "Hello World"}
