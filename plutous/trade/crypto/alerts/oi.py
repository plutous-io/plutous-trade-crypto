from plutous.trade.crypto.models import OpenInterest

from .base import BaseAlert, BaseAlertConfig


class OIAlertConfig(BaseAlertConfig):
    threshold: float = 0.1


class OIAlert(BaseAlert):
    __tables__ = [OpenInterest]

    config: OIAlertConfig

    def run(self):
        if self.config.lookback < 2:
            raise ValueError("Lookback cannot be less than 2")

        df = self.data[OpenInterest.__tablename__]
        df = df.iloc[-1] / df.iloc[0] - 1
        df = df[df > self.config.threshold]
        if df.empty:
            return

        interval, frequnecy = (
            int(self.config.frequency[:-1]) * (self.config.lookback - 1),
            self.config.frequency[-1].replace("m", "min").replace("h", "hr"),
        )
        if (interval >= 60) & (frequnecy == "min"):
            if interval % 60 == 0:
                frequnecy = "hr"
                interval = interval // 60

        msg = f"**OI Variation Alert (last {interval}{frequnecy})** \n"
        for symbol, pct in df.items():
            msg += f"{symbol.split(':')[0]}: {pct:.2%} \n"

        self.send_discord_message(msg)
        self.send_telegram_message(msg)
