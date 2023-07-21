FROM python:alpine3.17
WORKDIR /app
COPY . .
RUN pip install flask
RUN pip install requests
RUN pip install gunicorn
RUN pip install gtts

#ENV FLASK_APP=geocoding.py
#ENV FLASK_RUN_HOST=3.80.28.78
#ENV FLASK_RUN_PORT=3011

CMD ["gunicorn", "-b", "0.0.0.0:3011", "app:app"]

#CMD ["flask", "run"]
