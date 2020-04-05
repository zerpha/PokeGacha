#Henry Nguyen

# Work with Python 3.6
import random, os
import discord
import requests
import asyncio
import pickle
from discord.ext import commands
from datetime import datetime

TOKEN = 'NjMwNDYzOTU3Njg5MzAzMDQx.XloO7w.13LNfCh7RqXXXMKmaA2knWBaixQ'

BOT_PREFIX = ("?", "!")
client = commands.Bot(command_prefix=BOT_PREFIX)
client.remove_command('help')

#pokemon class
class PokeObj:
    def __init__(self, name, number, type, imgLink):
        self.name = name
        self.num = number
        self.type = type
        self.imgLink = imgLink
        self.caughtAt = (datetime.now().strftime("%b %d, %Y - %I:%M %p"))

#user class which holds users pokemon
class User:
    def __init__(self, pokemon):
        if pokemon == None:
            self.pokeDict = {} #dictionary with pokemon names as the key, the names are capitalized
            self.pokeNum = [0] * 807 #list of pokemon with index being the pokemon indices
            self.numberOfRolls = 99 #####################3
        else:
            self.pokeDict = {pokemon.name: pokemon} #dictionary with pokemon names as the key, the names are capitalized
            self.pokeNum = [0] * 807 #list of pokemon with index being the pokemon indices
            self.pokeNum[pokemon.num] = pokemon
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

#bot class which holds all users
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

    #extracts info from poke class taken from PokemonAPI
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

    #formats all pokemon information into a embed
    # In embed.color: int value should be less than or equal to 16777215
    def toEmbed(self, pokemon, owner):
        randomColor = random.randint(0, 16777215)
        embed = discord.Embed(title=str(pokemon.num) + '. ' + pokemon.name, color=randomColor, description=pokemon.type)
        embed.set_image(url=pokemon.imgLink)
        if owner != None:
            msg = 'Caught by ' + str(owner.name) + ' at ' + pokemon.caughtAt
            embed.set_footer(text=msg,
                             icon_url="https://play.pokemonshowdown.com/sprites/itemicons/poke-ball.png")
        return embed

    def set_pickle(self):
        with open("data/users.pickle", 'wb') as file:
            try:
                pickle.dump(self.users, file, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as Err:
                print("Cant pickle users")
            file.close
        with open("data/owners.pickle", 'wb') as file:
            try:
                pickle.dump(self.ownership, file, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as Err:
                print("Cant pickle ownership")
            file.close
        with open("data/left.pickle", 'wb') as file:
            try:
                pickle.dump(self.pokemonLeft, file, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as Err:
                print("Cant pickle left")
            file.close

    #rolls a random pokemon
    @commands.command(name='roll')
    async def pokemonRoll(self, context):
        if context.author.id not in self.users.keys():
            self.users[context.author.id] = User(None)
        if len(self.pokemonLeft) > 0:
            if self.users[context.author.id].numberOfRolls != 0:
                self.users[context.author.id].subtractRolls()
                number = random.randint(1, len(self.pokemonLeft))
                pokemonNumber = str(self.pokemonLeft[number-1])
                poke = requests.get('http://pokeapi.co/api/v2/pokemon/{}/'.format(pokemonNumber)).json()
                pokemon = self.extractData(poke)
                embeded = self.toEmbed(pokemon, None)
                await context.send(embed=embeded)

                def check(reaction, user):
                    if len(reaction.message.embeds) > 0:
                        return reaction.message.embeds[0].title == embeded.title
                    else:
                        return False

                try:
                    reaction, user = await client.wait_for('reaction_add', timeout=8.0, check = check)
                except:
                    await context.send('{} has escaped!'.format(pokemon.name))
                else:
                    if user.id in self.users.keys():
                        self.users[user.id].addPokemon(pokemon)
                    else:
                        self.users[user.id] = User(pokemon)

                    self.ownership[pokemon.name] = user.id
                    self.pokemonLeft.remove(int(pokemonNumber))
                    self.set_pickle()
                    await context.send('{} has been caught by {}!'.format(pokemon.name, user.name))
            else:
                await context.send('Out of Rolls.')
        else:
            await context.send('All pokemon have been caught.')

    #show pokemon info and if anyone owns it
    @commands.command(name='check')
    async def pokemonInfo(self, context, name):
        owner = None
        nameLower = name.lower()
        if context.message.author.id not in self.users.keys():
            self.users[context.message.author.id] = User(None)
        url = "http://pokeapi.co/api/v2/pokemon/" + nameLower + "/"
        request = requests.get("http://pokeapi.co/api/v2/pokemon/{}/".format(nameLower))
        if request.status_code == 200:
            poke = requests.get(url).json()
            pokemon = self.extractData(poke)
            if pokemon.name in self.ownership.keys():
                ownerid = self.ownership[pokemon.name]
            embed = self.toEmbed(pokemon, client.get_user(ownerid))
            await context.send(embed=embed)

    #list all of users pokemon
    @commands.command(name='list')
    async def pokemonList(self, context):
        words = context.message.content.split()
        if len(words) > 1 and len(context.message.mentions) == 1:
            if context.message.mentions[0].id in self.users.keys():
                user = self.users[context.message.mentions[0].id]
                pokeEmbed = discord.Embed(type="rich", title=str(context.author.name), color=15849984)
                str_desc = ""
                for num in range(1, 807):
                    if (user.pokeNum[num] != 0):
                        poke = user.pokeNum[num]
                        str_desc += "{}. {}\n".format(str(poke.num), poke.name.capitalize())
                pokeEmbed.description = str_desc
                pokeEmbed.set_footer(text='{} caught {} out of 807.'.format(context.author.name, str(len(user.pokeDict.keys()))),
                                     icon_url="https://play.pokemonshowdown.com/sprites/itemicons/poke-ball.png")
                await context.send(embed=pokeEmbed)
            else:
                self.users[context.message.author.id] = User(None)
                await context.send('No Pokemon owned.')

    #release pokemon from user if they own it
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
                self.set_pickle()
                await context.send('{} has been set free.'.format(nameFix))
            else:
                await context.send('Pokemon is not owned.')
        else:
            self.users[context.message.author.id] = User(None)
            await context.send('No Pokemon owned.')

    @commands.command(name='trade')
    async def trade(self, context, yourPoke, trader, theirPoke):
        if context.message.author.id != context.message.mentions[0].id:
            nameFix = theirPoke.lower().capitalize()
            myFix = yourPoke.lower().capitalize()
            if nameFix in self.ownership.keys() and context.message.mentions[0].id == self.ownership[nameFix]: #check the trader and their pokemon
                if myFix in self.ownership.keys() and context.message.author.id == self.ownership[myFix]: #check yourself and your pokemon
                    def check(m):
                        words = m.content.split()
                        if len(words) == 2 and m.mentions[0].id == context.message.author.id:
                            msg = words[1].lower().capitalize()
                            return m.author.id == self.ownership[nameFix] and ((msg == 'Yes' or msg == 'Y') or (msg == 'No' or msg == 'N')) #true if its a valid reply
                        else:
                            return False
                    try:
                         await context.send('\"@user yes/no\" to finish trade.')
                         confirmationMsg = await client.wait_for('message', timeout=15.0, check = check)
                    except:
                        await context.send('Trade between {} and {} has expired.'.format(context.message.author.name, context.message.mentions[0].name))
                    else:
                        words = confirmationMsg.content.split()
                        msg = words[1].lower().capitalize()
                        print(msg)
                        if (msg == 'No' or msg == 'N'):
                            await context.send('{} has denied the trade from {}.'.format(context.message.mentions[0].name, context.message.author.name))
                        else:
                            self.ownership[myFix] = context.message.mentions[0].id
                            self.ownership[nameFix] = context.message.author.id
                            poke1 = self.users[context.message.author.id].pokeDict[myFix] #get your mon before deleting it
                            self.users[context.message.author.id].delPokemon(poke1.name) #remove mon from your collection
                            self.users[context.message.mentions[0].id].addPokemon(poke1) #give the mon to the trader
                            poke2 = self.users[context.message.mentions[0].id].pokeDict[nameFix] #get traders mon before deleting it
                            self.users[context.message.mentions[0].id].delPokemon(poke2.name) #remove mon from traders collection
                            self.users[context.message.author.id].addPokemon(poke2) #give the mon to the you
                            self.set_pickle()
                            await context.send('{} has traded their {} for {}\'s {}.'.format(context.message.author.name, poke1.name,
                                                                                             context.message.mentions[0].name, poke2.name))
                else:
                    await context.send('{} does not own {}.'.format(context.message.author.name, myFix))
            else:
                await context.send('{} does not own {}.'.format(context.message.mentions[0].name, nameFix))
        else:
            await context.send('You can not trade with yourself.')


    @commands.command(name='left')
    async def leftover(self, context):
        if context.message.author.id not in self.users.keys():
            self.users[context.message.author.id] = User(None)
        await context.send('{} has {} rolls left.'.format(context.author.name, str(self.users[context.message.author.id].numberOfRolls)))

    @commands.command(name='time')
    async def time(self, context):
        CurMinute = int(datetime.now().strftime("%M"))
        minutesLeft = 60 - CurMinute
        await context.send('Rolls reset in {} minutes.'.format(str(minutesLeft)))

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

    @commands.command(name='help')
    async def help(self, context):
        embed = discord.Embed(type="rich")
        embed.description = 'Commands: \n\n !roll  :  Rolls a random, available pokemon. React to claim the pokemon\n' \
                            '!list @user : Lists all of users pokemon\n' \
                            '!check \'pokemonName\'  :  Check a pokemon\'s information\n' \
                            '!release \'pokemonName\'  :  Release pokemon if you own it\n' \
                            '!left  :  Check how many rolls you have left\n' \
                            '!time  :  Check time left till rolls reset\n' \
                            '!trade \'yourPokemon\' @user \'traderPokemon\'  :  Send trade request to a user\n\n' \
                            'Type !help command for more info on a command.'
        await context.send(embed= embed)

@client.event
async def on_ready():
    Poke = PokeBot(client)
    if os.path.isfile("data/users.pickle"):
        with open("data/users.pickle", 'rb') as file:
            try:
                users = pickle.load(file)
                if isinstance(users, dict):
                    print("Found obj")
                    Poke.users = users
                else:
                    print("Couldn't Find")
            except EOFError:
                print("EOFError")
            except Exception as Err:
                print(Err)
                pass
        file.close
    if os.path.isfile("data/owners.pickle"):
        with open("data/owners.pickle", 'rb') as file:
            try:
                owners = pickle.load(file)
                if isinstance(owners, dict):
                    print("Found obj")
                    Poke.ownership = owners
                else:
                    print("Couldn't Find")
            except EOFError:
                print("EOFError")
            except Exception as Err:
                print(Err)
                pass
        file.close
    if os.path.isfile("data/left.pickle"):
        with open("data/left.pickle", 'rb') as file:
            try:
                left = pickle.load(file)
                if isinstance(left, list):
                    print("Found obj")
                    Poke.pokemonLeft = left
                else:
                    print("Couldn't Find")
            except EOFError:
                print("EOFError")
            except Exception as Err:
                print(Err)
                pass
        file.close

    client.add_cog(Poke)
    print("Logged in as " + client.user.name)

client.run(TOKEN)