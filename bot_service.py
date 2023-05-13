# This example requires the 'message_content' intent.
import os
import asyncio
import discord
import requests


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

DONGNIAO_API_KEY = os.getenv("DONGNIAO_API_KEY")
DONGNIAO_API_URL = "http://ca.dongniao.net/dongniao_2"


async def dongniao_api(message):
    url = message.attachments[0].url
    values = {"image": "image", "api_key": DONGNIAO_API_KEY, "url": url, "async": 1}
    resp = requests.post(DONGNIAO_API_URL, data=values)
    print("[url]", url)
    reply = resp.json()
    print("<<< ", reply, " >>>")
    if reply[0] != 1000:
        return
    result_id = reply[1]
    values = {
        "resultidv3": result_id,
        "api_key": DONGNIAO_API_KEY,
    }
    retry = 0
    while retry < 10:
        await asyncio.sleep(1)
        resp = requests.post(DONGNIAO_API_URL, data=values)
        reply = resp.json()
        print("((( ", reply, " )))")
        if len(reply) > 0 and reply[0] != 1000:
            break
        retry += 1
    reply = discord.Embed(title="Looks good!", description=message.author.mention)
    reply.set_image(url=url)
    # if message.channel.type == discord.ChannelType.text:
    print("Done")
    await message.channel.send(file=discord.File("/Users/rdong/Downloads/vicuna.png"))


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.attachments:
        return

    await dongniao_api(message)


client.run(os.getenv("TOKEN"))
