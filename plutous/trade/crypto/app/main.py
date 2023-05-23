from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from plutous.app.utils.session import get_session
from plutous.trade.crypto.commands.bot import WebhookBotCreateOrder

from .models import BotTradePost

app = FastAPI(
    title="Plutous Crypto API",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
