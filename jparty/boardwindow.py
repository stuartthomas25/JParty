from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QImage,
    QColor,
    QFont,
    QPalette,
    QPixmap,
    QTextDocument,
    QTextOption,
    QGuiApplication,
    QFontMetrics,
)
from PyQt6.QtWidgets import *  # QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QRect,
    QPoint,
    QPointF,
    QTimer,
    QRect,
    QSize,
    QSizeF,
)
from PyQt6.sip import delete


from .game import game_params as gp
from .utils import resource_path
from .constants import DEBUG
import time
import threading
import re
import logging

margin = 50
n = 8  # even integer
CELLRATIO = 3 / 5
FONTSIZE = 10

BLUE = QColor("#031591")
HINTBLUE = QColor("#041ec8")
YELLOW = QColor("#ffcc00")
RED = QColor("#ff0000")
BLACK = QColor("#000000")
GREY = QColor("#505050")
WHITE = QColor("#ffffff")
GREEN = QColor("#33cc33")


CARDPAL = QPalette()
CARDPAL.setColor(QPalette.ColorRole.Window, BLUE)
CARDPAL.setColor(QPalette.ColorRole.WindowText, WHITE)

BOARDSIZE = (6, 6)

CATFONT = QFont()
CATFONT.setBold(True)
CATFONT.setPointSize(24)
CATPEN = QPen(WHITE)

MONFONT = QFont(CATFONT)
MONFONT.setPointSize(50)
MONPEN = QPen(YELLOW)
TEXTPADDING = 20

QUFONT = QFont()
QUFONT.setPointSize(70)
QUMARGIN = 50

NAMEHEIGHT = 50
NAMEFONT = QFont()
NAMEFONT.setPointSize(20)
NAMEPEN = QPen(WHITE)
SCOREFONT = QFont()
SCOREFONT.setPointSize(50)
SCOREPEN = QPen(WHITE)
HOLEPEN = QPen(RED)
HIGHLIGHTPEN = QPen(BLUE)
HIGHLIGHTBRUSH = QBrush(WHITE)
HINTBRUSH = QBrush(HINTBLUE)

CORRECTBRUSH = QBrush(GREEN)
INCORRECTBRUSH = QBrush(RED)

LIGHTPEN = QPen(GREY)
LIGHTBRUSH = QBrush(RED)

BORDERWIDTH = 10
BORDERPEN = QPen(BLACK)
BORDERPEN.setWidth(BORDERWIDTH)
DIVIDERBRUSH = QBrush(WHITE)
DIVIDERWIDTH = 20

FILLBRUSH = QBrush(BLUE)
SCOREHEIGHT = 0.15
ANSWERHEIGHT = 0.15

ANSWERBARS = 30
ANSWERSECS = 5

FINALANSWERHEIGHT = 0.6


def updateUI(f):
    def wrapper(self, *args):
        ret = f(self, *args)
        self.game.update()
        return ret

    return wrapper


def autofitsize(text, font, rect, start=None, stepsize=2):
    if start:
        font.setPointSize(start)

    size = font.pointSize()
    flags = Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter

    def fullrect(font, text=text, flags=flags):
        fm = QFontMetrics(font)
        return fm.boundingRect(rect, flags, text)

    if fullrect(font).height() > rect.height():
        while size > 0:
            size -= stepsize
            font.setPointSize(size)
            newrect = fullrect(font)
            if newrect.height() <= rect.height():
                return font.pointSize()
        raise Exception(f"Nothing fit! (text='{text}')")

    logging.info(f"'{text}' is good")
    return size


class PlayerWidget(QWidget):
    def __init__(self, game, player):
        super().__init__()
        self.player = player
        self.game = game
        self.name_label = QLabel(player.name)
        self.name_label.setFont(NAMEFONT)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.score_label = QLabel()
        self.update_score()
        self.score_label.setFont(SCOREFONT)
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.highlighted = False

        layout = QVBoxLayout()
        layout.addWidget(self.score_label)
        layout.addWidget(self.name_label)

        self.setAutoFillBackground(True)
        self.setPalette(CARDPAL)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.setLayout(layout)
        self.show()

    def __buzz_hint(self, p):
        self.__buzz_hint_players.append(p)
        self.update()
        time.sleep(0.25)
        self.__buzz_hint_players.remove(p)
        self.update()

    def buzz_hint(self, p):
        self.__buzz_hint_thread = threading.Thread(
            target=self.__buzz_hint, args=(p,), name="buzz_hint"
        )
        self.__buzz_hint_thread.start()

    def update_score(self):
        self.score_label.setText( f"{self.player.score}" )

    def mousePressEvent(self, event):
        self.game.adjust_score(self.player)
        self.update_score()



class LightsWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.__light_level = 0
        self.__light_thread = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, WHITE)
        self.setPalette(palette)

    def sizeHint(self):
        return QSize(self.geometry().width(), DIVIDERWIDTH)

    def paintEvent(self, event):
        w = self.geometry().width()
        qp = QPainter()
        qp.begin(self)

        # Light dividers
        num_lights = 9
        light_width = w // num_lights
        light_padding = 3
        ungrouped_rects = [
            QRect(
                light_width * i + light_padding,
                light_padding,
                light_width - 2 * light_padding,
                DIVIDERWIDTH - 2 * light_padding,
            )
            for i in range(num_lights)
        ]
        grouped_rects = [
            [
                rect
                for j, rect in enumerate(ungrouped_rects)
                if abs(num_lights // 2 - j) == i
            ]
            for i in range(5)
        ]
        qp.setBrush(LIGHTBRUSH)
        qp.setPen(LIGHTPEN)
        for i, rects in enumerate(grouped_rects):
            if i < self.__light_level:
                for rect in rects:
                    qp.drawRect(rect)

    def __lights(self):
        self.__light_level = ANSWERSECS + 1
        while (
            self.__light_level > 0 and threading.current_thread() is self.__light_thread
        ):
            self.__light_level -= 1
            self.update()
            time.sleep(1.0)

    def run_lights(self):
        self.__light_thread = threading.Thread(target=self.__lights, name="lights")
        self.__light_thread.start()

    def stop_lights(self):
        self.__light_level = 0


class ScoreWidget(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game

        player_layout = QHBoxLayout()
        for p in self.game.players:
            player_layout.addWidget( PlayerWidget(game, p) )
        player_layout.setSpacing(0)

        self.setLayout(player_layout)
        self.setPalette(CARDPAL)

        self.__buzz_hint_players = []
        self.__buzz_hint_thread = []


        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.show()


    def maximumSizeHint(self):
        return QSize(self.geometry().width(), 100)

    # def paintEvent(self, event):
    #     return None
    #     h = self.geometry().height()
    #     w = self.geometry().width()
    #     qp = QPainter()
    #     qp.begin(self)

    #     qp.setBrush(DIVIDERBRUSH)
    #     dividerrect = QRectF(0, 0, w, DIVIDERWIDTH)
    #     qp.drawRect(dividerrect)

    #     # Light dividers
    #     num_lights = 9
    #     light_width = w // num_lights
    #     light_padding = 3
    #     ungrouped_rects = [
    #         QRect(
    #             light_width * i + light_padding,
    #             light_padding,
    #             light_width - 2 * light_padding,
    #             DIVIDERWIDTH - 2 * light_padding,
    #         )
    #         for i in range(num_lights)
    #     ]
    #     grouped_rects = [
    #         [
    #             rect
    #             for j, rect in enumerate(ungrouped_rects)
    #             if abs(num_lights // 2 - j) == i
    #         ]
    #         for i in range(5)
    #     ]
    #     qp.setBrush(LIGHTBRUSH)
    #     qp.setPen(LIGHTPEN)
    #     for i, rects in enumerate(grouped_rects):
    #         if i < self.__light_level:
    #             for rect in rects:
    #                 qp.drawRect(rect)

    #     margin = 50
    #     players = self.game.players
    #     sw = w // len(players)

    #     if self.game.current_round.final:
    #         highlighted_players = [p for p in players if p not in self.game.wagered]
    #     else:
    #         highlighted_players = []
    #     ap = self.game.answering_player
    #     if ap:
    #         highlighted_players.append(ap)

    #     for i, p in enumerate(players):
    #         if p.score < 0:
    #             qp.setPen(HOLEPEN)
    #         else:
    #             qp.setPen(SCOREPEN)

    #         qp.setFont(SCOREFONT)
    #         qp.drawText(
    #             self.__scorerect(i),
    #             Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
    #             f"{p.score:,}",
    #         )

    #         namerect = QRectF(sw * i, h - NAMEHEIGHT, sw, NAMEHEIGHT)
    #         qp.setFont(NAMEFONT)
    #         qp.setPen(NAMEPEN)
    #         if p in highlighted_players:
    #             qp.setBrush(HIGHLIGHTBRUSH)
    #             qp.drawRect(namerect)
    #             qp.setPen(HIGHLIGHTPEN)
    #         elif p in self.__buzz_hint_players:
    #             qp.setBrush(HINTBRUSH)
    #             qp.drawRect(namerect)

    #         qp.drawText(
    #             namerect,
    #             Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
    #             p.name,
    #         )

    # def __scorerect(self, i):
    #     w = self.geometry().width()
    #     h = self.geometry().height()
    #     sw = w // len(self.game.players)
    #     return QRectF(sw * i, DIVIDERWIDTH, sw, h - NAMEHEIGHT - DIVIDERWIDTH)



class BorderWidget(QWidget):
    def __init__(self, game, boardrect, parent=None):
        super().__init__(parent)
        self.game = game
        self.boardrect = boardrect
        margin_size = self.boardrect.x()
        self.__answerbarrect = boardrect.adjusted(-ANSWERBARS, 0, ANSWERBARS, 0)

        self.__correctrect = QRect(0, 0, margin_size, self.boardrect.height())
        self.__incorrectrect = QRect(
            self.boardrect.right(), 0, margin_size, self.boardrect.height()
        )
        arrow_size = QSize(int(margin_size * 0.7), int(margin_size * 0.7))
        self.__leftarrowrect = QRect(QPoint(0, 0), arrow_size)
        self.__leftarrowrect.moveCenter(self.__correctrect.center())
        self.__rightarrowrect = QRect(QPoint(0, 0), arrow_size)
        self.__rightarrowrect.moveCenter(self.__incorrectrect.center())

        self.__leftarrowimage = QPixmap(resource_path("left-arrow.png"))
        self.__rightarrowimage = QPixmap(resource_path("right-arrow.png"))
        self.__spaceimage = QPixmap(resource_path("space.png"))

        self.show()
        self.__lit = False
        self.arrowhints = False
        self.spacehints = False

    @property
    def lit(self):
        return self.__lit

    @lit.setter
    @updateUI
    def lit(self, val):
        self.__lit = val

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.lit:
            qp.setBrush(HIGHLIGHTBRUSH)
            qp.drawRect(self.__answerbarrect)
        if self.arrowhints and self.parent().alex:
            qp.setBrush(CORRECTBRUSH)
            qp.drawRect(self.__correctrect)
            qp.setBrush(INCORRECTBRUSH)
            qp.drawRect(self.__incorrectrect)
            qp.setBrush(HIGHLIGHTBRUSH)
            qp.drawPixmap(self.__leftarrowrect, self.__leftarrowimage)
            qp.drawPixmap(self.__rightarrowrect, self.__rightarrowimage)

        if self.spacehints and self.parent().alex:
            qp.setBrush(HIGHLIGHTBRUSH)
            qp.drawPixmap(self.__leftarrowrect, self.__spaceimage)
            qp.drawPixmap(self.__rightarrowrect, self.__spaceimage)


class QuestionLabel(QLabel):
    def __init__(self, text, rect, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: white;")
        self.setGeometry(QRect(rect))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.font = QFont("Helvetica")
        fontsize = autofitsize(text, self.font, rect, start=72)
        self.font.setPointSize(fontsize)
        self.setFont(self.font)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor("black"))
        shadow.setOffset(3)
        self.setGraphicsEffect(shadow)


class QuestionWidget(QWidget):
    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.question = question

        self.responses_open = False

        # pheight = parent.geometry().height()
        # height = pheight * (1 - SCOREHEIGHT)
        # width = height / CELLRATIO
        self.resize(parent.size())
        # self.move(
        # self.parent().geometry().width() / 2 - self.parent().boardwidget.geometry().width() / 2, 0
        # )
        alex = self.parent().alex

        if alex:
            anheight = ANSWERHEIGHT * self.size().height()
            self.qurect = self.rect().adjusted(
                QUMARGIN, QUMARGIN, -2 * QUMARGIN, -ANSWERHEIGHT * self.size().height(),
            )
            self.anrect = QRect(
                QUMARGIN,
                self.size().height() * (1 - ANSWERHEIGHT),
                self.size().width() - 2 * QUMARGIN,
                ANSWERHEIGHT * self.size().height(),
            )
            self.answer_label = QuestionLabel(question.answer, self.anrect, self)
            text = question.text

        else:
            self.qurect = self.rect().adjusted(
                QUMARGIN, QUMARGIN, -2 * QUMARGIN, -2 * QUMARGIN
            )
            self.anrect = None
            self.answer_label = None

            text = question.text.upper()

        self.question_label = QuestionLabel(text, self.qurect, self)

        self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setBrush(FILLBRUSH)
        qp.drawRect(self.rect())
        # Show question
        if self.parent().alex:
            anheight = ANSWERHEIGHT * self.size().height()
            qp.drawLine(
                0,
                (1 - ANSWERHEIGHT) * self.size().height(),
                self.size().width(),
                (1 - ANSWERHEIGHT) * self.size().height(),
            )


class DailyDoubleWidget(QuestionWidget):
    def __init__(self, game, parent=None):
        super().__init__(game, parent)
        self.question_label.setVisible(False)
        if self.parent().alex:
            self.answer_label.setVisible(False)

        self.dd_label = QuestionLabel("DAILY<br/>DOUBLE!", self.qurect, self)
        self.dd_label.setFont(QFont("Helvetica", 140))
        self.dd_label.setVisible(True)
        self.update()

    def show_question(self):
        self.question_label.setVisible(True)
        if self.parent().alex:
            self.answer_label.setVisible(True)
        self.dd_label.setVisible(False)


class CardLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setFont( QFont("Helvetica") )
        self.setAutoFillBackground(True)


        font = self.font()
        fontsize = autofitsize(self.text(), font, self.rect(), start=self.geometry().height() / 10 )
        font.setPointSize(fontsize)
        self.setFont(font)


        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, BLUE)
        palette.setColor(QPalette.ColorRole.WindowText, WHITE)
        self.setPalette(palette)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor("black"))
        shadow.setOffset(3)
        self.setGraphicsEffect(shadow)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self):
        # parent_height = self.parent().geometry().height()
        # height = parent_height * (1-SCOREHEIGHT)
        # width = height / CELLRATIO
        return QSize(50, 30)

    def resizeEvent(self, event):
        pass
        # font = self.font()
        # fontsize = autofitsize(self.text(), font, self.rect(), start=self.geometry().height()*0.1 )
        # font.setPointSize(fontsize)
        # self.setFont(font)


class QuestionCard(CardLabel):
    def __init__(self, game, question):
        self.game = game
        self.question = question
        if not question.complete:
            moneytext = "$" + str(question.value)
        else:
            moneytext = ""
        super().__init__(moneytext)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, BLUE)
        palette.setColor(QPalette.ColorRole.WindowText, YELLOW)
        self.setPalette(palette)

    def mousePressEvent(self, event):
        if not self.question.complete:
            self.game.load_question(self.question)
            self.setText("")



class BoardWidget(QWidget):
    def __init__(self, game, alex, parent=None):
        super().__init__(parent)
        self.game = game
        self.alex = alex

        self.responses_open = False

        self.questionwidget = None
        self.__completed_questions = []
        cellheight = self.size().height() // (self.board.size[1] + 1)
        self.cellsize = (cellheight / CELLRATIO, cellheight)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)


        for x in range(self.board.size[0]):
            self.grid_layout.setRowStretch(x, 1.)
        for y in range(self.board.size[1]+1):
            self.grid_layout.setColumnStretch(y, 1.)

        for x in range(self.board.size[0]):
            for y in range(self.board.size[1]+1):

                if y == 0:
                    # Categories
                    label = CardLabel(self.board.categories[x])
                    self.grid_layout.addWidget(label, 0, x)

                else:
                    # Questions
                    q = self.board.get_question(x,y-1)

                    label = QuestionCard(game, q)
                    self.grid_layout.addWidget(label, y, x)

        self.setLayout(self.grid_layout)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.show()

    def minimumSizeHint(self):
        return QSize(self.geometry().width(), 900)

    # @updateUI
    # def resizeEvent(self, event):
    #     print(self.geometry().height())
    #     print(self.parent().geometry().height())
    #     parent = self.parent()
    #     pheight = parent.geometry().height()
    #     height = pheight * (1 - SCOREHEIGHT)
    #     width = height / CELLRATIO
    #     self.resize(width + BORDERWIDTH, height)
    #     print("RESIZE!")


    @property
    def board(self):
        return self.game.current_round

    def paintEvent(self, event):
        return None
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(FILLBRUSH)
        parent = self.parent()
        pheight = parent.geometry().height()
        height = pheight * (1 - SCOREHEIGHT)
        width = height / CELLRATIO
        if not self.board.final:
            # Normal board
            for x in range(self.board.size[0]):
                for y in range(-1, self.board.size[1]):
                    rel_pos = (
                        x * self.cellsize[0] + BORDERWIDTH / 2,
                        (y + 1) * self.cellsize[1],
                    )
                    cell = (x, y)
                    qp.setPen(BORDERPEN)
                    qp.setBrush(FILLBRUSH)
                    cell_rect = QRectF(*rel_pos, *self.cellsize)
                    text_rect = QRectF(cell_rect)
                    text_rect.setX(cell_rect.x() + TEXTPADDING)
                    text_rect.setWidth(cell_rect.width() - 2 * TEXTPADDING)
                    qp.drawRect(cell_rect)
                    if y == -1:
                        # Categories
                        qp.setPen(CATPEN)
                        qp.setFont(CATFONT)
                        qp.drawText(
                            text_rect,
                            Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                            self.board.categories[x],
                        )
                    else:
                        # Questions
                        q = self.board.get_question(*cell)
                        if not q in self.game.completed_questions:
                            qp.setPen(MONPEN)
                            qp.setFont(MONFONT)
                            if not self.board.dj:
                                monies = gp.money1
                            else:
                                monies = gp.money2
                            qp.drawText(
                                text_rect,
                                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                                "$" + str(q.value),
                            )
        else:
            # Final jeopardy
            qp.setBrush(FILLBRUSH)
            qp.drawRect(self.rect())
            qp.setPen(CATPEN)
            qp.setFont(QUFONT)

            qurect = self.rect().adjusted(
                QUMARGIN, QUMARGIN, -2 * QUMARGIN, -2 * QUMARGIN
            )

            qp.drawText(
                qurect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                self.board.categories[0],
            )

    @updateUI
    def load_question(self, q):
        if q.dd:
            self.questionwidget = DailyDoubleWidget(q, self)
        else:
            logging.info("Question widget!")
            self.questionwidget = QuestionWidget(q, self)

    @updateUI
    def hide_question(self):
        delete(self.questionwidget)

    # def _identify_question(self, event):
    #     dc = self.game.dc

    #     coord = (
    #         event.position().x() // self.cellsize[0],
    #         event.position().y() // self.cellsize[1] - 1,
    #     )
    #     q = self.board.get_question(*coord)
    #     if not q in self.game.completed_questions:
    #         dc.load_question(q)
    #         self.game.load_question(q)

    # def mousePressEvent(self, event):
    #     if not any(
    #         [
    #             self.game.paused,
    #             self.game.active_question,
    #             not self.alex,
    #             self.board.final,
    #         ]
    #     ):
    #         self._identify_question(event)


class FinalAnswerWidget(QWidget):
    def __init__(self, game, parent=None):
        super().__init__()
        self.game = game
        self.__margin = 50
        self.winner = None

        if parent.alex:
            self.setGeometry(
                parent.boardwidget.x(),
                self.__margin,
                parent.boardwidget.width(),
                parent.height() * FINALANSWERHEIGHT,
            )

        else:
            self.setGeometry(
                0, self.__margin, parent.width(), parent.height() * FINALANSWERHEIGHT,
            )
        self.info_level = 0

        self.__light_level = 0
        self.__light_thread = None

        self.show()

    def paintEvent(self, event):
        h = self.geometry().height()
        w = self.geometry().width()
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(FILLBRUSH)
        qp.drawRect(self.rect())

        p = self.game.answering_player
        margin = self.__margin

        qp.setPen(SCOREPEN)
        qp.setFont(SCOREFONT)

        if self.winner:
            winnerrect = QRectF(0, NAMEHEIGHT + 2 * margin, w, 2 * NAMEHEIGHT)
            qp.drawText(
                winnerrect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                f"{self.winner.name} is the winner!",
            )
            return

        namerect = QRectF(0, margin, w, NAMEHEIGHT)
        qp.drawText(
            namerect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, p.name
        )

        if self.info_level > 0:
            answerrect = QRectF(0, NAMEHEIGHT + 2 * margin, w, 2 * NAMEHEIGHT)
            finalanswer = (
                p.finalanswer
                if len(p.finalanswer.replace(" ", "")) > 0
                else "_________"
            )
            qp.drawText(
                answerrect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                finalanswer,
            )

        if self.info_level > 1:
            wagerrect = QRectF(0, h - NAMEHEIGHT - margin, w, NAMEHEIGHT)
            qp.drawText(
                wagerrect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                f"{p.wager:,}",
            )


class DisplayWindow(QMainWindow):
    def __init__(self, game, alex=True, monitor=0):
        super().__init__()
        self.alex = alex
        self.setWindowTitle("Host" if alex else "Board")

        colorpal = QPalette()
        colorpal.setColor(QPalette.ColorRole.Window, BLACK)
        self.setPalette(colorpal)

        # monitor = QDesktopWidget().screenGeometry(monitor)
        if DEBUG:
            if len(QGuiApplication.screens()) == 1:
                monitor = 0

        monitor = QGuiApplication.screens()[monitor].geometry()

        self.move(monitor.left(), monitor.top())  # move to monitor 0
        self.showFullScreen()

        self.lights_widget = LightsWidget()

        self.boardwidget = BoardWidget(game, alex, self)
        self.boardwidget.move(
            self.geometry().width() / 2 - self.boardwidget.geometry().width() / 2, 0
        )
        self.boardwidget.update()

        self.scoreboard = ScoreWidget(game, self)
        # self.finalanswerwindow = FinalAnswerWidget(game)
        # self.finalanswerwindow.setVisible(False)

        self.borderwidget = BorderWidget(game, self.boardwidget.geometry())
        self.borderwidget.setGeometry(
            0, 0, self.size().width(), self.boardwidget.size().height()
        )
        self.borderwidget.stackUnder(self.boardwidget)

        self.game = game
        self.game.dc += self

        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0.)
        self.main_layout.setContentsMargins(0., 0., 0., 0.)
        self.main_layout.addWidget( self.boardwidget, 0 )
        self.main_layout.addWidget( self.lights_widget, 1 )
        self.main_layout.addWidget( self.scoreboard, 2 )

        self.newWidget = QWidget()
        self.newWidget.setLayout(self.main_layout)
        self.setCentralWidget(self.newWidget)

        self.show()

    def hide_question(self):
        self.boardwidget.hide_question()

    def keyPressEvent(self, event):
        self.game.keystroke_manager.call(event.key())

    def load_question(self, q):
        logging.info("DC load_question")
        self.boardwidget.load_question(q)
