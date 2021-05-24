FROM python:3.9-slim

WORKDIR /cwd

COPY requirements.txt /cwd/

RUN set -xe && \
    pip install -r requirements.txt && \
    true

COPY wait.py /cwd/

ENTRYPOINT [ "python", "/cwd/wait.py" ]
LABEL org.opencontainers.image.source https://github.com/samjarrett/elb-waiter
