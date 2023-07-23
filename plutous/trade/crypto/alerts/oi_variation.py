from plutous.trade.crypto.models import OpenInterest

from .base import BaseAlert, BaseAlertConfig


class OIVariationAlertConfig(BaseAlertConfig):
    threshold: float = 0.1


class OIVariationAlert(BaseAlert):
    __tables__ = [OpenInterest]

    config: OIVariationAlertConfig

    def __init__(self, config: OIVariationAlertConfig):
        base_alert_config = BaseAlertConfig(**config.dict())
        base_alert_config.lookback += 1
        super().__init__(base_alert_config)
        self.config = config

    def run(self):
        if self.config.lookback < 2:
            raise ValueError("Lookback cannot be less than 2")

        df = self.data[OpenInterest.__tablename__]
        df = (df / df.shift(self.config.lookback - 1) - 1).iloc[
            -1 * self.config.lookback :
        ]
        df_latest = df.iloc[-1]
        df_last = df.iloc[-2]
        df_latest = df_latest[df_latest > self.config.threshold]
        df_last = df_last[df_last > self.config.threshold]
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

        msg = f"**OI Variation Alert ({self.config.exchange.value}) (last {interval}{frequnecy})**\n"
        symbols = []
        mention = False
        for symbol, pct in df_latest.items():
            if symbol not in df_last:
                symbol = f"**{symbol}**"
                mention = True
            symbols.append((symbol, pct))

        if mention:
            msg += "{{ mentions }}\n"
        msg += "\n".join([f"{sbl}: {pct:.2%}" for sbl, pct in symbols])

        self.send_discord_message(msg)
        self.send_telegram_message(msg)
