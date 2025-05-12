from loguru import logger

from plutous.trade.crypto.models import FundingRate

from .base import BaseAlert, BaseAlertConfig


class FRVariationAlertConfig(BaseAlertConfig):
    threshold: float = 0.01  # Default threshold for significant funding rate change


class FRVariationAlert(BaseAlert):
    __tables__ = [FundingRate]

    config: FRVariationAlertConfig

    def run(self):
        if self.config.lookback < 2:
            raise ValueError("Lookback cannot be less than 2")

        df = self.data[FundingRate.__tablename__]
        df = df.swaplevel(axis=1)
        df = df["funding_rate"] * 8 / df["funding_interval"]
        diff = df.iloc[-1] - df.iloc[0]
        symbols = diff[
            (diff < -1 * self.config.threshold) & (df.iloc[-1] < 0)
        ].sort_values(ascending=True)
        if symbols.empty:
            return

        interval, frequency = (
            int(self.config.frequency[:-1]) * (self.config.lookback),
            self.config.frequency[-1].replace("m", "min").replace("h", "hr"),
        )
        if (interval >= 60) & (frequency == "min"):
            if interval % 60 == 0:
                frequency = "hr"
                interval = interval // 60

        msg = f"**Funding Rate Variation Alert ({self.config.exchange.value}) (last {interval}{frequency})**\n"
        msg += "\n".join([f"{sbl}: {diff:.4f}" for sbl, diff in symbols.items()])

        logger.info(msg)
        self.send_discord_message(msg)
        self.send_telegram_message(msg)
