import asyncio
import time
from datetime import datetime, timedelta
from typing import Type

import numpy as np
from ccxt.async_support.base.ws.order_book import OrderBook as _Orderbook
from loguru import logger
from sqlalchemy.orm import Session

from plutous import database as db
from plutous.trade.crypto.models import BidAskSum, Orderbook, orderbook

from .base import BaseCollector, BaseCollectorConfig

INIT_TIMEOUT = 20
TIMEOUT = timedelta(minutes=5)


class OrderbookCollectorConfig(BaseCollectorConfig):
    watch_orderbook_limit: int = 5000


class OrderbookCollector(BaseCollector):
    TABLE: Type[Orderbook] = Orderbook

    def __init__(self, config: OrderbookCollectorConfig):
        super().__init__(config)
        self.exchange.options["watchOrderBookLimit"] = config.watch_orderbook_limit

    async def _collect(self):
        active_symbols = await self.fetch_active_symbols()
        await self.exchange.watch_order_book_for_symbols(active_symbols)
        await asyncio.sleep(1)

        if self.exchange.orderbooks is None:
            raise RuntimeError("No orderbooks found")

        start_time = time.time()
        while True:
            if time.time() - start_time > INIT_TIMEOUT:
                raise RuntimeError("Orderbook not populated")
            if all(
                [
                    self.exchange.orderbooks[symbol]["timestamp"] is not None
                    for symbol in active_symbols
                ]
            ):
                break
            await asyncio.sleep(1)

        # Fetch the last snapshot of the orderbook and update miss prices
        with db.Session() as session:
            orderbook_snapshot = self.fetch_orderbook_snapshot(active_symbols, session)

        logger.info(
            f"Orderbook snapshot fetched for symbols: {orderbook_snapshot.keys()}"
        )

        for symbol, snapshot in orderbook_snapshot.items():
            for side in ["bids", "asks"]:
                for price, volume in self.exchange.orderbooks[symbol][side]:
                    snapshot[side].store(price, volume)
                self.exchange.orderbooks[symbol][side] = snapshot[side]

        while True:
            ob_data = []
            bas_data = []
            if set(self.exchange.orderbooks.keys()) != set(active_symbols):
                logger.error(
                    f"Active symbols: {active_symbols}, Orderbook symbols: {self.exchange.orderbooks.keys()}"
                )
                raise RuntimeError("Active symbols do not match orderbook symbols")

            for symbol, orderbook in self.exchange.orderbooks.items():
                logger.info(f"Processing orderbook for {symbol}")

                if orderbook["timestamp"] < int(
                    (datetime.now() - TIMEOUT).timestamp() * 1000
                ):
                    raise RuntimeError(
                        f"Orderbook for {symbol} is stale, last updated at {orderbook['timestamp']}"
                    )

                while (lastest_bid := orderbook["bids"][0][0]) > (
                    lastest_ask := orderbook["asks"][0][0]
                ):
                    ticker = await self.exchange.fetch_ticker(symbol)
                    logger.info(f"Filtering bid {lastest_bid} > ask {lastest_ask}")
                    if lastest_bid > ticker["bid"]:
                        logger.info(
                            f"Filtering bid {lastest_bid} > ticker bid {ticker['bid']}"
                        )
                        orderbook["bids"].store(lastest_bid, 0)
                    if lastest_ask < ticker["ask"]:
                        logger.info(
                            f"Filtering ask {lastest_ask} < ticker ask {ticker['ask']}"
                        )
                        orderbook["asks"].store(lastest_ask, 0)

                bids, asks = np.array(orderbook["bids"]), np.array(orderbook["asks"])
                timestamp = self.round_milliseconds(orderbook["timestamp"])
                bas = BidAskSum(
                    exchange=self._exchange,
                    symbol=symbol,
                    timestamp=timestamp,
                    datetime=self.exchange.iso8601(timestamp),
                    bids_sum_5=float(bids[bids[:, 0] > (bids[0, 0] * 0.95), 1].sum()),
                    bids_sum_10=float(bids[bids[:, 0] > (bids[0, 0] * 0.90), 1].sum()),
                    bids_sum_15=float(bids[bids[:, 0] > (bids[0, 0] * 0.85), 1].sum()),
                    bids_sum_20=float(bids[bids[:, 0] > (bids[0, 0] * 0.80), 1].sum()),
                    asks_sum_5=float(asks[asks[:, 0] < (asks[0, 0] * 1.05), 1].sum()),
                    asks_sum_10=float(asks[asks[:, 0] < (asks[0, 0] * 1.10), 1].sum()),
                    asks_sum_15=float(asks[asks[:, 0] < (asks[0, 0] * 1.15), 1].sum()),
                    asks_sum_20=float(asks[asks[:, 0] < (asks[0, 0] * 1.20), 1].sum()),
                )
                bas_data.append(bas)
                ob_data.append(
                    Orderbook(
                        exchange=self._exchange,
                        symbol=symbol,
                        timestamp=timestamp,
                        datetime=self.exchange.iso8601(timestamp),
                        bids=orderbook["bids"],
                        asks=orderbook["asks"],
                    )
                )
            with db.Session() as session:
                self._insert(ob_data, session, Orderbook)
                self._insert(bas_data, session, BidAskSum)
                session.commit()

            await asyncio.sleep(30)

    def fetch_orderbook_snapshot(
        self, symbols: list[str], session: Session
    ) -> dict[str, _Orderbook]:
        logger.info("Fetching orderbook snapshot")
        tb = self.TABLE
        snapshots = (
            session.query(tb.symbol, tb.bids, tb.asks)
            .distinct(tb.symbol)
            .filter(
                tb.exchange == self._exchange,
                tb.symbol.in_(symbols),
                tb.timestamp
                >= (datetime.now().timestamp() * 1000) - 10 * 60 * 1000,  # 10 minutes
            )
            .order_by(tb.symbol, tb.timestamp.desc())
            .all()
        )
        return {
            snapshot.symbol: self.exchange.order_book(
                {"bids": snapshot.bids, "asks": snapshot.asks}
            )
            for snapshot in snapshots
        }
