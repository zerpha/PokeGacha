# Work with Python 3.6
import random, os
import discord
import requests
import asyncio
from discord.ext import commands
from datetime import datetime

TOKEN = 'NjMwNDYzOTU3Njg5MzAzMDQx.XloO7w.13LNfCh7RqXXXMKmaA2knWBaixQ'

BOT_PREFIX = ("?", "!")
client = commands.Bot(command_prefix=BOT_PREFIX)

class PokeObj:
    def __init__(self, name, number, type, imgLink):
        self.name = name
        self.num = number
        self.type = type
        self.imgLink = imgLink
        self.caughtAt = (datetime.now().strftime("%b %d, %Y - %I:%M %p"))

class User:
    def __init__(self, pokemon):
        if pokemon == None:
            self.pokeDict = {} #dictionary with pokemon names as the key, the names are capitalized
            self.pokeNum = [0] * 807 #list of pokemon with index being the pokemon indices
            self.numberOfRolls = 99 #####################
        else:
            self.pokeDict = {pokemon.name: pokemon} #dictionary with pokemon names as the key, the names are capitalized
            self.pokeNum = [0] * 807 #list of pokemon with index being the pokemon indices
            self.pokeNum[pokemon.num] = pokemon
            self.numberOfRolls = 2

    def addPokemon(self, pokemon):
        self.pokeDict[pokemon.name] = pokemon
        self.pokeNum[pokemon.num] = pokemon

    def delPokemon(self, name):
        poke = self.pokeDict[name]
        del self.pokeDict[name]
        self.pokeNum[poke.num] = 0

    def subtractRolls(self):
        self.numberOfRolls -= 1

class PokeBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self.ownership = {}
        self.pokemonLeft = []
        for x in range(1, 808): #appends 1 - 807
             self.pokemonLeft.append(x)
        self.bot.loop.create_task(self.rollTimer())

    def getImageLink(self, number):
        return 'https://pokeres.bastionbot.org/images/pokemon/' + str(number) + '.png'

    def extractData(self, poke):
        types = poke['types']
        type2 = ""
        type1 = (((types[0])['type'])['name']).capitalize()
        if ((types[0])['slot']) == 2:
            type2 = (((types[1])['type'])['name']).capitalize()
            type1 = type1 + "/" + type2
        pokemonNumber = poke['id']
        pokemon = PokeObj(poke['name'].capitalize(), pokemonNumber, type1, self.getImageLink(pokemonNumber))
        return pokemon

    # In embed.color: int value should be less than or equal to 16777215
    def toEmbed(self, pokemon, owner):
        randomColor = random.randint(0, 16777215)
        embed = discord.Embed(title=str(pokemon.num) + '. ' + pokemon.name, color=randomColor, description=pokemon.type)
        embed.set_image(url=pokemon.imgLink)
        if owner != None:
            msg = 'Caught by ' + str(owner) + ' at ' + pokemon.caughtAt
            embed.set_footer(text=msg,
                             icon_url="https://play.pokemonshowdown.com/sprites/itemicons/poke-ball.png")
        return embed

    @commands.command(name='roll')
    async def pokemonRoll(self, context):
        if context.author.id not in self.users.keys():
            self.users[context.author.id] = User(None)
        if len(self.pokemonLeft) > 0:
            if self.users[context.author.id].numberOfRolls != 0:
                self.users[context.author.id].subtractRolls()
                number = random.randint(1, len(self.pokemonLeft))
                pokemonNumber = str(self.pokemonLeft[number-1])

                url = "http://pokeapi.co/api/v2/pokemon/" + pokemonNumber + "/"
                poke = requests.get(url).json()
                pokemon = self.extractData(poke)
                embed = self.toEmbed(pokemon, None)
                await context.send(embed=embed)

                try:
                    reaction, user = await client.wait_for('reaction_add', timeout=8.0)
                except:
                    ran = pokemon.name + ' has escaped!'
                    await context.send(ran)
                else:
                    if user.id in self.users.keys():
                        self.users[user.id].addPokemon(pokemon)
                    else:
                        self.users[user.id] = User(pokemon)

                    self.ownership[pokemon.name] = user.name
                    self.pokemonLeft.remove(int(pokemonNumber))
                    caught = pokemon.name + ' has been caught by ' + user.name + '!'
                    await context.send(caught)
            else:
                await context.send('Out of Rolls.')
        else:
            await context.send('All pokemon have been caught.')

    @commands.command(name='check')
    async def pokemonInfo(self, context, name):
        owner = None
        nameLower = name.lower()
        if context.message.author.id not in self.users.keys():
            self.users[context.message.author.id] = User(None)
        url = "http://pokeapi.co/api/v2/pokemon/" + nameLower + "/"
        request = requests.get(url)
        if request.status_code == 200:
            poke = requests.get(url).json()
            pokemon = self.extractData(poke)
            if pokemon.name in self.ownership.keys():
                owner = self.ownership[pokemon.name]
            embed = self.toEmbed(pokemon, owner)
            await context.send(embed=embed)

    @commands.command(name='list')
    async def pokemonList(self, context):
        if context.message.author.id in self.users.keys():
            user = self.users[context.message.author.id]
            total = str(context.author.name) + ' caught ' + str(len(user.pokeDict.keys())) + ' out of 807.'
            pokeEmbed = discord.Embed(type="rich", title=str(context.author.name), color=15849984)
            str_desc = ""
            for num in range(1, 807):
                if (user.pokeNum[num] != 0):
                    poke = user.pokeNum[num]
                    str_desc += "{}. {}\n".format(str(poke.num), poke.name.capitalize())
            pokeEmbed.description = str_desc
            pokeEmbed.set_footer(text=total,
                                 icon_url="https://play.pokemonshowdown.com/sprites/itemicons/poke-ball.png")
            await context.send(embed=pokeEmbed)
        else:
            self.users[context.message.author.id] = User(None)
            await context.send('No Pokemon owned.')

    @commands.command(name='release')
    async def release(self, context, name):
        nameFix = name.lower().capitalize()
        if context.message.author.id in self.users.keys():
            user = self.users[context.message.author.id]
            if nameFix in user.pokeDict.keys():
                poke = user.pokeDict[nameFix]
                self.pokemonLeft.append(poke.num) #add pokemon back into pool of rolls
                del self.ownership[nameFix] #delete ownership of pokemon
                user.delPokemon(nameFix) #delete pokemon in user
                msg = nameFix + ' has been set free.'
                await context.send(msg)
            else:
                await context.send('Pokemon is not owned.')
        else:
            self.users[context.message.author.id] = User(None)
            await context.send('No Pokemon owned.')

    @commands.command(name='left')
    async def leftover(self, context):
        if context.message.author.id not in self.users.keys():
            self.users[context.message.author.id] = User(None)
        msg = str(context.author.name) + ' has ' + str(self.users[context.message.author.id].numberOfRolls) + ' rolls left.'
        await context.send(msg)

    @commands.command(name='time')
    async def time(self, context):
        CurMinute = int(datetime.now().strftime("%M"))
        minutesLeft = 60 - CurMinute
        msg = 'Rolls reset in ' + str(minutesLeft) + ' minutes.'
        await context.send(msg)

    async def rollTimer(self):
        await self.bot.wait_until_ready()
        #channel = self.bot.get_channel(683192733455745225)
        while not self.bot.is_closed():
            for value in self.users.values():
                value.numberOfRolls = 3
            CurMinute = int(datetime.now().strftime("%M"))
            minutesLeft = 60 - CurMinute
            secondsTotal = minutesLeft * 60
            await asyncio.sleep(secondsTotal)

@client.event
async def on_ready():
    client.add_cog(PokeBot(client))
    print("Logged in as " + client.user.name)

client.run(TOKEN)