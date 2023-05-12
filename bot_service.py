# This example requires the 'message_content' intent.
import os
import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.attachments:
        print(message.attachments)
        url = message.attachments[0].url
        if message.channel.type == discord.ChannelType.text:
            print("mention:", message.author.mention)
            reply = discord.Embed(title="Looks good!", description=message.author.mention)
            reply.set_image(url=url)
            await message.channel.send(embed=reply)
        else:
            await message.channel.send(file=discord.File("/Users/rdong/Downloads/vicuna.png"))

client.run(os.getenv("TOKEN"))
