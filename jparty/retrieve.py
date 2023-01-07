import requests
from bs4 import BeautifulSoup
import re
import json
from jparty.game import Question, Board, FinalBoard, GameData
import logging
import csv
from jparty.constants import MONIES


def list_to_game(s):
    # Template link: https://docs.google.com/spreadsheets/d/1_vBBsWn-EVc7npamLnOKHs34Mc2iAmd9hOGSzxHQX0Y/edit?usp=sharing
    alpha = "BCDEFG"  # columns
    boards = []
    # gets single and double jeopardy rounds
    for n1 in [1, 14]:
        categories = s[n1 - 1][1:7]
        questions = []
        for row in range(5):
            for col, cat in enumerate(categories):
                address = alpha[col] + str(row + n1 + 1)
                index = (col, row)
                text = s[row + n1][col + 1]
                answer = s[row + n1 + 6][col + 1]
                value = int(s[row + n1][0])
                dd = address in s[n1 - 1][-1]
                questions.append(Question(index, text, answer, cat, value, dd))

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
    csv_url = f"https://docs.google.com/spreadsheet/ccc?key={file_id}&output=csv"
    with requests.get(csv_url, stream=True) as r:
        lines = (line.decode("utf-8") for line in r.iter_lines())
        r3 = csv.reader(lines)
        return list_to_game(list(r3))


def get_game(game_id):
    if len(str(game_id)) < 7:
        return get_wayback_jarchive_game(game_id)
    else:
        return get_Gsheet_game(str(game_id))

def get_JArchive_Game(game_id, soup=None, is_wayback=False, wayback_url=None):
    logging.info(f"getting game {game_id}")
    if is_wayback:
        r = requests.get(wayback_url)
    else:
        r = requests.get(f"http://www.j-archive.com/showgame.php?game_id={game_id}")
    soup = BeautifulSoup(r.text, "html.parser")
    datesearch = re.search(
        r"- \w+, (.*?)$", soup.select("#game_title > h1")[0].contents[0]
    )
    if datesearch is None:
        return None
    date = datesearch.groups()[0]
    comments = soup.select("#game_comments")[0].contents
    comments = comments[0] if len(comments) > 0 else ""

    # Normal Rounds
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
                return None

            text = text_obj.text
            index_key = text_obj["id"]
            index = (
                int(index_key[-3]) - 1,
                int(index_key[-1]) - 1,
            )  # get index from id string
            js = clue.find("div")["onmouseover"]
            dd = clue.find(class_="clue_value_daily_double") is not None
            value = MONIES[i][index[1]]
            answer = re.findall(r'correct_response">(.*?)</em', js.replace("\\", ""))[0]
            print(text)
            questions.append(
                Question(index, text, answer, categories[index[0]], value, dd)
            )

        boards.append(Board(categories, questions, dj=(i == 1)))

    # Final Jeopardy
    fro = soup.find_all(class_="final_round")[0]
    category_obj = fro.find_all(class_="category")[0]
    category = category_obj.find(class_="category_name").text
    clue = fro.find_all(class_="clue")[0]
    text_obj = clue.find(class_="clue_text")
    if text_obj is None:
        logging.info("this game is incomplete")
        return None

    text = text_obj.text
    index_key = text_obj["id"]
    js = list(clue.parents)[1].find("div")["onmouseover"]
    answer = re.findall(r'correct_response">(.*?)</em', js.replace("\\", ""))[0]
    question = Question((0, 0), text, answer, category)

    boards.append(FinalBoard(category, question))

    return GameData(boards, date, comments)


def get_wayback_jarchive_game(game_id):
    # kudos to Abhi Kumbar: https://medium.com/analytics-vidhya/the-wayback-machine-scraper-63238f6abb66
    # this query's the wayback cdx api for possible instances of the saved jarchive page with the specified game id & returns the latest one
    JArchive_url = f"j-archive.com/showgame.php?game_id={str(game_id)}"  # use the url w/o the http:// or https:// to include both in query
    url = f'http://web.archive.org/cdx/search/cdx?url={JArchive_url}&collapse=digest&limit=-2&fastLatest=true&output=json'  # for some reason, using limit=-1 does not work
    urls = requests.get(url).text
    parse_url = json.loads(urls)  # parses the JSON from urls.
    if len(parse_url) == 0:  # if no results, return None
        logging.info("no games found in wayback")
        # return None
        # alternative: use fallback to get game from scraping j-archive directly
        return get_JArchive_Game(game_id)

    ## Extracts timestamp and original columns from urls and compiles a url list.
    url_list = []
    for i in range(1, len(parse_url)): # gets the wayback url
        orig_url = parse_url[i][2]
        tstamp = parse_url[i][1]
        waylink = tstamp + '/' + orig_url
        final_url = f'http://web.archive.org/web/{waylink}'
        url_list.append(final_url)
    latest_url = url_list[-1]
    return get_JArchive_Game(game_id, None, True, latest_url)

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
