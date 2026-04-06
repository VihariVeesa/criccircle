from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "CricCircle Backend Running 🚀"}