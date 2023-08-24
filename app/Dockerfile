FROM python:latest
WORKDIR /app
COPY . .
RUN pip install flask
RUN pip install requests
RUN pip install gunicorn
RUN pip install gtts
RUN pip install pymongo
RUN pip install twilio


ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=3011

#CMD ["gunicorn", "-b", "0.0.0.0:3011", "app:app"]

#CMD ["flask", "run"]
