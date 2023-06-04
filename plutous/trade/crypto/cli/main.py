import asyncio

from typer import Typer

from plutous.enums import Exchange
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
):
    """Collect data from exchange."""
    collector = COLLECTORS[collector_type](exchange)
    asyncio.run(collector.collect())
