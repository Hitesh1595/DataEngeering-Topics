FROM jupyter/pyspark-notebook:spark-3.5.0

USER root

WORKDIR /home/jovyan/work

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER jovyan
