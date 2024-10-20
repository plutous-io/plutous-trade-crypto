import asyncio

from loguru import logger

from plutous.trade.crypto import exchanges as ex

from .base import BaseAlert, BaseAlertConfig


class PriceDiffAlertConfig(BaseAlertConfig):
    frequency: None = None
    lookback: None = None
    min_threshold: float = 0.005
    max_threshold: float = 0.1
    volume_threshold: float = 1_000_000


class PriceDiffAlert(BaseAlert):
    config: PriceDiffAlertConfig

    def __init__(self, config: PriceDiffAlertConfig):
        self.config = config
        self.exchange: ex.Exchange = getattr(ex, config.exchange.value)()

    def run(self):
        logger.info("Running PriceDiffAlert")
        asyncio.run(self._run())

    async def _run(self):
        spot_tickers, swap_tickers = await asyncio.gather(
            self.exchange.fetch_tickers(params={"type": "spot"}),
            self.exchange.fetch_tickers(params={"type": "swap"}),
        )
        logger.info("Fetched spot and swap tickers")

        msg = f"**Price Diff Alert ({self.config.exchange.value})**\n"
        symbols = []
        mention = False
        for ticker in spot_tickers:
            swap_ticker = f"{ticker}:USDT"
            if swap_ticker not in swap_tickers:
                continue
            spot = spot_tickers[ticker]
            swap = swap_tickers[swap_ticker]

            if spot["quoteVolume"] < self.config.volume_threshold:
                continue

            diff_percent = (swap["bid"] - spot["ask"]) / (
                (swap["bid"] + spot["ask"]) / 2
            )
            if self.config.min_threshold < diff_percent < self.config.max_threshold:
                symbols.append(
                    (
                        ticker,
                        diff_percent,
                        spot["quoteVolume"],
                        swap["info"]["fundingRate"],
                    )
                )

        if not symbols:
            await self.exchange.close()
            return

        symbols.sort(key=lambda x: x[-1], reverse=True)

        if mention:
            msg += "{{ mentions }}\n"
        msg += "\n".join(
            [
                f"{sbl}: {pct:.2%}, vol: {vol:.2f}, fr: {float(fr):.4%}"
                for sbl, pct, vol, fr in symbols
            ]
        )

        logger.info(msg)

        self.send_discord_message(msg)
        self.send_telegram_message(msg)

        await self.exchange.close()
