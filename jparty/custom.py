from jparty.game import Question, Board, Game
import csv


def csv_to_game(s):
    # Template link: https://docs.google.com/spreadsheets/d/1_vBBsWn-EVc7npamLnOKHs34Mc2iAmd9hOGSzxHQX0Y/edit?usp=sharing
    alpha = "BCDEFG"
    boards = []
    # gets single and double jeopardy rounds
    for n in [1, 14]:
        categories = s[n][1:6]
        questions = []
        # r is row; c is cell
        for r in range(5):
            for c in range(6):
                address = alpha[c] + str(r + n-1)
                index = (r, c)
                text = s[r+n][c+1]
                answer = s[r+n+6][c+1]
                value = int(s[r+n][0])
                dd = address in s[n-1][-1]
                if dd:
                    print(address)
                questions.append(Question(index, text, answer, value, dd))
        boards.append(Board(categories, questions, final=False, dj=(n == 14)))
    fj = s[-1]
    index = (0, 0)
    text = fj[2]
    answer = fj[3]
    questions = [Question(index, text, answer, None, False)]
    categories = [fj[1]]
    boards.append(Board(categories, questions, final=True, dj=False))
    date = fj[-4]
    comments = fj[-2]
    return Game(boards, date, comments)