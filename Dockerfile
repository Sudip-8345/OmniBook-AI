FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize the SQLite database
RUN python -c "import sys; sys.path.insert(0,'.'); from database.db import init_db; init_db()"

EXPOSE 8000 8501

# Run FastAPI + Streamlit together
CMD bash -c "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"
