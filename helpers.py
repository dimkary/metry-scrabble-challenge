from fastapi import HTTPException
import random
import json

random.seed(10)


def populateBoard(body):
    board = []
    cur_row = []
    isEmpty = True
    for item in body["board_state"]:
        cur_row.append(body["board_state"][item])
        if cur_row[-1] != "" and isEmpty:
            isEmpty = False

        if len(cur_row) == 15:
            board.append(cur_row.copy())
            cur_row = []
    print("Board is empty: ", isEmpty)
    return board, isEmpty


def dealLetters(body):
    # print("Hi from dealer")
    remaining = body["remaining"]
    _remaining = []
    player = body["player_turn"]
    p1_letters = body["p1"]
    p2_letters = body["p2"]
    # print("START IS: PLAYER " + player)
    assert len(p1_letters) <= 7 and len(p2_letters) <= 7

    for letter in remaining:
        amount = remaining[letter]
        if amount > 0:
            for _ in range(amount):
                _remaining.append(letter)

    # print("Remaining before\n", remaining)
    random.shuffle(_remaining)

    if len(p1_letters) == len(p2_letters) == 0:
        print("Initiating round")
        ### Deal for both players
        p1_letters = _remaining[:7].copy()
        p2_letters = _remaining[7:14].copy()
        ### remove from remaining
        for letter in p1_letters + p2_letters:
            remaining[letter] -= 1

        body["p1"] = p1_letters
        body["p2"] = p2_letters

    elif player == "p1":
        assert len(p2_letters) <= 7 and len(p1_letters) < 7
        to_deal = 7 - len(p1_letters)
        p1_letters += _remaining[:to_deal].copy()

        for letter in p1_letters:
            remaining[letter] -= 1

        body["p1"] = p1_letters
        body["player_turn"] = "p2"
        # print("WHY NOT CHANGING :", body["player_turn"])

    elif player == "p2":
        assert len(p1_letters) <= 7 and len(p2_letters) <= 7
        to_deal = 7 - len(p2_letters)
        p2_letters += _remaining[:to_deal].copy()

        for letter in p2_letters:
            remaining[letter] -= 1

        body["p2"] = p2_letters
        body["player_turn"] = "p1"
    else:
        raise Exception("Invalid player letters")

    # print("END IS: PLAYER " + body["player_turn"])

    with open("current_state.json", "w") as f:
        json.dump(body, f)

    return body


def validatePlayer(body, playload):
    ### stack 'p' in front of player attribute if missing
    if playload.player[0] != "p":
        playload.player = "p" + playload.player

    ### CHECK 1: player
    try:
        assert (playload.player == body["player_turn"]) and playload.player in [
            "p1",
            "p2",
        ]
    except:
        raise HTTPException(status_code=409, detail="Wrong player")

    return True


def playTurn(body, playload, points):
    player = body["player_turn"]
    score = body["{}_score".format(player)]
    board, boadIsEmpty = populateBoard(body)
    word = playload.word

    ##################################################################################
    ################################### ASSERTIONS ###################################
    ##################################################################################
    try:
        start = [int(i) for i in playload.start.split("-")]
        end = [int(i) for i in playload.end.split("-")]
    except ValueError:
        raise HTTPException(status_code=406, detail="Coordinates not valid numbers")
    available_letters = body[player]

    ### ASSERT 0: coordinates must be between 0-14

    try:
        assert (
            start[0] >= 0
            and end[0] >= 0
            and start[1] >= 0
            and end[1] >= 0
            and start[0] < 15
            and end[0] < 15
            and start[1] < 15
            and end[1] < 15
        ) and (sum(start) < sum(end))
    except:
        raise HTTPException(status_code=406, detail="Coordinates between 0 and 14")

    ### ASSERT 1: coordinates are either row or columns
    try:
        assert (start[0] == end[0] and start[1] != end[1]) or (
            start[1] == end[1] and start[0] != end[0]
        )
    except:
        raise HTTPException(
            status_code=406, detail="Word should be vertical or horizontal"
        )

    ### ASSERT 2: word letters should be a subset of the available letters

    ##### generate all coordinates #####
    if start[0] == end[0]:
        y_s = list(range(start[1], end[1] + 1))
        x_s = [start[0] for _ in range(len(y_s))]
    elif start[1] == end[1]:
        x_s = list(range(start[0], end[0] + 1))
        y_s = [start[1] for _ in range(len(x_s))]
    try:
        assert len(x_s) == len(word)
    except:
        raise HTTPException(
            status_code=406, detail="Length of the word doesn't match coordinates"
        )
    coords = list(zip(x_s, y_s))
    ##### Store occupied cells letters #####
    pre_occupied = []
    pre_occ_coord = []
    for cc in coords:
        if board[cc[0]][cc[1]] != "":
            pre_occupied.append(board[cc[0]][cc[1]])
            pre_occ_coord.append(cc)

    ### Invalid if board is occupied and player placed stuff elsewhere
    try:
        assert boadIsEmpty or pre_occupied != []
    except:
        raise HTTPException(
            status_code=406,
            detail="Illegal word placement. Need to be adjascent to existing words",
        )

    ##### Add them to the available letters (availablePlus) #####
    available_letters_plus = available_letters + pre_occupied
    # print(available_letters_plus)
    ##### word should be a subset of the availablePlus letters ####
    try:
        for _letter in set(word):
            # print(_letter, word.count(_letter), available_letters_plus.count(_letter))
            assert word.count(_letter) <= available_letters_plus.count(_letter)
    except:
        raise HTTPException(
            status_code=406, detail="Available letters cannot form current word"
        )

    ##################################################################################
    ################################# ASSERTIONS END #################################
    ##################################################################################

    # count points
    for letter, cc in zip(word, coords):
        if cc in pre_occ_coord:
            try:
                assert letter == body["board_state"]["{}-{}".format(cc[0], cc[1])]
            except:
                raise HTTPException(
                    status_code=406, detail="Cannot change placed tiles"
                )
        score += points[letter]
        # remove used letters
        available_letters_plus.remove(letter)
        body["board_state"]["{}-{}".format(cc[0], cc[1])] = letter

    ### Check that the player actually played something :-)
    try:
        assert sorted(available_letters_plus) != sorted(available_letters)
    except:
        raise HTTPException(status_code=406, detail="Player has not added any word")
    # print(board)
    # construct the body chaning ONLY the count and the used letters
    body["{}_score".format(player)] = score
    body[player] = available_letters_plus
    # write state
    with open("current_state.json", "w") as f:
        json.dump(body, f)
    return body
