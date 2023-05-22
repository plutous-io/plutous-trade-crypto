from fastapi import FastAPI, Depends

from plutous.app.utils.session import Session, get_session
from plutous.trade.models import Strategy

from plutous.trade.crypto import exchanges as ex

from .models import TradePost

app = FastAPI(
    title="Plutous Crypto API",
    version="0.0.1",
)

@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/trade", response_model=TradePost)
async def trade(
    trade: TradePost,
    session: Session = Depends(get_session),
):
    strategy = session.query(Strategy).filter_by(id=trade.strategy_id).one()
    exchange: ex.Exchange = getattr(ex, trade.exchange.value)
    await exchange.create_order(trade)
    return trade

