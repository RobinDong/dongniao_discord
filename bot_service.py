# This example requires the 'message_content' intent.
import os
import cv2
import asyncio
import discord
import requests
import numpy as np

from io import BytesIO


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

DONGNIAO_API_KEY = os.getenv("DONGNIAO_API_KEY")
DONGNIAO_API_URL = "http://ca.dongniao.net/dongniao_2"
NIAODIAN_URL = "http://dongniao.net/nd/"
NIAODIAN_ICON_URL = "https://ca.dongniao.net/niaodian?birdiconid="
BIRD_ID_FILE = "final.121.new.txt"

bird_id_map = {}


def dongniao_result_id(url):
    values = {"image": "image", "api_key": DONGNIAO_API_KEY, "url": url, "async": 1}
    resp = requests.post(DONGNIAO_API_URL, data=values)
    reply = resp.json()
    print("<<< ", reply, " >>>")
    if reply[0] != 1000:
        return None
    result_id = reply[1]
    return result_id


async def dongniao_box_list(result_id):
    values = {"resultidv3": result_id, "api_key": DONGNIAO_API_KEY}
    retry = 0
    cat_list = None
    while retry < 10:
        await asyncio.sleep(2)
        resp = requests.post(DONGNIAO_API_URL, data=values)
        reply = resp.json()
        print("((( ", reply, " )))")
        if len(reply) > 0 and reply[0] != 1000:
            if type(reply[0]) == dict:
                cat_list = reply
            break
        retry += 1
    return cat_list


def draw_image(url, box):
    # get image
    resp = requests.get(url, stream=True)
    if resp.status_code != 200:
        return None, None
    buffer = BytesIO(resp.content)
    file_bytes = np.asarray(bytearray(buffer.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (10, 10, 255), 2)
    is_success, buffer = cv2.imencode(".jpg", img)
    return is_success, buffer


async def dongniao_api(message):
    url = message.attachments[0].url
    result_id = dongniao_result_id(url)
    if not result_id:
        return
    cat_list = await dongniao_box_list(result_id)
    if not cat_list:
        em = discord.Embed(title="Can't find bird in this picture", description=message.author.mention)
        em.set_image(url=url)
        await message.channel.send(embed=em)
        return
    # if message.channel.type == discord.ChannelType.text:
    # return original picture if there is only one bird in the picture
    if len(cat_list) == 1:
        bird_id = cat_list[0]['list'][0][2]
        if bird_id not in bird_id_map:
            return
        eng_name, zh_name, sci_name = bird_id_map[bird_id]
        em = discord.Embed(title=eng_name)
        em.add_field(name="", value=f"Scientific Name: {sci_name}")
        em.add_field(name="", value=f"中文名: [{zh_name}]({NIAODIAN_URL}{bird_id})")
        em.set_image(url=url)
        em.set_thumbnail(url=f"{NIAODIAN_ICON_URL}{bird_id}")
        await message.channel.send(embed=em)
        return
    for item in cat_list:
        box, lst = item["box"], item["list"]
        em = discord.Embed(title=f"{lst[0][1]}", description=message.author.mention)
        is_success, buffer = draw_image(url, box)
        if is_success:
            file = discord.File(filename=f"{lst[0][1]}.jpg", fp=BytesIO(buffer))
            em.set_image(url=f"attachment://{lst[0][1]}.jpg")
            await message.channel.send(embed=em, file=file)
    print("Done")
    # await message.channel.send(file=file)


@client.event
async def on_ready():
    with open(BIRD_ID_FILE, "r") as fp:
        lines = fp.readlines()
        for line in lines:
            arr = line.split(",")
            bird_id_map[int(arr[0])] = arr[3:6]
    print("bird_id_map:", len(bird_id_map))
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.attachments:
        return

    await dongniao_api(message)


client.run(os.getenv("TOKEN"))
