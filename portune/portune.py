# -*- coding: utf-8 -*-
import re
import random
import os
import hoshino
from datetime import date
from hoshino.util import DailyNumberLimiter
from hoshino import R, Service
from hoshino.modules.priconne._pcr_data import CHARA_NAME
from hoshino.util import pic2b64
from hoshino.typing import *
from .luck_desc import luck_desc
from .luck_type import luck_type
from PIL import Image, ImageSequence, ImageDraw, ImageFont


#帮助文本
sv_help = '''
[抽签|人品|运势|抽凯露签]
随机角色/指定凯露预测今日运势
准确率高达114.514%！
'''.strip()
sv = Service('portune', help_=sv_help, bundle='pcr娱乐')


#也可以直接填写为res文件夹所在位置，例：absPath = "C:/res/"
Data_Path = hoshino.config.RES_DIR
Img_Path = Data_Path + 'img/portunedata/imgbase'
config = {}


@sv.on_rex(r'^抽(.+)?签|人品|运势$')
async def portune_chara(bot, ev):
    # 0. Initialize parameters
    global config
    uid = ev.user_id
    name = ev['match'].group(1)
    today = date.today()
    formal_name = None

    # 1. Check if the name is in _pcr_data.py
    for key in CHARA_NAME:
        if name in CHARA_NAME[key]:
            formal_name = CHARA_NAME[key][0]
            break

    # 2. If the name is not valid
    if name and (not formal_name or formal_name not in luck_desc):
        await bot.finish(ev,'图库里没有这个角色，试试其他的吧~', at_sender=True)

    # 3. Check if the user has drawn a fortune today
    if uid not in config or config[uid]['date'] != today:
        # Sample a chara or use the specified one
        chara = formal_name if formal_name else random.choice(list(luck_desc))
        charaid = random.choice(luck_desc[chara]['charaid'])
        # Save the configuration
        config[uid] = {}
        config[uid]['base_img'] = get_basemap_by_id(charaid)
        config[uid]['text'], config[uid]['title'] = get_info(charaid)
        config[uid]['name'] = chara
        config[uid]['date'] = today
    elif formal_name != config[uid]['name']:
        await bot.finish(ev, f'你今天已经抽过{config[uid]["name"]}签了~', 
                         at_sender=True)

    pic = drawing_pic(config[uid]['base_img'], config[uid]['text'], 
                      config[uid]['title'])
    await bot.send(ev, pic, at_sender=True)


def drawing_pic(base_img, text, title) -> Image:
    fontPath = {
        'title': R.img('portunedata/font/Mamelon.otf').path,
        'text': R.img('portunedata/font/sakura.ttf').path
    }

    filename = os.path.basename(base_img.path)
    charaid = filename.lstrip('frame_')
    charaid = charaid.rstrip('.jpg')

    img = base_img.open()
    # Draw title
    draw = ImageDraw.Draw(img)

    text = text['content']
    font_size = 45
    color = '#F5F5F5'
    image_font_center = (140, 99)
    ttfront = ImageFont.truetype(fontPath['title'], font_size)
    font_length = ttfront.getsize(title)
    draw.text((image_font_center[0]-font_length[0]/2,
               image_font_center[1]-font_length[1]/2),
               title, fill=color, font=ttfront)
    # Text rendering
    font_size = 25
    color = '#323232'
    image_font_center = [140, 297]
    ttfront = ImageFont.truetype(fontPath['text'], font_size)
    result = decrement(text)
    if not result[0]:
        return Exception('Unknown error in daily luck') 
    textVertical = []
    for i in range(0, result[0]):
        font_height = len(result[i + 1]) * (font_size + 4)
        textVertical = vertical(result[i + 1])
        x = int(image_font_center[0] + (result[0] - 2) * font_size / 2 + 
                (result[0] - 1) * 4 - i * (font_size + 4))
        y = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), textVertical, fill = color, font = ttfront)

    img = pic2b64(img)
    img = MessageSegment.image(img)
    return img


def get_basemap_by_id(charaid) -> R.ResImg:
    filename = 'frame_' + charaid + '.jpg'
    return R.img(os.path.join(Img_Path, filename))


def randombbasemap() -> R.ResImg:
    base_dir = R.img(Img_Path).path
    random_img = random.choice(os.listdir(base_dir))
    return R.img(os.path.join(Img_Path, random_img))


def get_info(charaid):
    for i in luck_desc:
        if charaid in i['charaid']:
            typewords = i['type']
            desc = random.choice(typewords)
            return desc, get_luck_type(desc)
    raise Exception('luck description not found')


def get_luck_type(desc):
    target_luck_type = desc['good-luck']
    for i in luck_type:
        if i['good-luck'] == target_luck_type:
            return i['name']
    raise Exception('luck type not found')


def decrement(text):
    length = len(text)
    result = []
    cardinality = 9
    if length > 4 * cardinality:
        return [False]
    numberOfSlices = 1
    while length > cardinality:
        numberOfSlices += 1
        length -= cardinality
    result.append(numberOfSlices)
    # Optimize for two columns
    space = ' '
    length = len(text)
    if numberOfSlices == 2:
        if length % 2 == 0:
            # even
            fillIn = space * int(9 - length / 2)
            return [numberOfSlices, text[:int(length / 2)] + fillIn, fillIn + text[int(length / 2):]]
        else:
            # odd number
            fillIn = space * int(9 - (length + 1) / 2)
            return [numberOfSlices, text[:int((length + 1) / 2)] + fillIn,
                                    fillIn + space + text[int((length + 1) / 2):]]
    for i in range(0, numberOfSlices):
        if i == numberOfSlices - 1 or numberOfSlices == 1:
            result.append(text[i * cardinality:])
        else:
            result.append(text[i * cardinality:(i + 1) * cardinality])
    return result


def vertical(str):
    list = []
    for s in str:
        list.append(s)
    return '\n'.join(list)
