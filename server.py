import uuid

import uvicorn
from fastapi import FastAPI, File, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from text_generation.tabular_extraction import get_hypotheses, load_hypothesis

from utils import *

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_data(file: UploadFile = File(...)):
    try:
        file_id = str(uuid.uuid4())
        save_data(file_id, file.file.read())
        answer = {
            "id": file_id,
        }
        return JSONResponse(
            content=jsonable_encoder(answer), status_code=status.HTTP_201_CREATED
        )
    except Exception as failure:
        print(f"/upload failed with error: {failure}")
        raise failure
    finally:
        file.file.close()


@app.get("/list")
async def hypotheses_list(data_id: str):
    answer = []
    for hypothesis in get_hypotheses(data_id):
        hypo_id = str(uuid.uuid4())
        short_hypothesis = {
            "proba": hypothesis["corr"],
            "name": " ".join(hypothesis["first_graph"]["name"].split()[::-1][:3][::-1]),
        }
        wrapped_hypothesis = short_hypothesis | {
            "id": hypo_id,
        }
        answer.append(wrapped_hypothesis)
    return answer


@app.get("/hypothesis")
async def hypothesis_info(hypothesis_id: str):
    answer = load_hypothesis(hypothesis_id)
    return answer


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info", workers=4)
