from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plutous.trade.crypto.bots import WebhookBot, WebhookBotConfig

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
async def create_trade(bot_id: int, trade: BotTradePost):
    config = WebhookBotConfig(
        bot_id=bot_id,
        symbol=trade.symbol,
        action=trade.action,
        quantity=trade.quantity,
    )
    await WebhookBot(config=config)._run()
