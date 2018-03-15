FROM python:3.6
LABEL maintainer "Tristan Kernan <tristan.kernan@rutgers.edu>"

RUN apt-get update
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD python app.py
