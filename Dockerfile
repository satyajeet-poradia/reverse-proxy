FROM python:2

WORKDIR /app

COPY app.py app.py
COPY cache.py cache.py
COPY models.py models.py
COPY config.json config.json

RUN pip install peewee

EXPOSE 8080

ENTRYPOINT ["python", "app.py", "--config" , "config.json"]