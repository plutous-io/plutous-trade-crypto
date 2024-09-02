import asyncio

from plutous.trade.crypto import exchanges as ex

from .base import BaseAlert, BaseAlertConfig


class PriceDiffAlertConfig(BaseAlertConfig):
    min_threshold: float = 0.5
    max_threshold: float = 10


class PriceDiffAlert(BaseAlert):
    config: PriceDiffAlertConfig

    def __init__(self, config: PriceDiffAlertConfig):
        self.config = config
        self.exchange: ex.Exchange = getattr(ex, config.exchange.value)()

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        spot_tickers, swap_tickers = await asyncio.gather(
            self.exchange.fetch_tickers(params={"type": "spot"}),
            self.exchange.fetch_tickers(params={"type": "swap"}),
        )

        msg = f"**Price Diff Alert ({self.config.exchange.value})**\n"
        symbols = []
        mention = False
        for ticker in spot_tickers:
            swap_ticker = f"{ticker}:USDT"
            if swap_ticker not in swap_tickers:
                continue
            spot = spot_tickers[ticker]
            swap = swap_tickers[swap_ticker]

            if spot["quoteVolume"] < 200_000:
                continue

            diff_percent = (
                (swap["bid"] - spot["ask"]) / (swap["bid"] + spot["ask"])
            ) * 100
            if self.config.min_threshold < diff_percent < self.config.max_threshold:
                symbols.append((ticker, diff_percent))

        if mention:
            msg += "{{ mentions }}\n"
        msg += "\n".join([f"{sbl}: {pct:.2%}" for sbl, pct in symbols])

        self.send_discord_message(msg)
        self.send_telegram_message(msg)
