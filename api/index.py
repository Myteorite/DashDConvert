# api/index.py
from fastapi import FastAPI
from convert import router as convert_router

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FastAPI is working on Vercel!"}

# register route
app.include_router(convert_router, prefix="/api")
