from fastapi import FastAPI
from routers import sessionRouter, readingRouter
from repository import database
from fastapi.middleware.cors import CORSMiddleware

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="CardioTwin API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(sessionRouter.session_router)
app.include_router(readingRouter.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "CardioTwin API"}
