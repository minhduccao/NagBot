from enum import Enum


class TimerStatus(Enum):
    STOPPED = -1
    PAUSED = 0
    RUNNING = 1


class Timer:
    """A class for a countdown timer.

    Attributes:
        status : TimerStatus
            Timer state (stopped/paused/running)
        time_left : int
            Remaining timer duration in seconds

    Methods:
        start(duration):
            Changes timer status to running and updates duration
        resume():
            Changes timer status to running
        pause():
            Changes timer status to paused
        tick(tick_duration=1):
            Counts down timer duration and changes timer state to stopped
        get_status():
            Returns the timer status
        get_time():
            Returns the remaining timer duration in seconds
    """
    def __init__(self):
        """Constructs timer status and duration for the timer object.

        Attributes:
            self.status : TimerStatus
                Timer state (stopped/paused/running)
            self.time_left : int
                Remaining timer duration in seconds
        """
        self.status = TimerStatus.STOPPED
        self.time_left = 0

    def start(self, duration: int):
        """Changes timer status to running and updates duration.

        Args:
            duration : int
                Timer duration in seconds
        Returns:
            bool
                Whether or not the timer status was changed to running
        """
        if self.status != TimerStatus.RUNNING:
            self.time_left = duration
            self.status = TimerStatus.RUNNING
            return True
        return False

    def resume(self):
        """Changes timer status to running.

        Returns:
            bool
                Whether or not the timer status was changed to running
        """
        if self.status == TimerStatus.PAUSED:
            self.status = TimerStatus.RUNNING
            return True
        return False

    def pause(self):
        """Changes timer status to paused.

        Returns:
            bool
                Whether or not the timer status was changed to paused
        """
        if self.status == TimerStatus.RUNNING:
            self.status = TimerStatus.PAUSED
            return True
        return False

    def tick(self, tick_duration=1):
        """Counts down timer duration and changes timer state to stopped.

        Args:
            tick_duration : int
        """
        self.time_left -= tick_duration
        if self.time_left <= 0:
            self.status = TimerStatus.STOPPED

    def get_status(self):
        """Returns the timer status."""
        return self.status

    def get_time(self):
        """Returns the remaining timer duration in seconds."""
        return self.time_left
