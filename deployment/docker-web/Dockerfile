FROM python:3.5.1

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y libmemcached-dev

ENV PYTHONUNBUFFERED 1

ADD requirements/ /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000
EXPOSE 8888

