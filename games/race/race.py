from car import Car
from track import Track
from counter import Counter
import pyglet

WIDTH, HEIGHT = 1100, 700
window = pyglet.window.Window(width=WIDTH, height=HEIGHT)

track = Track()
car = Car(track=track, window=window)
counter = Counter(car=car, height=HEIGHT)


@window.event
def on_draw():
    window.clear()
    track.draw()
    car.draw()
    counter.draw()


def update(dt):
    global x, y
    car.update(dt)
    counter.update(dt)


if __name__ == "__main__":
    # Update the game 20 times per second
    pyglet.clock.schedule_interval(update, 1 / 20.0)
    pyglet.app.run()
