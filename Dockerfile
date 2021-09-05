FROM python:3.6-slim

COPY requirements.txt ./requirements.txt
RUN mkdir /usr/app
COPY app.py /usr/app/app.py
RUN pip install --upgrade pip setuptools
RUN pip install --requirement ./requirements.txt
ENV PYTHONIOENCODING=utf-8
ENV LANG C.UTF-8
WORKDIR /usr/app
ENTRYPOINT ["python", "app.py"]