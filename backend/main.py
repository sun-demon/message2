import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from auth.routes import router as auth_router

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="message2 API", version="0.1.0")

# Configuring CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In develop may "*", after other
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "message2 API", "status": "running"}


@app.get("/ping")
async def ping():
    return {"ping": "pong"}


app.include_router(auth_router)

#  Start point for launching of python main.py (optional)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
