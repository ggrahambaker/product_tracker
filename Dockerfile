FROM python:3.6-alpine

RUN adduser -D tracker

WORKDIR /home/tracker

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY tracker.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP tracker.py

RUN chown -R tracker:tracker ./
USER tracker

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]