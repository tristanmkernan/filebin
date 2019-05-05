FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.8

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

RUN python -m nltk.downloader wordnet

COPY . /app
