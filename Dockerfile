FROM python:3.6.4

RUN mkdir -p app

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

CMD [ "python", "./main.py" ]