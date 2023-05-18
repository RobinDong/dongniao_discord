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

MAX_RETRIES = 20
DONGNIAO_API_KEY = os.getenv("DONGNIAO_API_KEY")
DONGNIAO_API_URL = "https://us.dongniao.net/dnapi"
NIAODIAN_URL = "https://dongniao.net/nd/"
NIAODIAN_ICON_URL = "https://ca.dongniao.net/niaodian?birdiconid="
BIRD_ID_FILE = "final.121.new.txt"
CONF_THRESHOLD = 38

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
    while retry < MAX_RETRIES:
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


def draw_image(url, boxes):
    # get image
    resp = requests.get(url, stream=True)
    if resp.status_code != 200:
        return None, None
    buffer = BytesIO(resp.content)
    file_bytes = np.asarray(bytearray(buffer.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    for index, box in enumerate(boxes):
        cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (10, 10, 255), 2)
        cv2.putText(img, str(index+1), (box[0]+5, box[1]+55), cv2.FONT_HERSHEY_SIMPLEX, 2, (20,20,255), 4, 2)
    is_success, buffer = cv2.imencode(".jpg", img)
    return is_success, buffer


async def send_not_found(message, url):
    em = discord.Embed(title="Can't find bird in this picture")
    em.set_image(url=url)
    await message.channel.send(embed=em, reference=message)


async def dongniao_api(message):
    if message.attachments:
        url = message.attachments[0].url
    elif message.content[:5] == "http:" or message.content[:6] == "https:":
        url = message.content
    else:
        url = None
    if not url:
        return
    result_id = dongniao_result_id(url)
    if not result_id:
        await send_not_found(message, url)
        return
    cat_list = await dongniao_box_list(result_id)
    if not cat_list:
        await send_not_found(message, url)
        return
    # if message.channel.type == discord.ChannelType.text:
    # return original picture if there is only one bird in the picture
    if len(cat_list) == 1:
        bird_id = cat_list[0]['list'][0][2]
        if bird_id not in bird_id_map:
            await send_not_found(message, url)
            return
        eng_name, zh_name, sci_name = bird_id_map[bird_id]
        em = discord.Embed(title=eng_name, description=f"Scientific Name: [{sci_name}]({NIAODIAN_URL}{bird_id}/en)\n中文名: [{zh_name}]({NIAODIAN_URL}{bird_id})")
        # em.add_field(name="", value=f"Scientific Name: {sci_name}")
        # em.add_field(name="", value=f"中文名: [{zh_name}]({NIAODIAN_URL}{bird_id})")
        em.set_image(url=url)
        em.set_thumbnail(url=f"{NIAODIAN_ICON_URL}{bird_id}")
        await message.channel.send(embed=em, reference=message)
        return

    # drop box in cat_list that have confident smaller than threshold
    cat_list = list(filter(lambda item: item["list"][0][0] > CONF_THRESHOLD, cat_list))

    em = discord.Embed()
    boxes = [item["box"] for item in cat_list]
    is_success, buffer = draw_image(url, boxes)
    if not is_success:
        print("Failed to draw image {url}")
        return
    file = discord.File(filename=f"bird.jpg", fp=BytesIO(buffer))
    em.set_image(url=f"attachment://bird.jpg")
    for index, item in enumerate(cat_list):
        lst = item["list"]
        bird_id = lst[0][2]
        eng_name, zh_name, sci_name = bird_id_map[bird_id]
        em.add_field(name=f"{index+1}. {eng_name}", value=f"Scientific Name: [{sci_name}]({NIAODIAN_URL}{bird_id}/en)\n中文名: [{zh_name}]({NIAODIAN_URL}{bird_id})")
    await message.channel.send(embed=em, file=file, reference=message)
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

    await dongniao_api(message)


client.run(os.getenv("TOKEN"))
