from pokemon import PokeObj

#user class which holds users pokemon
class User:
    def __init__(self, PokeObj):
        if PokeObj == None:
            self.pokeDict = {} #dictionary with pokemon names as the key, the names are capitalized
            self.pokeNum = [0] * 807 #list of pokemon with index being the pokemon indices
            self.numberOfRolls = 99 #####################3
        else:
            self.pokeDict = {PokeObj.name: PokeObj} #dictionary with pokemon names as the key, the names are capitalized
            self.pokeNum = [0] * 807 #list of pokemon with index being the pokemon indices
            self.pokeNum[PokeObj.num] = PokeObj
            self.numberOfRolls = 99 ##########2

    def addPokemon(self, pokemon):
        self.pokeDict[pokemon.name] = pokemon
        self.pokeNum[pokemon.num] = pokemon

    def delPokemon(self, name):
        poke = self.pokeDict[name]
        del self.pokeDict[name]
        self.pokeNum[poke.num] = 0

    def subtractRolls(self):
        self.numberOfRolls -= 1