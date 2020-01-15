import sys
from random import shuffle
from PyQt5.QtGui import QPainter, QPen, QBrush, QImage
from PyQt5.QtWidgets import *#QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt5.QtCore import Qt, QRectF, QPoint, QTimer

from retrieve import get_game

margin=50
window_size=500
n=8 #even integer
cell_size=(window_size-2*margin)//n
fontSize=10

class Memory(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(50, 50, window_size, window_size)
        self.setWindowTitle('Memory')
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.callback)
        self.__gameRect=QRectF(margin,margin,cell_size*n,cell_size*n)
        self.__currentNumber=-1
        udata=2*list(range(1,n**2//2+1))
        shuffle(udata)
        self.__data=[udata[n*x:n*(x+1)] for x in range(n)]
        self.__visibleCells=[]
        self.__paused=False
        self.__complete=False
        self.show()
    def callback(self):
        self.__visibleCells=self.__visibleCells[:-2]
        self.__currentNumber=-1
        self.__paused=False
        self.__timer.stop()
        self.update()
    def numberFromCoord(self, coord):
        return self.__data[coord[0]][coord[1]]
    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
# 		for i in range(n+1):
# 			qp.drawLine(margin, margin+cell_size*i, window_size-margin, margin+cell_size*i)
# 		for j in range(n+1):
# 			qp.drawLine(margin+cell_size*j, margin, margin+cell_size*j, window_size-margin)
        for x in range(n):
            for y in range(n):
                cell=(x,y)
                if cell in self.__visibleCells:
                    number=self.numberFromCoord(cell)
                    qp.drawText((cell[0]+0.5)*cell_size+margin-fontSize/2,(cell[1]+0.5)*cell_size+margin+fontSize/2,str(number))
                else:	
                    source=QRectF(0,0,100,100)
                    target=QRectF(cell[0]*cell_size+margin,cell[1]*cell_size+margin,cell_size,cell_size)
                    qp.drawImage(target,QImage("card_back.png"),source)
        if self.__complete:
            qp.drawText(225,30,"You won!")
        qp.end()
    def mousePressEvent(self, event):
        if not self.__paused:
            coord=((event.x()-margin)//cell_size,(event.y()-margin)//cell_size)
            if not coord in self.__visibleCells and self.__gameRect.contains(event.pos()):
                self.__visibleCells.append(coord)
                number=self.numberFromCoord(coord)
                if self.__currentNumber==-1:
                    self.__currentNumber=number
                else:
                    if self.__currentNumber!=number:
                        self.__timer.start(1000)
                        self.__paused=True
                    else:
                        self.__currentNumber=-1
                        if len(self.__visibleCells)==n**2:
                            self.__complete=True
                self.update()

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Jeopardy!'
        self.left = 10
        self.top = 10
        self.width = 500
        self.height = 300

        self.startButton = QPushButton('Start!', self)
        self.textbox = QLineEdit(self)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())


        self.startButton.setToolTip('Start Game')
        self.startButton.move(200,200)
        self.startButton.clicked.connect(self.start)

        self.textbox.move(200, 100)
        self.textbox.resize(100,40)
        self.textbox.setText("4727")


        self.show()

    def start(self):
        game_id = int(self.textbox.text())
        game = get_game(game_id)
        print("start!")


if __name__ == '__main__':

    # game_id = 4727

    # game = get_game(game_id)
    # for r in game.rounds:
    # 	for q in r.questions:
    # 		print(q.answer)
            
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
