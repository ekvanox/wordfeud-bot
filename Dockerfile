FROM python:3

RUN mkdir -p app

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD [ "python", "./main.py" ]