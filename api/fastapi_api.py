import fastapi
import mlflow
import pandas as pd
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import io
from fastapi import UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

load_dotenv(".env")
load_dotenv("../.env")
mlflow.set_tracking_uri("http://84.201.144.227:8000")
logged_model_uri = 'runs:/12f37fb387ae4e3d865270d6ee2f8ebc/model_pipeline' 

app = fastapi.FastAPI(root_path="/api-student-grade-prediction")

class StudentFeatures(BaseModel):
    Sex: str
    High_School_Type: str
    Transportation: str
    Additional_Work: str
    Sports_activity: str
    Reading: str
    Notes: str
    Listening_in_Class: str
    Project_work: str
    Student_Age: int
    Weekly_Study_Hours: int
    Scholarship: int
    Attendance: Optional[float] = None
    
    class Config:
        populate_by_name = True
        extra = "ignore"

class PredictionResponse(BaseModel):
    predictions: List[int]

class DictFeatures(BaseModel):
    features: List[StudentFeatures]

# @app.get("/")
# def root():
#     return {"message": "Hello World"}

# @app.get("/test")
# def test():
#     return {"message": "Test message"}

# @app.post("/test2")
# def post(param:str, textparam:str):
#     return {"message": "Test message"+param+textparam}

# @app.post("/predict")
# def predict():
#     logged_model = 'runs:/aa735d26384d4e20aa803b9cf235e64f/model_pipeline'

#     loaded_model = mlflow.pyfunc.load_model(logged_model)

#     loaded_model.predict(pd.read_csv("../X_test.csv"))

#     return{"answer":(pd.DataFrame(loaded_model.predict(pd.read_csv("../X_test.csv")))).to_json()}

ml_model= mlflow.pyfunc.load_model(logged_model_uri)
app = fastapi.FastAPI()

@app.get("/")
def root():
    return {"message": "API для предсказания оценок студентов. Используйте /docs для документации."}

@app.post("/predict-single", response_model=PredictionResponse)
def predict_single(features: DictFeatures):

    feature_dict = features.model_dump(by_alias=True)
    print(feature_dict)
    input_df = pd.DataFrame.from_dict(feature_dict["features"])
    
    prediction_raw = (pd.Series(ml_model.predict(input_df))).to_list()
    
    return {"predictions": prediction_raw}

@app.post("/predict-batch", response_model=PredictionResponse)
async def predict_batch(file: UploadFile = File(...)):

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Неверный формат файла. Требуется .csv")
    
    try:
        contents = await file.read()
        buffer = io.StringIO(contents.decode('utf-8'))
        input_df = pd.read_csv(buffer)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при чтении или обработке файла: {e}")
        
    try:
        predictions_raw = ml_model.predict(input_df)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка во время предсказания. Убедитесь, что колонки в файле соответствуют требованиям модели. Ошибка: {e}")

    return {"predictions": predictions_raw.tolist()}
