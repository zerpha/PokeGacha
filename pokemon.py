from datetime import datetime

#pokemon class
class PokeObj:
    def __init__(self, name, number, type, imgLink):
        self.name = name
        self.num = number
        self.type = type
        self.imgLink = imgLink
        self.caughtAt = (datetime.now().strftime("%b %d, %Y - %I:%M %p"))