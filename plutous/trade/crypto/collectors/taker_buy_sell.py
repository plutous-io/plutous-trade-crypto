import asyncio
from datetime import datetime
from typing import Type

from loguru import logger

from plutous import database as db
from plutous.trade.crypto.models import TakerBuySell

from .base import BaseCollector, BaseCollectorConfig


class TakerBuySellCollectorConfig(BaseCollectorConfig): ...


class TakerBuySellCollector(BaseCollector):
    TABLE: Type[TakerBuySell] = TakerBuySell

    config: TakerBuySellCollectorConfig

    async def _collect(self):
        active_symbols = await self.fetch_active_symbols()
        await self.exchange.watch_trades_for_symbols(active_symbols)
        await asyncio.sleep(1)

        logger.info("Collector started")

        taker_buy_sell = {}
        current_interval = datetime.now().timestamp() // 60

        if not self.exchange.trades:
            raise RuntimeError("No trades found")

        while True:
            if (
                datetime.now().timestamp() - 1
            ) // 60 != current_interval:  # delayed by 1 second
                current_interval = datetime.now().timestamp() // 60
                logger.info("New minute started")
                if taker_buy_sell:
                    for tbs in taker_buy_sell.values():
                        if (tbs.buy_vol == 0) or (tbs.sell_vol == 0):
                            raise RuntimeError(
                                f"Invalid taker buy sell data {tbs.buy_vol} {tbs.sell_vol} for {tbs.symbol}"
                            )
                    with db.Session() as session:
                        self._insert(list(taker_buy_sell.values()), session)
                        session.commit()
                ts = self.round_milliseconds(int(datetime.now().timestamp()) * 1000)
                taker_buy_sell = {
                    symbol: TakerBuySell(
                        symbol=symbol,
                        exchange=self._exchange,
                        buy_vol=0,
                        sell_vol=0,
                        timestamp=ts,
                        datetime=self.exchange.iso8601(ts),
                    )
                    for symbol in active_symbols
                }

            if not taker_buy_sell:
                logger.info("Waiting for the next minute to start")
                await asyncio.sleep(0.5)
                continue

            if set(active_symbols) != (
                trades_symbol := set(self.exchange.trades.keys())
            ):
                raise RuntimeError(
                    f"Missing symbols {set(active_symbols) - trades_symbol} in trades"
                )

            for symbol, trades in self.exchange.trades.items():
                logger.info(f"Processing trades for {symbol}")
                while len(trades) > 0:
                    trade = trades._deque.popleft()
                    if (
                        trade_interval := (trade["timestamp"] // 60000)
                    ) != current_interval:
                        logger.info("Trade timestamp does not match current interval")
                        if trade_interval > current_interval:
                            logger.info("Trade timestamp is in the future")
                            trades.append(trade)
                            break
                        continue

                    if trade["side"] == "buy":
                        taker_buy_sell[symbol].buy_vol += trade["amount"]
                    else:
                        taker_buy_sell[symbol].sell_vol += trade["amount"]

            await asyncio.sleep(0.5)
