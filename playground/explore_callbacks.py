# I want to have a class call back a function of the code


def SimpleFunc():
    print("in simple func")


class CallMe:
    def __init__(self, func):
        self.func = func

    def start_timer(self):
        self.func()


caller = CallMe(SimpleFunc)
caller.start_timer()
