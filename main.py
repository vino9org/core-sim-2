import uvicorn
from fastapi import FastAPI

from casa.api import router as casa_router

app = FastAPI(docs_url=None, redoc_url=None)
app.include_router(casa_router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
