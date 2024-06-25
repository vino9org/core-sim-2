import json
import logging
import logging.config
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from casa.api import router as casa_router

# Load the logging configuration
LOGGING_CONFIG = {}
with open("logger_config.json", "r") as f:
    LOGGING_CONFIG = json.load(f)
    logging.config.dictConfig(LOGGING_CONFIG)

app = FastAPI(docs_url=None, redoc_url=None)
app.include_router(casa_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger("uvicorn.access")
    # the uvicorn.logging is out exposed to the public
    # we tell mypy to ignore it for now
    console_formatter = uvicorn.logging.ColourizedFormatter(LOGGING_CONFIG["formatters"]["standard"]["format"])
    logger.handlers[0].setFormatter(console_formatter)
    yield


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
