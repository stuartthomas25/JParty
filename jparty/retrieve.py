import requests
from bs4 import BeautifulSoup
import re
from threading import Thread
from queue import Queue
from .game import Question, Board, Game

import pickle

monies = [200, 400, 600, 800, 1000]


def get_game(game_id, soup=None):
    print(f"getting game {game_id}")

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
                # print("this game is incomplete")
                continue
            # else:
            # print("complete")
            text = text_obj.text
            index_key = text_obj["id"]
            if not final:
                index = (int(index_key[-3]) - 1, int(index_key[-1]) - 1)
                js = clue.find("div")["onmouseover"]
                value = monies[index[1]]
            else:
                index = (0, 0)
                js = list(clue.parents)[1].find("div")["onmouseover"]
                value = None
            answer = re.findall(r'correct_response">(.*?)</em', js.replace("\\", ""))[0]
            questions.append(Question(index, text, answer, value))
        boards.append(Board(categories, questions, final=final, dj=i == 1))

    return Game(boards, date, comments)


def get_all_games():
    r = requests.get("http://j-archive.com/listseasons.php")
    soup = BeautifulSoup(r.text, "html.parser")
    seasons = soup.find_all("tr")

    # Using Queue
    concurrent = 40
    game_ids = []

    def send_requests():
        while True:
            url = q.get()
            season_r = requests.get("http://j-archive.com/" + url)
            season_soup = BeautifulSoup(season_r.text, "html.parser")
            for game in season_soup.find_all("tr"):
                if game:
                    game_id = int(
                        re.search(r"(\d+)\s*$", game.find("a")["href"]).groups()[0]
                    )
                    game_ids.append(game_id)
            q.task_done()

    q = Queue(concurrent * 2)
    for _ in range(concurrent):
        t = Thread(target=send_requests)
        t.daemon = True
        t.start()
    for season in seasons:
        link = season.find("a")["href"]
        q.put(link)
    q.join()
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

    return game_ids


def get_game_sum(soup):
    date = re.search(
        r"- \w+, (.*?)$", soup.select("#game_title > h1")[0].contents[0]
    ).groups()[0]
    comments = soup.select("#game_comments")[0].contents

    return date, comments


# def getStatus(ourl):
# try:
# url = urlparse(ourl)
# conn = httplib.HTTPConnection(url.netloc)
# conn.request("HEAD", url.path)
# res = conn.getresponse()
# return res.status, ourl
# except:
# return "error", ourl
