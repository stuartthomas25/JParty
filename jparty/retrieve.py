import requests
from bs4 import BeautifulSoup
import re
from threading import Thread
from queue import Queue
from jparty.game import Question, Board, FinalBoard, GameData
import logging
import csv


import pickle

monies = [[200, 400, 600, 800, 1000], [400, 800, 1200, 1600, 2000]]

def list_to_game(s):
    # Template link: https://docs.google.com/spreadsheets/d/1_vBBsWn-EVc7npamLnOKHs34Mc2iAmd9hOGSzxHQX0Y/edit?usp=sharing
    alpha = "BCDEFG"
    boards = []
    # gets single and double jeopardy rounds
    for n1 in [1, 14]:
        categories = s[n1-1][1:7]
        questions = []
        for row in range(5):
            for col,cat in enumerate(categories):
                address = alpha[col] + str(row + n1 + 1)
                index = (col, row)
                text = s[row + n1][col + 1]
                answer = s[row + n1 + 6][col + 1]
                value = int(s[row + n1][0])
                dd = address in s[n1 - 1][-1]
                questions.append(Question(index, text, answer, value, dd))
                print(index, text, answer, value, dd)
        boards.append(Board(categories, questions, dj=(n1 == 14)))
    # gets final jeopardy round
    fj = s[-1]
    index = (0, 0)
    text = fj[2]
    answer = fj[3]
    category = fj[1]
    question = Question(index, text, answer, category)
    boards.append(FinalBoard(category, question))
    date = fj[5]
    comments = fj[7]
    return GameData(boards, date, comments)


def get_Gsheet_game(file_id):
    csv_url = f'https://docs.google.com/spreadsheet/ccc?key={file_id}&output=csv'
    with requests.get(csv_url, stream=True) as r:
        lines = (line.decode('utf-8') for line in r.iter_lines())
        r3 = csv.reader(lines)
        return list_to_game(list(r3))


def get_game(game_id):
    if len(str(game_id)) < 7:
        return get_JArchive_Game(game_id)
    else:
        return get_Gsheet_game(str(game_id))


def get_JArchive_Game(game_id, soup=None):
    logging.info(f"getting game {game_id}")

    r = requests.get(f"http://www.j-archive.com/showgame.php?game_id={game_id}")
    soup = BeautifulSoup(r.text, "html.parser")
    date = re.search(
        r"- \w+, (.*?)$", soup.select("#game_title > h1")[0].contents[0]
    ).groups()[0]
    comments = soup.select("#game_comments")[0].contents
    comments = comments[0] if len(comments) > 0 else ""

    # Normal Roudns
    boards = []
    rounds = soup.find_all(class_="round")
    for i, ro in enumerate(rounds):
        categories_objs = ro.find_all(class_="category")
        categories = [c.find(class_="category_name").text for c in categories_objs]
        questions = []
        for clue in ro.find_all(class_="clue"):
            text_obj = clue.find(class_="clue_text")
            if text_obj is None:
                logging.info("this game is incomplete")
                continue

            text = text_obj.text
            index_key = text_obj["id"]
            index = (int(index_key[-3]) - 1, int(index_key[-1]) - 1) # get index from id string
            js = clue.find("div")["onmouseover"]
            dd = clue.find(class_="clue_value_daily_double") is not None
            value = monies[i][index[1]]
            answer = re.findall(r'correct_response">(.*?)</em', js.replace("\\", ""))[0]
            questions.append(Question(index, text, answer, categories[index[0]], value, dd))

        boards.append(Board(categories, questions, dj=(i == 1)))


    # Final jeopardy
    fro = soup.find_all(class_="final_round")[0]
    category_obj = fro.find_all(class_="category")[0]
    category = category_obj.find(class_="category_name").text
    clue = fro.find_all(class_="clue")[0]
    text_obj = clue.find(class_="clue_text")
    if text_obj is None:
        logging.info("this game is incomplete")

    text = text_obj.text
    index_key = text_obj["id"]
    js = list(clue.parents)[1].find("div")["onmouseover"]
    answer = re.findall(r'correct_response">(.*?)</em', js.replace("\\", ""))[0]
    question = Question((0,0), text, answer, category)

    boards.append(FinalBoard(category, question))


    return GameData(boards, date, comments)

def get_game_sum(soup):
    date = re.search(
        r"- \w+, (.*?)$", soup.select("#game_title > h1")[0].contents[0]
    ).groups()[0]
    comments = soup.select("#game_comments")[0].contents

    return date, comments


def get_random_game():
    r = requests.get("http://j-archive.com/")
    soup = BeautifulSoup(r.text, "html.parser")

    link = soup.find_all(class_="splash_clue_footer")[1].find("a")["href"]
    return int(link[21:])
