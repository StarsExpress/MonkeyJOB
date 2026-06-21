from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from blackjack import Blackjack

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

sessions: dict[str, Blackjack] = {}


def get_game(session_id: str) -> Blackjack:
    game = sessions.get(session_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return game


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
    session_id = str(uuid4())
    game = Blackjack()
    result = game.new_session(req.player_name, req.capital)
    if "error" not in result:
        sessions[session_id] = game
        result["session_id"] = session_id
    return result


@app.post("/round/start")
def start_round(req: RoundRequest, session_id: str):
    return get_game(session_id).start_round(req.bets)


@app.post("/round/early_pay")
def early_pay(req: EarlyPayRequest, session_id: str):
    return get_game(session_id).make_early_pay(req.choice)


@app.post("/round/insurance")
def insurance(req: InsuranceRequest, session_id: str):
    return get_game(session_id).make_insurance_decision(req.insured_hands)


@app.post("/round/hit")
def hit(session_id: str):
    return get_game(session_id).hit()


@app.post("/round/stand")
def stand(session_id: str):
    return get_game(session_id).stand()


@app.post("/round/double")
def double(session_id: str):
    return get_game(session_id).double_down()


@app.post("/round/split")
def split(session_id: str):
    return get_game(session_id).split()


@app.post("/round/surrender")
def surrender(session_id: str):
    return get_game(session_id).surrender()


@app.get("/income")
def income(session_id: str):
    return get_game(session_id).get_incomes()


_ALLOWED_LANGS = {"english", "traditional", "simplified"}

@app.get("/rules/{lang}")
def get_rules(lang: str):
    if lang not in _ALLOWED_LANGS:
        return {"error": "Unknown language."}
    return {"content": Path(f"rules/{lang}.txt").read_text(encoding="utf-8")}
