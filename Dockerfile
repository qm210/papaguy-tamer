FROM python:3.7.15-slim-buster

WORKDIR /home

RUN apt update
RUN apt install -y gcc libc-dev python3-dev libasound2-dev

RUN python --version
# RUN /usr/local/bin/python -m pip install --upgrade pip

ENV VIRTUAL_ENV=/home/venv/
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY papaguy-tamer ./papaguy-tamer
COPY moves ./moves

EXPOSE 8080

CMD python -m papaguy-tamer
