from machine import Timer


class MinuteTimer:

    def __init__(self, func, mins=1):
        # The value passed in for period to the Timer init function.
        self.callback_period = 1000
        self.counter_ticks = mins * 60
        print('in minuteTimer. counter ticks: {}'.format(self.counter_ticks))
        self.callback = func  # used to call back code when timer stops.
        print('in minuteTimer.  callback {}'.format(self.callback))
        # number of times the timer has fired.
        self.counter_count = 0
        self.timer = Timer(-1)

    def _timer_callback(self):
        self.counter_count += 1
        print(self.counter_count)
        if self.counter_count == self.counter_ticks:
            self.stop_timer()

    def start_timer(self):
        self.timer.init(period=self.callback_period,
                        mode=Timer.PERIODIC, callback=lambda t: self._timer_callback())

    def stop_timer(self):
        # Reset the number of timer firings to 0.
        self.counter_count = 0
        self.timer.deinit()
        self.callback()
