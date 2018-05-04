import asyncio
import logging
import sys
import traceback
from datetime import datetime

import discord
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse

from data import channels
from utils import queue_logger as logger

def hash_queue(row):
    authorp = row.find("p", attrs={"class": "topicauthor"})
    if authorp is None:
        return None
    author_u = authorp.find("a")["href"].strip("/u/")
    titlea = row.find("a", attrs={"class": "topictitle"})
    title = titlea.string.strip()
    return "{}:{}".format(author_u, title)

def get_last_updated(row):
    el = row.find("time", attrs={"class": "timeago"})
    if not el:
        return None
    # 2018-03-04T07:13:34Z
    return parse(el["datetime"])  # '%a %B %d %H:%M:%S +0800 %Y')

async def fetch_queues():
    global client
    queue_page = "https://osu.ppy.sh/forum/60"
    contents = requests.get(queue_page).text
    soup = BeautifulSoup(contents, "html.parser")
    table = soup.find("table", attrs={"class": "forum_posts_table"})
    rows = table.findAll("tr")
    queues = dict()
    for row in rows:
        authorp = row.find("p", attrs={"class": "topicauthor"})
        titlea = row.find("a", attrs={"class": "topictitle"})
        directlinka = row.find("a", attrs={"class": "blacklink"})
        h = hash_queue(row)
        latest = get_last_updated(row)
        if not all([h, latest, titlea, directlinka]):
            continue
        title = titlea.string.strip()
        directlink = directlinka["href"]
        queues[h] = dict(
            forumlink=titlea["href"],
            author=authorp.find("a").string,
            title=title,
            directlink=directlink,
            last_updated=latest
        )
    return queues

def start_queue(client, loop):
    async def wrapped(client):
        logger.info("b")
        queue_channel = client.get_channel(channels["queue"])
        logger.error("type:" + str(type(queue_channel)))
        queues = await fetch_queues()

        logger.info("fetched")
        while True:
            try:
                # await client.send_message(queue_channel, "scanning for new queues now..")
                logger.info("scanning now")
                queues_new = await fetch_queues()
                new_queues = dict()
                for h, queue in queues_new.items():
                    if h not in queues or queues[h].get("last_updated") is None:
                        new_queues.update({h: queue})
                    elif queue.get("last_updated") is None:
                        continue
                    elif queue["last_updated"] > queues[h]["last_updated"]:
                        new_queues.update({h: queue})
                logger.info("new queues: " + repr(new_queues))
                updates = []
                for h, queue in new_queues.items():
                    embed = discord.Embed(
                        title=queue.get("title"),
                        url="https://osu.ppy.sh{}".format(queue.get("directlink")),
                    )
                    embed.set_author(name=queue.get("author"))
                    updates.append(embed)
                for embed in updates:
                    logger.info("sending embed: {}".format(embed))
                    await client.send_message(queue_channel, embed=embed)
                queues = queues_new
                await asyncio.sleep(15)
            except KeyboardInterrupt:
                break
            except:
                logger.error(traceback.format_exc())

    # asyncio.set_event_loop(loop)
    # asyncio.ensure_future(wrapped())
    return wrapped(client)
