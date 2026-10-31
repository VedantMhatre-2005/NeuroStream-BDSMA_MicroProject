FROM apache/spark:3.5.1

USER root

COPY requirements.txt /opt/spark/requirements.txt
RUN pip install --no-cache-dir -r /opt/spark/requirements.txt

WORKDIR /app
COPY jobs /app/jobs

USER spark
