FROM python:3.6

WORKDIR /opt/bookworm

COPY . .

RUN pip install -r requirements.txt

EXPOSE 10012

CMD [ "gunicorn", "--preload", "-w", "4", "-t", "1200", "-b", "0.0.0.0:10012", "app:server" ]