import pyglet

# Tell pyglet where to find the resources
pyglet.resource.path = ['./resources']
pyglet.resource.reindex()

# Load the three main resources
car_image = pyglet.resource.image("car.png")
car_image.texture.width = 20
car_image.texture.height = 45
car_image.anchor_x = 10
car_image.anchor_y = 22

background_image = pyglet.resource.image("background.png")
