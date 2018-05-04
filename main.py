import time
import asyncio
import threading
import discord
import os
import sys

OSU_APIKEY = os.getenv("OSU_APIKEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = None

def cmd_thread_handler(loop):
    asyncio.set_event_loop(loop)
    while True:
        try:
            line = input("pepster> ")
            line = line.strip()
            if not line:
                continue
            print("you said :", line)
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit(0)

def client_thread_handler(loop, token):
    asyncio.set_event_loop(loop)
    client = discord.Client(loop=client_loop)

    @client.event
    async def on_ready():
        print("Bot has logged in as {}.".format(client.user.name))

    client.run(token)


if __name__ == "__main__":
    assert OSU_APIKEY, "Make sure osu! API key (OSU_APIKEY) is set."
    assert BOT_TOKEN, "Make sure the bot token (BOT_TOKEN) is set."

    cmd_loop = asyncio.new_event_loop()
    cmd_thread = threading.Thread(target=cmd_thread_handler, args=(cmd_loop,))
    cmd_thread.start()

    client_loop = asyncio.new_event_loop()
    client_thread = threading.Thread(target=client_thread_handler, args=(client_loop, BOT_TOKEN))
    client_thread.start()
