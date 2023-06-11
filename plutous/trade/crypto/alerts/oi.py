from plutous.trade.crypto.models import OpenInterest

from .base import BaseAlert, BaseAlertConfig


class OIAlertConfig(BaseAlertConfig):
    threshold: float = 0.1


class OIAlert(BaseAlert):
    __tables__ = [OpenInterest]

    config: OIAlertConfig

    def run(self):
        df = self.data[OpenInterest.__tablename__]
        df = df.pct_change().iloc[-1]
        df = df[df>self.config.threshold]
        if df.empty:
            return
        
        frequency = self.config.frequency.replace('m', 'min').replace('h', 'hr')
        msg = f"**Open Interest Alert ({frequency})** \n"
        for symbol, pct in df.items():
            msg += f"{symbol.split(':')[0]}: {pct:.2%} \n"

        self.send_discord_message(msg)
        self.send_telegram_message(msg)