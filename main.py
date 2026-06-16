from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from blackjack import Blackjack

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

game = Blackjack()


@app.get("/")
def root():
    return FileResponse("static/index.html")


class SessionRequest(BaseModel):
    player_name: str = ""
    capital: int


class RoundRequest(BaseModel):
    bets: list[int]


class EarlyPayRequest(BaseModel):
    choice: str  # Take or wait.


class InsuranceRequest(BaseModel):
    insured_hands: list[str]  # Hand ordinals that buy insurance.


@app.post("/session/new")
def new_session(req: SessionRequest):
    return game.new_session(req.player_name, req.capital)


@app.post("/round/start")
def start_round(req: RoundRequest):
    return game.start_round(req.bets)


@app.post("/round/early_pay")
def early_pay(req: EarlyPayRequest):
    return game.make_early_pay_decision(req.choice)


@app.post("/round/insurance")
def insurance(req: InsuranceRequest):
    return game.make_insurance_decision(req.insured_hands)


@app.post("/round/hit")
def hit():
    return game.hit()


@app.post("/round/stand")
def stand():
    return game.stand()


@app.post("/round/double")
def double():
    return game.double_down()


@app.post("/round/split")
def split():
    return game.split()


@app.post("/round/surrender")
def surrender():
    return game.surrender()


@app.get("/income")
def income():
    return game.get_incomes()


_ALLOWED_LANGS = {"english", "traditional", "simplified"}

@app.get("/rules/{lang}")
def get_rules(lang: str):
    if lang not in _ALLOWED_LANGS:
        return {"error": "Unknown language."}
    return {"content": Path(f"rules/{lang}.txt").read_text(encoding="utf-8")}
