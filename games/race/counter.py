from time import time
import pyglet

FONT_SIZE = 32
FONT_NAME = 'Verdana'
TOTAL_LAPS_TEXT = "Total laps - {}"
BEST_LAP_TEXT = "Best lap - {0:.2f}"
TIME_LAP_TEXT = "Time - {0:.2f}"


class Counter:
    # will use them later, to check that the car actually crossed them
    # track_points = [
    #     (240, 410),  # top left
    #     (600, 340),  # bottom middle
    #     (800, 90),  # bottom right
    # ]

    def __init__(self, car, height):
        self.car = car
        self.laps = 0
        self.start_time = None
        self.best_lap_time = None
        self.total_laps_label = pyglet.text.Label(
            TOTAL_LAPS_TEXT.format(self.laps),
            font_name=FONT_NAME,
            font_size=FONT_SIZE,
            x=FONT_SIZE, y=height - FONT_SIZE,
            anchor_x='left', anchor_y='top',
            color=[255] * 4
        )
        self.best_lap_label = pyglet.text.Label(
            BEST_LAP_TEXT.format(0),
            font_name=FONT_NAME,
            font_size=FONT_SIZE,
            x=FONT_SIZE, y=height - FONT_SIZE * 2.5,
            anchor_x='left', anchor_y='top',
            color=[255] * 4
        )
        self.lap_label = pyglet.text.Label(
            TIME_LAP_TEXT.format(0),
            font_name=FONT_NAME,
            font_size=FONT_SIZE,
            x=FONT_SIZE, y=height - FONT_SIZE * 4,
            anchor_x='left', anchor_y='top',
            color=[255] * 4
        )

    def draw(self):
        self.total_laps_label.draw()
        self.best_lap_label.draw()
        self.lap_label.draw()

    def update(self, dt):
        now = time()
        car = self.car
        if car.crossed_finish:
            if self.start_time:
                lap_time = now - self.start_time
                if not self.best_lap_time or lap_time < self.best_lap_time:
                    self.best_lap_time = lap_time
                    self.best_lap_label.text = BEST_LAP_TEXT.format(lap_time)

                self.start_time = now
                self.laps += 1
                self.total_laps_label.text = TOTAL_LAPS_TEXT.format(self.laps)
            else:
                self.start_time = now

        if self.start_time:
            self.lap_label.text = TIME_LAP_TEXT.format(now - self.start_time)



