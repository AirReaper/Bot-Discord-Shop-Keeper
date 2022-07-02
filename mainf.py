import discord
import json
import os

from discord.ext import commands

config = json.load(open("config.json", "r"))

bot = commands.Bot(command_prefix=config["prefix"], intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot connecté.")

for file in os.listdir("cogs"):
    if file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:-3]}")

bot.run(config["token"])