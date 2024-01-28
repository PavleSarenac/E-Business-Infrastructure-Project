FROM python:3

RUN mkdir -p /opt/src/store
RUN mkdir -p /opt/src/store/blockchain
RUN mkdir -p /opt/src/store/blockchain/output

WORKDIR /opt/src/store

COPY ./migrate.py ./migrate.py
COPY ./configuration.py ./configuration.py
COPY ./models.py ./models.py
COPY ./requirements.txt ./requirements.txt
COPY ./blockchain/output/Order.abi ./blockchain/output/Order.abi
COPY ./blockchain/output/Order.bin ./blockchain/output/Order.bin

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/store"

ENTRYPOINT ["python", "./migrate.py"]