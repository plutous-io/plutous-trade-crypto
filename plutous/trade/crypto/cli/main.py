import asyncio

from typer import Context, Typer

from plutous.cli.utils import parse_context_args
from plutous.enums import Exchange
from plutous.trade.crypto.collectors import COLLECTORS
from plutous.trade.crypto.enums import CollectorType

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
def collect(
    exchange: Exchange,
    collector_type: CollectorType,
    ctx: Context,
):
    """Collect data from exchange."""
    collector = COLLECTORS[collector_type](exchange, **parse_context_args(ctx))
    asyncio.run(collector.collect())
