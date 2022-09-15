FROM python:3.10.4-slim-buster

LABEL maintainer="antonshpachukjob@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]