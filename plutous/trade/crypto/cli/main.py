from datetime import datetime
from typing import Type

import pandas as pd
from typer import Context, Typer

from plutous.cli.utils import parse_context_args
from plutous.trade.crypto import alerts, collectors

from . import database

app = Typer(name="crypto")
apps = [database.app]

for a in apps:
    app.add_typer(a)


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
@app.command()
def collect(collector_type: str, ctx: Context):
    collector_cls: Type[collectors.BaseCollector] = getattr(
        collectors, f"{collector_type}Collector"
    )
    collector_config_cls: Type[collectors.BaseCollectorConfig] = getattr(
        collectors, f"{collector_type}CollectorConfig"
    )
    collector = collector_cls(collector_config_cls(**parse_context_args(ctx)))
    collector.collect()


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
@app.command()
def backfill(collector_type: str, ctx: Context):
    collector_cls: Type[collectors.BaseCollector] = getattr(
        collectors, f"{collector_type}Collector"
    )
    collector_config_cls: Type[collectors.BaseCollectorConfig] = getattr(
        collectors, f"{collector_type}CollectorConfig"
    )
    context = parse_context_args(ctx)
    assert "lookback" in context
    collector = collector_cls(collector_config_cls(**context))
    since = datetime.now() - pd.Timedelta(context["lookback"]).to_pytimedelta()
    d = (
        pd.Timedelta(context["duration"]).to_pytimedelta()
        if context.get("duration")
        else None
    )
    collector.backfill(since, d)


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
def alert(alert_type: str, ctx: Context):
    """Alert on data from exchange."""
    alert_cls: Type[alerts.BaseAlert] = getattr(alerts, f"{alert_type}Alert")
    alert_config_cls: Type[alerts.BaseAlertConfig] = getattr(
        alerts, f"{alert_type}AlertConfig"
    )

    config = alert_config_cls(**parse_context_args(ctx))
    alert = alert_cls(config)
    alert.run()
