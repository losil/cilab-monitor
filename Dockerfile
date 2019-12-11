FROM python:3

LABEL mainainer="silvan.loser@stud.hslu.ch"

COPY monitor.py /opt/monitoring/monitor.py
COPY config.yml /opt/monitoring/config.yml

RUN pip3 install PyYAML cryptography

WORKDIR /opt/monitoring/

ENTRYPOINT ["python3", "/opt/monitoring/monitor.py"]