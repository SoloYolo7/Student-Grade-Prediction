FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY fastapi_api.py .

COPY .env .

CMD ["uvicorn", "fastapi_api:app", "--host", "0.0.0.0", "--port", "8000"]