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
            self.numberOfRolls = 3
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

def getImageLink(number):
    return 'https://pokeres.bastionbot.org/images/pokemon/' + str(number) + '.png'

def extractData(poke):
    types = poke['types']
    type2 = ""
    type1 = (((types[0])['type'])['name']).capitalize()
    if ((types[0])['slot']) == 2:
        type2 = (((types[1])['type'])['name']).capitalize()
        type1 = type1 + "/" + type2
    pokemonNumber = poke['id']
    pokemon = PokeObj(poke['name'].capitalize(), pokemonNumber, type1, getImageLink(pokemonNumber))
    return pokemon

#In embed.color: int value should be less than or equal to 16777215
def toEmbed(pokemon, flag):
    randomColor = random.randint(0, 16777215)
    embed = discord.Embed(title = str(pokemon.num) + '. ' + pokemon.name, color=randomColor, description=pokemon.type)
    embed.set_image(url=pokemon.imgLink)
    if flag == True:
        embed.set_footer(text=pokemon.caughtAt, icon_url="https://play.pokemonshowdown.com/sprites/itemicons/poke-ball.png")
    return embed


@client.command(name= 'roll')
async def pokemonRoll(context):
    global users
    if context.author.id not in users.keys():
        users[context.author.id] = User(None)
    if users[context.author.id].numberOfRolls != 0:
        users[context.author.id].subtractRolls()
        pokemonNumber = random.randint(1,807)
        url = "http://pokeapi.co/api/v2/pokemon/" + str(pokemonNumber) + "/"
        poke = requests.get(url).json()
        pokemon = extractData(poke)
        embed = toEmbed(pokemon, False)
        await context.send(embed = embed)

        try:
                reaction, user = await client.wait_for('reaction_add', timeout=8.0)
        except:
                ran = pokemon.name + ' has escaped!'
                await context.send(ran)
        else:
                if user.id in users.keys():
                    users[user.id].addPokemon(pokemon)
                else:
                    users[user.id] = User(pokemon)

                caught = pokemon.name + ' has been caught by ' + user.name + '!'
                await context.send(caught)
    else:
        await context.send('Out of Rolls.')

@client.command(name= 'check')
async def pokemonInfo(context, name):
    global users
    flag = False
    nameLower = name.lower()
    if context.message.author.id not in users.keys():
        users[context.message.author.id] = User(None)
    url = "http://pokeapi.co/api/v2/pokemon/" + nameLower + "/"
    request = requests.get(url)
    if request.status_code == 200:
        poke = requests.get(url).json()
        pokemon = extractData(poke)
        if context.message.author.id in users.keys():
            user = users[context.message.author.id]
            if nameLower.capitalize() in user.pokeDict.keys():
                flag = True
        embed = toEmbed(pokemon, flag)
        await context.send(embed=embed)


@client.command(name = 'list')
async def pokemonList(context):
    global users
    if context.message.author.id in users.keys():
        user = users[context.message.author.id]
        total = str(context.author.name) + ' caught ' + str(len(user.pokeDict.keys())) + ' out of 807.'
        pokeEmbed = discord.Embed(type="rich", title=str(context.author.name), color=15849984)
        str_desc = ""
        for num in range(1, 807):
            if(user.pokeNum[num] != 0):
                poke = user.pokeNum[num]
                str_desc += "{}. {}\n".format(str(poke.num), poke.name.capitalize())
        pokeEmbed.description = str_desc
        pokeEmbed.set_footer(text = total, icon_url="https://play.pokemonshowdown.com/sprites/itemicons/poke-ball.png")
        await context.send(embed = pokeEmbed)
    else:
        users[context.message.author.id] = User(None)
        await context.send('No Pokemon owned.')

@client.command(name = 'release')
async def release(context, name):
    nameFix = name.lower().capitalize()
    if context.message.author.id in users.keys():
        user = users[context.message.author.id]
        if nameFix in user.pokeDict.keys():
            user.delPokemon(nameFix)
            str = nameFix + ' has been set free.'
            await context.send(str)
        else:
            await context.send('Pokemon is not owned.')
    else:
        users[context.message.author.id] = User(None)
        await context.send('No Pokemon owned.')

@client.command(name = 'left')
async def leftover(context):
    if context.message.author.id not in users.keys():
        users[context.message.author.id] = User(None)
    msg = str(context.author.name) + ' has ' + str(users[context.message.author.id].numberOfRolls) + ' rolls left.'
    await context.send(msg)

@client.event
async def on_ready():
    print("Logged in as " + client.user.name)

async def rollTimer():
    global users
    global counter
    await client.wait_until_ready()
    channel = client.get_channel(683192733455745225)
    while not client.is_closed():
        for value in users.values():
            value.numberOfRolls = 3
        await asyncio.sleep(60)

users = {}
client.loop.create_task(rollTimer())
client.run(TOKEN)