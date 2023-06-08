from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plutous.trade.crypto.bots import WebhookBot, WebhookBotConfig

from .models import BotClosePost, BotTradePost

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
    )
    await WebhookBot(config=config)._run(
        action=trade.action,
        quantity=trade.quantity,
        prev_position_side=trade.prev_position_side,
        prev_position_size=trade.prev_position_size,
    )


@app.post("/bot/{bot_id}/close")
async def close_trade(bot_id: int, trade: BotClosePost):
    config = WebhookBotConfig(
        bot_id=bot_id,
        symbol=trade.symbol,
    )
    await WebhookBot(config=config).close_position(
        side=trade.side,
        quantity=trade.quantity,
    )
