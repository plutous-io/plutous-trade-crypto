import asyncio
from datetime import datetime
from typing import Type

import pandas as pd
from typer import Context, Option, Typer
from typing_extensions import Annotated

from plutous.cli.utils import parse_context_args
from plutous.enums import Exchange
from plutous.trade.crypto import alerts
from plutous.trade.crypto.collectors import COLLECTORS
from plutous.trade.crypto.enums import CollectorType

from . import database

app = Typer(name="crypto")
apps = [database.app]

for a in apps:
    app.add_typer(a)


@app.command()
def collect(
    exchange: Exchange,
    collector_type: CollectorType,
    rate_limit: Annotated[bool, Option()] = False,
):
    """Collect data from exchange."""
    collector = COLLECTORS[collector_type](exchange, rate_limit)
    asyncio.run(collector.collect())


@app.command()
def backfill(
    exchange: Exchange,
    collector_type: CollectorType,
    rate_limit: Annotated[bool, Option()] = False,
    lookback: Annotated[str, Option()] = "1h",
):
    """Backfill last 1-hour data from exchange."""
    collector = COLLECTORS[collector_type](exchange, rate_limit)

    since = datetime.now() - pd.Timedelta(lookback).to_pytimedelta()
    asyncio.run(collector.backfill(since))


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
def alert(
    alert_type: str,
    ctx: Context,
):
    """Alert on data from exchange."""
    alert_cls: Type[alerts.BaseAlert] = getattr(alerts, f"{alert_type}Alert")
    alert_config_cls: Type[alerts.BaseAlertConfig] = getattr(
        alerts, f"{alert_type}AlertConfig"
    )

    config = alert_config_cls(**parse_context_args(ctx))
    alert = alert_cls(config)
    alert.run()
