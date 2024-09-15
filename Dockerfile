FROM python:3.11

WORKDIR /root/plutous-trade-crypto

COPY . .

RUN pip install poetry

RUN poetry config virtualenvs.create false && \
  poetry install

CMD ["plutous", "start-server"]
# CMD ["plutous", "trade", "crypto", "collect", "BinanceUsdm", "funding_rate"]