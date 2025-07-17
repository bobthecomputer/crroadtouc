FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .
CMD ["streamlit", "run", "streamlit_app.py"]
