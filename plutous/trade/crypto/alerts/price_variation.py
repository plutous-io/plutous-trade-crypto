from plutous.trade.crypto.models import OHLCV

from .base import BaseAlert, BaseAlertConfig


class PriceVariationAlertConfig(BaseAlertConfig):
    threshold: float = 0.03


class PriceVariationAlert(BaseAlert):
    __tables__ = [OHLCV]

    config: PriceVariationAlertConfig

    def run(self):
        if self.config.lookback < 2:
            raise ValueError("Lookback cannot be less than 2")

        df = self.data[OHLCV.__tablename__]
        df = df.swaplevel(axis=1).close
        df = (df / df.shift(self.config.lookback - 1) - 1).iloc[
            -1 * self.config.lookback :
        ]
        df_latest = df.iloc[-1]
        df_latest = df_latest[df_latest.abs() > self.config.threshold]
        if df_latest.empty:
            return

        interval, frequnecy = (
            int(self.config.frequency[:-1]) * (self.config.lookback - 1),
            self.config.frequency[-1].replace("m", "min").replace("h", "hr"),
        )
        if (interval >= 60) & (frequnecy == "min"):
            if interval % 60 == 0:
                frequnecy = "hr"
                interval = interval // 60

        msg = f"**Price Variation Alert ({self.config.exchange.value}) (last {interval}{frequnecy})**\n"
        msg += "\n".join([f"{sbl}: {pct:.2%}" for sbl, pct in df_latest.items()])

        self.send_discord_message(msg)
        self.send_telegram_message(msg)
