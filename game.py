class Question(object):
    def __init__(self,index,text,answer,value):
        self.index = index
        self.text = text
        self.answer = answer
        self.value = value

class Board(object):
    def __init__(self,categories, questions, final=False):
        if final:
            self.size = (1,1)
        else:
            self.size = (5,6)
        self.final = final
        self.categories = categories
        if not questions is None:
            self.questions = questions
        else:
            self.questions = []

class Game(object):
    def __init__(self,rounds):
        self.rounds = rounds
