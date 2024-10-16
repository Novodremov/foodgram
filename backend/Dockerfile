FROM python:3.9
WORKDIR /app
RUN python -m pip install --upgrade pip
RUN pip install gunicorn==20.1.0 --no-cache-dir
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "--bind", "0:8000", "foodgram_backend.wsgi"]
