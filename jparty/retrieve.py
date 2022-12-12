import requests
from bs4 import BeautifulSoup
import re
from threading import Thread
from queue import Queue
from jparty.game import Question, Board, Game
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
            for col in range(6):
                address = alpha[col] + str(row + n1 + 1)
                index = (col, row)
                text = s[row + n1][col + 1]
                answer = s[row + n1 + 6][col + 1]
                value = int(s[row + n1][0])
                dd = address in s[n1 - 1][-1]
                questions.append(Question(index, text, answer, value, dd))
                print(index, text, answer, value, dd)
        boards.append(Board(categories, questions, final=False, dj=(n1 == 14)))
    # gets final jeopardy round
    fj = s[-1]
    index = (0, 0)
    text = fj[2]
    answer = fj[3]
    questions = [Question(index, text, answer, None, False)]
    categories = [fj[1]]
    boards.append(Board(categories, questions, final=True, dj=False))
    date = fj[5]
    comments = fj[7]
    return Game(boards, date, comments)


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

    # boards = pickle.load(open("board_download.dat",'rb'))
    # return Game(boards)

    r = requests.get(f"http://www.j-archive.com/showgame.php?game_id={game_id}")
    soup = BeautifulSoup(r.text, "html.parser")
    date = re.search(
        r"- \w+, (.*?)$", soup.select("#game_title > h1")[0].contents[0]
    ).groups()[0]
    comments = soup.select("#game_comments")[0].contents
    comments = comments[0] if len(comments) > 0 else ""

    rounds = soup.find_all(class_="round") + soup.find_all(class_="final_round")
    boards = []
    for i, ro in enumerate(rounds):
        final = ro["class"][0] == "final_round"
        categories_objs = ro.find_all(class_="category")
        categories = [c.find(class_="category_name").text for c in categories_objs]
        questions = []
        for clue in ro.find_all(class_="clue"):
            text_obj = clue.find(class_="clue_text")
            if text_obj is None:
                # logging.info("this game is incomplete")
                continue
            # else:
            # logging.info("complete")
            text = text_obj.text
            index_key = text_obj["id"]
            if not final:
                index = (int(index_key[-3]) - 1, int(index_key[-1]) - 1)
                js = clue.find("div")["onmouseover"]
                dd = clue.find(class_="clue_value_daily_double") is not None
                value = monies[i][index[1]]
            else:
                index = (0, 0)
                js = list(clue.parents)[1].find("div")["onmouseover"]
                value = None
                dd = False
            answer = re.findall(r'correct_response">(.*?)</em', js.replace("\\", ""))[0]
            questions.append(Question(index, text, answer, value, dd))
        boards.append(Board(categories, questions, final=final, dj=(i == 1)))
    logging.info(f"Boards {len(boards)}")

    return Game(boards, date, comments)

    # def get_all_games():
    #     r = requests.get("http://j-archive.com/listseasons.php")
    #     soup = BeautifulSoup(r.text, "html.parser")
    #     seasons = soup.find_all("tr")

    #     # Using Queue
    #     concurrent = 40
    #     game_ids = []

    #     def send_requests():
    #         while True:
    #             url = q.get()
    #             season_r = requests.get("http://j-archive.com/" + url)
    #             season_soup = BeautifulSoup(season_r.text, "html.parser")
    #             for game in season_soup.find_all("tr"):
    #                 if game:
    #                     game_id = int(
    #                         re.search(r"(\d+)\s*$", game.find("a")["href"]).groups()[0]
    #                     )
    #                     game_ids.append(game_id)
    #             q.task_done()

    #     q = Queue(concurrent * 2)
    #     for _ in range(concurrent):
    #         t = Thread(target=send_requests)
    #         t.daemon = True
    #         t.start()
    #     for season in seasons:
    #         link = season.find("a")["href"]
    #         q.put(link)
    #     q.join()
    #     games_info = {}
    # game_ids = []
    # for season in seasons:
    # link = season.find('a')['href']
    # print(link)
    # season_r = requests.get("http://j-archive.com/"+link)
    # season_soup = BeautifulSoup(season_r.text, 'html.parser')
    # for game in season_soup.find_all("tr"):
    # if game:
    # game_id = int(re.search(r'(\d+)\s*$', game.find('a')['href']).groups()[0])
    # game_ids.append(game_id)
    # #                 game_date = re.search(r'([\-\d]*)$', str(game.find('a').contents[0])).groups()[0]
    # # summary = re.search(r'^\s+(.*)\s+$', game.find_all('td')[-1].contents[0])
    # # stripped_summary = '' if summary is None else summary.groups()[0]
    # # games_info[game_id] = game_date + ': ' + stripped_summary

    # return game_ids


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

# def getStatus(ourl):
# try:
# url = urlparse(ourl)
# conn = httplib.HTTPConnection(url.netloc)
# conn.request("HEAD", url.path)
# res = conn.getresponse()
# return res.status, ourl
# except:
# return "error", ourl
