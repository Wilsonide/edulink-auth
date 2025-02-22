from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routes import auth,post
from contextlib import asynccontextmanager
from database import sessionmanager
from starlette.middleware.sessions import SessionMiddleware
from settings import setting

def init():
    sessionmanager.init(setting.DATABASE_URL)
    @asynccontextmanager
    async def lifespan(app:FastAPI):
        async with sessionmanager.connect() as conn:
            await sessionmanager.create_all(conn)
    
        yield
        if sessionmanager._engine is not None:
            await sessionmanager.close()
    app = FastAPI(title='Fastapi',lifespan=lifespan)
    return app

app = init()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000", "http://localhost:5173", "https://project-react-pied-chi.vercel.app"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ['*']
)

app.add_middleware(
    SessionMiddleware,secret_key="add secret key"
)

@app.get('/')
def hello():
    return {"message": "Hello World"}

app.include_router(auth.router)
app.include_router(post.router)



if __name__ == "__main__":
    uvicorn.run('main:app',reload=True,port=8000)