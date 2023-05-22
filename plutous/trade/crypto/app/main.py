from fastapi import FastAPI, Depends

from plutous.app.utils.session import Session, get_session

from plutous.trade.crypto.commands.bot import WebhookBotCreateOrder

from .models import BotTradePost

app = FastAPI(
    title="Plutous Crypto API",
    version="0.0.1",
)

@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/bot/{bot_id}/trade")
async def create_trade(
    bot_id: int,
    trade: BotTradePost,
    session: Session = Depends(get_session),
):
    await WebhookBotCreateOrder(
        bot_id=bot_id,
        symbol=trade.symbol,
        action=trade.action,
    ).execute(session)
