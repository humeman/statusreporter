import humecord

from humecord.utils import (
    discordutils,
    debug,
    miscutils
)

import time
import psutil
import concurrent
import asyncio

class UpdateResourcesLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 15
        
        self.name = "update_resources"

        global bot
        from humecord import bot

    async def run(
            self
        ):
        with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
            future = executor.submit(get_utilization)

            while not future.done():
                await asyncio.sleep(0.05)

            details = future.result()

        details = [
            f"CPU usage: {details['cpu_percent']}%",
            f"RAM usage: {details['ram_percent']}% {details['ram_usage']}",
            f"Swap usage: {details['swap_percent']}% {details['swap_usage']}",
            f"Disk usage: {details['disk_percent']}% {details['disk_usage']}"
        ]

        lb = "\n"
        embed = discordutils.create_embed(
            title = "Server resource utilization",
            description = f"```yml\n{lb.join(details)}```"
        )

        channel = bot.client.get_channel(bot.config.sr_resources_channel)

        # Fetch message
        if "main" not in bot.files.files["__statusreporter__.json"]["resources_messages"]:
            bot.files.files["__statusreporter__.json"]["resources_messages"]["main"] = None

        msg_id = bot.files.files["__statusreporter__.json"]["resources_messages"]["main"]

        edit = True
        msg = None
        if msg_id is not None:
            fetch = True
            if msg_id in bot.mem_storage["message_cache"]:
                if bot.mem_storage["message_cache"][msg_id]["time"] > time.time() - 86400:
                    fetch = False
                    msg = bot.mem_storage["message_cache"][msg_id]["msg"]

            if fetch:
                try:
                    msg = await discordutils.fetch_message(channel, msg_id, retries = 5)

                except:
                    msg_id = None

                else:
                    bot.mem_storage["message_cache"][msg_id] = {
                        "msg": msg,
                        "time": time.time()
                    }
        
        if msg_id is None:
            # Generate a new message
            try:
                msg = await channel.send(
                    embed = embed
                )

            except:
                debug.print_traceback(f"Generate new resources message")
                return
            
            msg_id = msg.id
            edit = False

        if edit:
            try:
                await msg.edit(
                    embed = embed
                )

            except:
                debug.print_traceback(f"Edit resources message")

        bot.files.files["__statusreporter__.json"]["resources_messages"]["main"] = msg_id
        bot.files.write("__statusreporter__.json")

def get_utilization():
    cpu = psutil.cpu_percent(interval = None, percpu = True)
    cpu_percent = miscutils.friendly_number(sum(cpu) / len(cpu), trunc = True) # No interval so this doesn't block the main thread

    mem = psutil.virtual_memory()
    gb = (1024 * 1024 * 1024)
    ram_percent = miscutils.friendly_number(mem.percent, trunc = True)
    ram_usage = f"({round(mem.used / gb, 1)} GB/{round(mem.total / gb, 1)} GB)"

    swap = psutil.swap_memory()
    swap_percent = miscutils.friendly_number(swap.percent, trunc = True)
    swap_usage = f"({round(swap.used / gb, 1)} GB/{round(swap.total / gb, 1)} GB)"

    disk = psutil.disk_usage("/")
    disk_percent = miscutils.friendly_number(disk.percent, trunc = True)
    disk_usage = f"({round(disk.used / gb, 1)} GB/{round(disk.total / gb, 1)} GB)"

    return {
        "cpu_percent": cpu_percent,
        "ram_percent": ram_percent,
        "ram_usage": ram_usage,
        "swap_percent": swap_percent,
        "swap_usage": swap_usage,
        "disk_percent": disk_percent,
        "disk_usage": disk_usage
    }