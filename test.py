import threading
import time

class QuestionTimer(object):
    def __init__(self, interval, f, *args, **kwargs):
        super().__init__()
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.interval = interval
        self.__thread = None
        self.__start_time = -1
        self.__elapsed_time = 0

    def run(self, i):
        thread = self.__thread
        time.sleep(i)
        if thread == self.__thread:
            self.f(*self.args, **self.kwargs)

    def start(self):
        '''wrapper for resume'''
        self.resume()

    def pause(self):
        self.__thread = None
        self.__elapsed_time += (time.time() - self.__start_time)

    def resume(self):
        self.__thread = threading.Thread(target=self.run, args=(self.interval - self.__elapsed_time,))
        self.__thread.start()
        self.__start_time = time.time()

def f():
    print("DONE")

qt = QuestionTimer(3, f)
qt.start()
time.sleep(0.2)
print('buzz')
qt.pause()
time.sleep(5)
print('too late')
qt.resume()
time.sleep(5)

