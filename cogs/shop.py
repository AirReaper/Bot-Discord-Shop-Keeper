import asyncio
import random

import discord
import json

from discord.ext import commands


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = json.load(open("config.json", "r"))
        self.colors = [0xFFE4E1, 0x00FF7F, 0xD8BFD8, 0xDC143C, 0xFF4500, 0xDEB887, 0xADFF2F, 0x800000, 0x4682B4, 0x006400, 0x808080, 0xA0522D, 0xF08080, 0xC71585, 0xFFB6C1, 0x00CED1]
        self.cache = {}
        self.messages = {}
        self.embeds = {}

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def new(self, ctx: commands.Context):
        questions = [
            "What will be the product name ?",
            "What will be the product prize ?",
            "Please send the product image here.",
            "What will be the destination channel ?"
        ]
        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        i = 1
        for q in questions:
            xx = await ctx.send(embed=discord.Embed(title=f"Question {i}", color=random.choice(self.colors), description=q))
            msg = await self.bot.wait_for("message", check=check)
            answers.append(msg.content)
            i+=1
            await xx.delete()
            await msg.delete()
        try:
            int(answers[3][2:-1])
            float(answers[1])
        except ValueError:
            return await ctx.send("The channel you mentionned or the prize are not correct.")

        embed = discord.Embed(title=answers[0], color=random.choice(self.colors), description=f"{answers[1]}€\nStock!")
        embed.set_image(url=answers[2])
        channel = self.bot.get_channel(int(answers[3][2:-1]))
        x = await channel.send(embed=embed)
        await x.add_reaction("🛒")
        await x.add_reaction("❌")

        products = json.load(open("products.json", "r"))
        products[str(x.id)] = {
            "name": answers[0],
            "prize": float(answers[1])
        }
        json.dump(products, open("products.json", "w"), indent=4)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        member = payload.member
        user = self.bot.get_user(payload.user_id)
        emoji = payload.emoji
        message_id = payload.message_id
        if self.bot.user in [member, user] : return
        is_dm = isinstance(self.bot.get_channel(payload.channel_id), discord.DMChannel)
        products = json.load(open("products.json", "r"))
        if str(message_id) in products.keys():
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(message_id)
            await message.remove_reaction(emoji, member)

            async def edit_cart():
                p = []
                total_prize = 0
                for product in cart_data.keys():
                    if self.cache[member.id][product] == 0:
                        continue
                    else:
                        p.append(
                            f"**{products[str(product)]['name']}** x **{self.cache[member.id][product]}**= **{round(products[str(product)]['prize'] * self.cache[member.id][product], 2)}€**\n")
                        total_prize += round(products[str(product)]["prize"], 2) * self.cache[member.id][product]

                products_string = "".join(p)
                delemitation = "~--------------------------------------~\nReact with ✔️ to confirm the order and create a ticket.\nReact with ❌ to cancel the order"
                due_embed = discord.Embed(title=f"Ticket for {member.name}", color=random.choice(self.colors),
                                      description=f"{products_string}\n**Total Prize: __{total_prize}__**\n{delemitation}")

                if member.id not in self.messages.keys():
                    dm = await member.send(embed=due_embed)
                    await dm.add_reaction("✔️")
                    await dm.add_reaction("❌")
                    self.messages[member.id] = dm.id
                    self.embeds[member.id] = due_embed.to_dict()
                else:
                    chann_user = self.bot.get_user(member.id)
                    priv_chann = chann_user.dm_channel
                    temp_msg = await priv_chann.fetch_message(self.messages[member.id])
                    self.embeds[member.id][
                        "description"] = f"{products_string}\n**Total Prize: __{round(total_prize, 2)}€__**\n{delemitation}"
                    edited_embed = discord.Embed.from_dict(self.embeds[member.id])
                    await temp_msg.edit(embed=edited_embed)

            if str(emoji) == "🛒":
                if member.id not in self.cache.keys():
                    self.cache[member.id] = {}
                if message_id not in self.cache[member.id].keys():
                    self.cache[member.id][message_id] = 0
                self.cache[member.id][message_id] += 1
                cart_data = self.cache[member.id]
                await edit_cart()

            if str(emoji) == "❌":
                if member.id not in self.cache.keys() or message_id not in self.cache[member.id].keys() or self.cache[member.id][message_id] <= 0: return
                self.cache[member.id][message_id] -= 1
                cart_data = self.cache[member.id]
                await edit_cart()

        elif is_dm:
            if str(emoji) == "✔️":
                guild = self.bot.get_guild(self.config["guild_id"])
                private_channel = user.dm_channel
                msg = await private_channel.fetch_message(self.messages[user.id])
                tickets_catergory = discord.utils.get(guild.categories, id=self.config["tickets_category"])
                await tickets_catergory.set_permissions(user, read_messages=True)
                command_channel = await guild.create_text_channel(f"ticket-{user.name}", category=tickets_catergory)
                embed = discord.Embed(title=f"Ticket {user.name.capitalize()}", color=random.choice(self.colors), description=
                                      f"**Order Summary ->**\n\n{self.embeds[user.id]['description'].split('~')[0]}\n"
                                      f"Use the command `!close` to close this ticket!")
                await command_channel.send(embed=embed)
                del self.embeds[user.id]
                del self.cache[user.id]
                del self.messages[user.id]
                await msg.delete()

                tickets = json.load(open("tickets.json", "r"))
                tickets[str(command_channel.id)] = user.id
                json.dump(tickets, open("tickets.json", "w"), indent=4)

            if str(emoji) == "❌":
                private_channel = user.dm_channel
                msg = await private_channel.fetch_message(self.messages[user.id])
                del self.embeds[user.id]
                del self.cache[user.id]
                del self.messages[user.id]
                await msg.edit(embed=discord.Embed(description="Order Canceled.", color=random.choice(self.colors)))
                for reaction in msg.reactions:
                    await msg.remove_reaction(reaction, self.bot.user)
                await asyncio.sleep(5)
                await msg.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, msg_id):
        data = json.load(open("products.json", "r"))
        if not msg_id in data.keys():
            return await ctx.send(embed=discord.Embed(color=random.choice(self.colors), description="No product found with this id"))
        name = data[msg_id]["name"]
        try:
            msg = await ctx.channel.fetch_message(int(msg_id))
            await msg.delete()
        except Exception:
            pass
        await ctx.send(embed=discord.Embed(color=random.choice(self.colors), description=f"The product `{name}` was removed from the shop."))
        del data[msg_id]
        json.dump(data, open("products.json", "w"), indent=4)

    @commands.command()
    async def close(self, ctx):
        tickets = json.load(open("tickets.json", "r"))
        if str(ctx.channel.id) in tickets.keys():
            channel = self.bot.get_channel(ctx.channel.id)
            embed = discord.Embed(title="Ticket closed.", color=random.choice(self.colors),
                                  description="This ticket channel will be closed in 5 seconds.")
            await channel.send(embed=embed)
            await asyncio.sleep(5)
            await channel.delete()
            del tickets[str(ctx.channel.id)]
            json.dump(tickets, open("tickets.json", "w"), indent=4)

def setup(bot): bot.add_cog(Shop(bot))