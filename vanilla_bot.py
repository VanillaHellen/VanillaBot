from pathlib import Path
from discord.ext import commands
import discord
import random
import json
import mysql.connector
import datetime
import os

script_location = Path(__file__).absolute().parent

db_data = {}
db_data['user']=os.environ['DB_USER']
db_data['password']=os.environ['DB_PASSWORD']
db_data['host']=os.environ['DB_HOST']
db_data['database']=os.environ['DB_DB']


def getUwuNumber(userId: str):
    number = 0
    try:
        dbcon = mysql.connector.connect(**db_data)
        cursor = dbcon.cursor(buffered=True, dictionary=True)
        cursor.execute(f"SELECT number FROM uwu_stats WHERE user_id = {userId}")
        result = cursor.fetchone()
        if result:
            number = result['number']
        cursor.close()
    except mysql.connector.Error as err:
        print(err)
    else:
        dbcon.close()
    return number


def dbInsertUserUwu(userId: str, numberToAdd: int):
    try:
        number = getUwuNumber(userId)
        dbcon = mysql.connector.connect(**db_data)
        cursor = dbcon.cursor(buffered=True)
        add_uwu = (f"""INSERT INTO uwu_stats
                (user_id, number)
            VALUES
                ({userId}, {number + numberToAdd})
            ON DUPLICATE KEY UPDATE
                number = VALUES(number);
                """)
        cursor.execute(add_uwu)
        dbcon.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(err)
    else:
        dbcon.close()



description = '''A custom bot made by VanillaHellen'''
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='?', help_command=None, description=description, intents=intents)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='Doki Doki UwU Club'))


@bot.command(
    description='Randomly picks an option from given ones.',
    usage=f'{bot.command_prefix}choose <option1, option2, ...>',
    help=f'{bot.command_prefix}choose 1 something "multiple words"'
    )
async def choose(ctx, *choices: str):
    await ctx.send(random.choice(choices))


@bot.command(
    description='Returns all commands available',
    usage=f'{bot.command_prefix}help',
    help=f'{bot.command_prefix}help'
    )
async def help(ctx):
    helptext = '''```
    Welcome to VanillaBot! :D\n\n
    Available commands:\n'''
    for command in bot.commands:
        helptext+=f'''
        {command}:'''
        helptext+=f'''
        {command.description}
        usage:
            {command.usage}
        example:
            {command.help}

        '''
    helptext+="```"
    await ctx.send(helptext)


@bot.command(
    description='The bot sends a prayer circle of emojis. Adding -h flag causes the bot to remove the command message',
    usage=f'{bot.command_prefix}pc [-h]',
    help=f'{bot.command_prefix}pc'
)
async def pc(ctx, flag: str = ''):
    b = '<:blank:773987871085953026>'
    c = ':candle:'
    p = ':pray:'
    first_line = b * 4 + c
    second_line = b * 2 + c + b * 3 + c
    third_line = b + c + b * 5 + c
    fourth_line = c + b * 3 + p + b * 3 + c

    message = '\n'.join([first_line, second_line, third_line, '', fourth_line, '', third_line, second_line, first_line])
    if flag == '-h':
        await ctx.message.delete()
    await ctx.send(message)

@bot.command(
    description='Rolls a Y dice X times.',
    usage=f'{bot.command_prefix}roll XdY',
    help=f'{bot.command_prefix}roll 2d6'
    )
async def roll(ctx, dice: str):
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in XdY, where X and Y are numbers!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)


@bot.command(
    description='Check your uwu stats. Adding a @tag after the command causes the bot to check the tagged user\'s stats',
    usage=f'{bot.command_prefix}uwu [@tag]',
    help=f'{bot.command_prefix}uwu @someone'
    )
async def uwu(ctx, user: discord.User = None):
    if user:
        if user == bot.user:
            await ctx.send('{} IS the uwu.'.format(user.mention))
        else:
            number = getUwuNumber(user.id)
            await ctx.send('{} has used uwu **{}** times!'.format(user.mention, number))
    else:
        number = getUwuNumber(ctx.message.author.id)
        await ctx.send('{}, you have used uwu **{}** times!'.format(ctx.message.author.mention, number))



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if 'uwu' in message.content.lower() and not message.content.startswith(f'{bot.command_prefix}uwu'):
        number = message.content.count('uwu')
        emoji = bot.get_emoji(372490965723643907)
        if not emoji:
            emoji = bot.get_emoji(505712821913255941)
        dbInsertUserUwu(message.author.id, number)
        await message.add_reaction(emoji)
    await bot.process_commands(message)


@choose.error
async def choose_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandInvokeError):
        await ctx.send('You must provide *something* to choose from!')


@bot.event
async def on_command_error(ctx, error):
    response = ''
    if isinstance(error, discord.ext.commands.BadArgument):
        response += 'Wrong argument! '
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        response += 'Missing argument! '
    response += 'If you\'re not sure how to use a command, call **?help** and try reading about it!'
    with open(script_location/'log.txt', 'a+') as log:
        log.write(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        + '\nSENT BY: ' + ctx.message.author.name + '#' + ctx.message.author.discriminator
        + ' (' + ctx.message.author.display_name + ')'
        + '\nMESSAGE: ' + ctx.message.content
        + '\nERROR: ' + str(error)
        + '\n----------------------------------------------\n') 
    await ctx.send(response)


bot.run(os.environ["ACCESS_TOKEN"])