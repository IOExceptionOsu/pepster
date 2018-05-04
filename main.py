import asyncio
import concurrent
import json
import logging
import argparse
import multiprocessing
import os
import re
import string
import sys
import time
import unicodedata

import discord
from osuapi import OsuApi, ReqConnector

from aioconsole import AsynchronousCli
from data import channels, emojis
from queuebot import start_queue
from state import State
from utils import chat_logger as logger
from utils import get_attachment

OSU_APIKEY = os.getenv("OSU_APIKEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = None

mapset_pattern = re.compile(r".*https?://osu.ppy.sh/(s|beatmapsets)/(\d+).*")
map_pattern = re.compile(r".*https?://osu.ppy.sh/b/(\d+).*")

def start_cmd(loop):
    global client
    madchan = client.get_channel(channels["mad"])

    @asyncio.coroutine
    def wrapped(reader, writer, text, *args, **kwargs):
        msg = " ".join(text)
        writer.write("%s\n" % repr((args, kwargs)))
        yield from client.send_message(madchan, msg)
        yield from writer.drain()
        return

        # print(madchan)
        # while True:
        #     try:
        #         line = input("pepster> ")
        #         line = line.strip()
        #         if not line:
        #             continue
        #     except KeyboardInterrupt:
        #         print("Exiting...")
        #         sys.exit(0)

    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title="subcommands")
    sendc = subparser.add_parser("send")
    sendc.add_argument("text", nargs="*")
    return AsynchronousCli(dict(pepster=(wrapped, parser)), prog="pepster")

def start_client(token):
    global client
    client = discord.Client()

    pinset = set()
    state = State.load()
    with open("colors.json") as f:
        colors_raw = dict(json.load(f))
        colors = dict()
        for k, v in colors_raw.items():
            colors.update({k.lower(): v})
    osuapi = OsuApi(OSU_APIKEY, connector=ReqConnector())
    mapcolors = {
        -2: colors.get("darkgray"),
        -1: colors.get("darkgray"),
        0: colors.get("darkgray"),
        1: colors.get("lime"),
        2: colors.get("lime"),
        3: colors.get("gold"),
        4: colors.get("pink")
    }

    letteremojis = dict()
    for i, c in enumerate(string.ascii_lowercase):
        letteremojis.update({c: unicodedata.lookup("REGIONAL INDICATOR SYMBOL LETTER " + c.upper())})

    def hex2rgb(h): return int(h, 16)

    def filterstar(b):
        if "lcfc's easy" in b.version.lower():
            return 10000
        if "akitoshi's normal" in b.version.lower():
            return 9999
        return b.difficultyrating

    @client.event
    async def on_ready():
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(start_queue(client, loop))
        asyncio.ensure_future(start_cmd(loop).interact())
        # executor = concurrent.futures.ThreadPoolExecutor()
        # asyncio.get_event_loop().run_in_executor(executor, start_queue, client, loop)
        # asyncio.get_event_loop().run_in_executor(executor, start_cmd, loop)

        print("Bot has logged in as {}.".format(client.user.name))

    @client.event
    async def on_reaction_add(reaction, user):
        test = False
        pinchannel = client.get_channel(id=channels["pins"])
        if reaction.message.channel.id == channels["pintest"]:
            pinchannel = client.get_channel(id=channels["pintest"])
            test = True
        if test or reaction.message.id not in pinset and reaction.message.channel != pinchannel and (reaction.count == 5) or (reaction.count == 3 and "itsfineman" in reaction.emoji.name):
            pinset.add(reaction.message.id)
            state.save()

            body = "{} <@{}>: {}".format(str(reaction.emoji), reaction.message.author.id, reaction.message.clean_content)
            f = get_attachment(reaction.message)
            if f is not None:
                msg = await client.send_file(pinchannel, f.name, content=body)
                logging.getLogger().error("msg = " + str(msg))
            else:
                await client.send_message(pinchannel, body)

    @client.event
    async def on_message(message):
        # log the message
        logger.info("server={server}:channel={channel}:user={{id:{userid},username:{username},nick:{usernick}}}:message:{message}".format(server=message.server.name,
                                                                                                                                          channel=message.channel.name, userid=message.author.id, username=message.author.name, usernick=message.author.nick, message=repr(message.clean_content)))

        if message.content == "WEW":
            return await client.send_message(message.channel, "LAD")
        elif message.content == "wew":
            return await client.send_message(message.channel, "lad")

        if message.content.lower().startswith("!color"):
            parts = message.content.split(" ")
            if len(parts) < 2:
                return await client.send_message(message.channel, 'usage: `!color dodgerblue` cept replace dodgerblue with whatever from https://www.w3schools.com/colors/colors_names.asp')
            color_name = parts[1].lower()
            if color_name == "none":
                keep = []
            else:
                color = colors.get(color_name)
                if not color:
                    return await client.send_message(message.channel, 'i dont kno that color Bro. get one here https://www.w3schools.com/colors/colors_names.asp')
                roles = message.server.roles
                color_role = None
                for role in roles:
                    if role.name == "Color: {}".format(color_name):
                        color_role = role
                        break
                else:
                    role = await client.create_role(message.server)
                    await client.edit_role(message.server, role, name="Color: {}".format(color_name), permissions=discord.Permissions(0), colour=discord.Color(hex2rgb(color)))
                    color_role = role
                keep = [color_role]
            for role in message.author.roles:
                if not role.name.startswith("Color:"):
                    keep.append(role)
            await client.replace_roles(message.author, *keep)
            emoji = discord.Emoji(id="418875117905641477", server=message.server)
            return await client.add_reaction(message, emoji)
        elif message.content.lower().startswith("!play"):
            parts = message.content.split(" ")
            if len(parts) >= 2:
                playing = " ".join(parts[1:])
                await client.change_presence(game=discord.Game(name=playing))
                await client.delete_message(message)
        elif message.content.lower().startswith("!react"):
            parts = message.content.split(" ")
            if len(parts) >= 2:
                word = re.sub(r"[^a-z]", "", "".join(parts[1:]).lower())
                async for msg in client.logs_from(message.channel, limit=1, before=message):
                    print(word, msg.content)
                    for c in word:
                        emojiname = letteremojis.get(c)
                        await client.add_reaction(msg, emojiname)
                    await client.delete_message(message)

        match = mapset_pattern.match(message.content)
        if match:
            sid = match.group(2)
            if not sid.isdigit():
                return
            mapset = osuapi.get_beatmaps(beatmapset_id=sid)
            if not mapset:
                return await client.send_message(message.channel, "could not find mapset with id {}".format(sid))
            mapset.sort(key=lambda b: filterstar(b), reverse=True)
            first = mapset[0]
            description = "Length: {} / BPM: {}\n".format(time.strftime('%M:%S', time.gmtime(first.total_length)), round(first.bpm, 2))

            def helper(b):
                return "**{}**: {}\n  CS{} / AR{} / OD{} / HP{}".format(
                    b.version, round(b.difficultyrating, 2),
                    b.diff_size, b.diff_approach, b.diff_overall, b.diff_drain
                )
            description += "\n".join(map(helper, mapset[:5]))
            if len(mapset) > 5:
                description += "\n...{} more difficult{}".format(len(mapset) - 5, "y" if len(mapset) - 5 == 1 else "ies")
            embed = discord.Embed(
                title="{} - {}".format(first.artist, first.title),
                color=discord.Color(hex2rgb(mapcolors.get(first.approved.value, colors.get("darkgray")))),
                url="https://osu.ppy.sh/s/{}".format(sid),
                type="rich",
                description=description,
            )
            embed.set_thumbnail(url="https://b.ppy.sh/thumb/{}l.jpg".format(sid))
            embed.set_footer(text="mapset by {}".format(first.creator))
            return await client.send_message(message.channel, embed=embed)

        match = map_pattern.match(message.content)
        if match:
            bid = match.group(1)
            if not bid.isdigit():
                return
            mapset = osuapi.get_beatmaps(beatmap_id=bid)
            if not mapset:
                return await client.send_message(message.channel, "could not find map with id {}".format(bid))
            mapset.sort(key=lambda b: filterstar(b), reverse=True)
            first = mapset[0]
            description = "Length: {} / BPM: {}\n".format(time.strftime('%M:%S', time.gmtime(first.total_length)), round(first.bpm, 2))
            description += "**{}**: {}\n  CS{} / AR{} / OD{} / HP{}".format(
                first.version, round(first.difficultyrating, 2),
                first.diff_size, first.diff_approach, first.diff_overall, first.diff_drain
            )
            embed = discord.Embed(
                title="{} - {}".format(first.artist, first.title),
                color=discord.Color(hex2rgb(mapcolors.get(first.approved.value, colors.get("darkgray")))),
                url="https://osu.ppy.sh/b/{}".format(bid),
                type="rich",
                description=description,
            )
            embed.set_thumbnail(url="https://b.ppy.sh/thumb/{}l.jpg".format(first.beatmapset_id))
            embed.set_footer(text="mapset by {}".format(first.creator))
            return await client.send_message(message.channel, embed=embed)

        if "lofl" in message.content.lower():
            emoji = discord.Emoji(id=emojis["lofl"], server=message.server)
            return await client.add_reaction(message, emoji)

    client.run(token)


if __name__ == "__main__":
    assert OSU_APIKEY, "Make sure osu! API key (OSU_APIKEY) is set."
    assert BOT_TOKEN, "Make sure the bot token (BOT_TOKEN) is set."

    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    start_client(BOT_TOKEN)
