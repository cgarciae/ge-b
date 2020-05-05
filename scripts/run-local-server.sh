
export PORT="8001"
export APP_HOST="http://0.0.0.0:$PORT"

uvicorn app.main:app --port $PORT --reload