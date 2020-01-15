import requests
from bs4 import BeautifulSoup 
import re
from game import Question, Board, Game

def get_game(game_id):
    r = requests.get(f"http://www.j-archive.com/showgame.php?game_id={game_id}")
    soup = BeautifulSoup(r.text, 'html.parser')

    rounds = soup.find_all(class_="round") + soup.find_all(class_="final_round")
    boards = []
    for ro in rounds:
        final = ro['class'][0]=='final_round'
        categories_objs = ro.find_all(class_="category")
        categories = [c.find(class_="category_name").text for c in categories_objs]
        questions = []
        for clue in ro.find_all(class_="clue"):
            try:
                value = int(clue.find(class_="clue_value").text[1:])
            except AttributeError as e:
                value = None
            text_obj = clue.find(class_="clue_text")
            text = text_obj.text
            index_key = text_obj['id']
            if not final:
                index = (int(index_key[-1])-1,int(index_key[-3])-1)
                js = clue.find("div")['onmouseover']
            else:
                index = (0,0)
                js = list(clue.parents)[1].find("div")['onmouseover']
            answer = re.findall(r'correct_response">(.*?)</em', js.replace('\\',''))[0]
            questions.append(Question(index, text, answer, value))
        boards.append(Board(categories, questions, final=final))
    return Game(boards)
