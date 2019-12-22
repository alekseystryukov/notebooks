from resources import background_image
import pyglet
import utils

TRACK = (
    (216, 216, 216),
    (217, 217, 217),
)
FINISH = (
    (247, 247, 247),
    (255, 255, 255),
    (243, 243, 243),
    (244, 244, 244),
)
INNER_BORDER = (28, 73, 76)
INNER_BORDER_2 = (19, 70, 73)
OUTER_BORDER = (43, 41, 41)
BORDERS = INNER_BORDER, INNER_BORDER_2, OUTER_BORDER


class Track(pyglet.sprite.Sprite):

    def __init__(self):
        super(Track, self).__init__(img=background_image,  x=0, y=0)

        # data
        self.img_data = background_image.get_image_data()

    def position_is_on_track(self, x, y):
        color = utils.get_color_for_position(x, y, self.img_data)
        return all(light > 215 for light in color)

    def position_is_on_finish(self, x, y):
        color = utils.get_color_for_position(x, y, self.img_data)
        return all(light > 243 for light in color)

