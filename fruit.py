from block import Block
from random import choice
from imagerect import ImageRect


class Fruit(Block):
    def __init__(self, x, y, width, height):
        images = ['apple.png', 'cherry.png', 'peach.png', 'strawberry.png']
        fruit_image, _ = ImageRect(img=choice(images), resize=(width // 2, height // 2)).get_image()
        super(Fruit, self).__init__(x, y, width, height, fruit_image)

