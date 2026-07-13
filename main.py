from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"status": "FDE plan: started"}
