from fastapi import FastAPI, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
import json
from helpers import *

### Specify a play body scema ###
class Play(BaseModel):
    player: str
    word: str
    start: str
    end: str


templates = Jinja2Templates(directory="templates/")

app = FastAPI(reload=True, debug=True)

print("Started server")

with open("letters.json") as f:
    DEFAULT_BAG = json.load(f)

POINTS = {}

for letter in DEFAULT_BAG["letters"]:
    POINTS[letter] = DEFAULT_BAG["letters"][letter]["points"]

with open("initial_state.json") as f:
    INITIAL_STATE = json.load(f)

try:
    with open("current_state.json") as f:
        CURRENT_STATE = json.load(f)
    ### Check if current state is default, then we initiate the first dealing
    if (
        CURRENT_STATE["p1_score"]
        == CURRENT_STATE["p2_score"]
        == len(CURRENT_STATE["p2"])
        == len(CURRENT_STATE["p1"])
        == 0
    ):
        CURRENT_STATE = dealLetters(INITIAL_STATE)
except FileNotFoundError:
    CURRENT_STATE = dealLetters(INITIAL_STATE)


@app.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def root():
    return "<h1> Welcome to Scramble </h1>"


###### NEED TO RETURN EVERYTHING IN THE REQUIREMENTS ####
@app.get("/currentstate/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def root(request: Request):
    playing = CURRENT_STATE["player_turn"]
    players_letters = CURRENT_STATE[CURRENT_STATE["player_turn"]]

    return templates.TemplateResponse(
        "state.html",
        {
            "request": request,
            "playing": playing,
            "players_letters": players_letters,
            "board": populateBoard(CURRENT_STATE)[0],
            "p1_score": CURRENT_STATE["p1_score"],
            "p2_score": CURRENT_STATE["p2_score"],
        },
    )


@app.post("/play/")
async def play(
    play: Play, response_class=HTMLResponse, status_code=status.HTTP_202_ACCEPTED
):
    global CURRENT_STATE
    validatePlayer(CURRENT_STATE, play)
    CURRENT_STATE = playTurn(CURRENT_STATE, play, POINTS)
    CURRENT_STATE = dealLetters(CURRENT_STATE)

    ### Check termination ###
    remainings = set(CURRENT_STATE["remaining"].values())
    if remainings == {0}:
        msg = "GAME OVER"
        if CURRENT_STATE["p1_score"] == CURRENT_STATE["p2_score"]:
            msg2 = "TIE GAME"
        elif CURRENT_STATE["p1_score"] > CURRENT_STATE["p2_score"]:
            msg2 = "PLAYER 1 WON"
        else:
            msg2 = "PLAYER 2 WON"
        CURRENT_STATE = dealLetters(INITIAL_STATE)
        print(msg, msg2)
        return HTMLResponse(
            content="<h1>{}<h1><h1>{}<h1>".format(msg, msg2), status_code=200
        )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
