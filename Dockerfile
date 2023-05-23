FROM python:3.10

WORKDIR /root/plutous-trade-crypto

COPY . .

RUN pip install poetry

RUN poetry config virtualenvs.create false && \
  poetry install

CMD ["plutous", "start-server"]