from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app import Application

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

game = Application()


@app.get("/")
def root():
    return FileResponse("static/index.html")


class SessionRequest(BaseModel):
    player_name: str = ""
    capital: int


class RoundRequest(BaseModel):
    bets: list[int]


class EarlyPayRequest(BaseModel):
    choice: str  # "take" | "wait"


@app.post("/session/new")
def new_session(req: SessionRequest):
    return game.new_session(req.player_name, req.capital)


@app.post("/round/start")
def start_round(req: RoundRequest):
    return game.start_round(req.bets)


@app.post("/round/early_pay")
def early_pay(req: EarlyPayRequest):
    return game.make_early_pay_decision(req.choice)


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
