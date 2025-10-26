from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.model import normalise_title

app = FastAPI(title="TV Title Normalisation Service", version="1.0")


class SingleTitleRequest(BaseModel):
    messy_title: str


class BatchTitleRequest(BaseModel):
    messy_titles: List[str]


@app.post("/normalise")
def normalise_single(request: SingleTitleRequest):
    try:
        clean_title = normalise_title(request.messy_title)
        return {"clean_title": clean_title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/normalise-batch")
def normalise_batch(request: BatchTitleRequest):
    try:
        clean_titles = [normalise_title(t) for t in request.messy_titles]
        return {"clean_titles": clean_titles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
