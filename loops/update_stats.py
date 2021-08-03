import humecord

from humecord.utils import (
    dateutils,
    discordutils,
    debug,
    miscutils
)

import time

class UpdateStatsLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 60
        
        self.name = "update_stats"

        global bot
        from humecord import bot

    async def run(
            self
        ):
        channel = bot.client.get_channel(bot.config.sr_stats_channel)

        for mtype in ["bot", "api"]:
            data = await bot.api.get(
                "stats",
                mtype,
                {
                    "bot": "all"
                }
            )

            if mtype == "bot":
                fields = []

                for name, stats in data.items():
                    details = [
                        f"__Commands__",
                        f"%-b% Today: {miscutils.friendly_number(stats['commands']['day']['count'])}",
                        f"%-b% Total: {miscutils.friendly_number(stats['commands']['total'])}",
                        " "
                    ]

                    uptime_header = f"__Uptime__"

                    if stats["uptime"]["month"]["month"] is not None:
                        if len(details) == 4:
                            details.append(uptime_header)

                        details.append(
                            f"%-b% Monthly: {round((stats['uptime']['month']['count'] / (time.time() - stats['uptime']['month']['start'])) * 100, 1)}%"
                        )
                    
                    if stats["uptime"]["total"]["start"] is not None:
                        if len(details) == 4:
                            details.append(uptime_header)

                        details.append(
                            f"%-b% Total: {round((stats['uptime']['total']['count'] / (time.time() - stats['uptime']['total']['start'])) * 100, 1)}%"
                        )

                    if details[-1] != " ":
                        details.append(" ")

                    fields.append(
                        {
                            "name": f"%-a% {name[0].upper()}{name[1:]}",
                            "value": "\n".join(details),
                            "inline": True
                        }
                    )

                embeds = [
                    discordutils.create_embed(
                        "Bot statistics",
                        fields = fields
                    )
                ]

            elif mtype == "api":
                fields = []
                for name, count in data["categories"].items():
                    name = name[0].upper() + name[1:]

                    if count["fail"] > 0 and count["success"] > 0:
                        emoji = "status_yellow"

                    elif count["fail"] > 0:
                        emoji = "status_red"

                    else:
                        emoji = "status_green"
                    
                    fields.append(
                        {
                            "name": f"%-a% {bot.config.lang['emoji'][emoji]}  {name}",
                            "value": f"__Succeeded:__ {miscutils.friendly_number(count['success'])}\n__Failed:__ {miscutils.friendly_number(count['fail'])}",
                            "inline": True
                        }
                    )

                embeds = [
                    discordutils.create_embed(
                        "Requests",
                        description = f"__Succeeded:__ {miscutils.friendly_number(data['total']['success'])}\n__Failed:__ {miscutils.friendly_number(data['total']['fail'])}",
                        footer = f"Tracking since the API's creation."
                    ),
                    discordutils.create_embed(
                        "Requests this hour",
                        fields = fields,
                        footer = f"Tracking since {dateutils.get_timestamp(data['current'] * 3600)}."
                    )
                ]

            if mtype not in bot.files.files["__statusreporter__.json"]["stats_messages"]:
                bot.files.files["__statusreporter__.json"]["stats_messages"][mtype] = None

            msg_id = bot.files.files["__statusreporter__.json"]["stats_messages"][mtype]

            edit = True
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
                        embeds = embeds
                    )

                except:
                    debug.print_traceback(f"Generate new stats message for {mtype}")
                    continue
                
                msg_id = msg.id
                edit = False

            if edit:
                try:
                    await msg.edit(
                        embeds = embeds
                    )

                except:
                    debug.print_traceback(f"Edit stats message for {mtype}")

            bot.files.files["__statusreporter__.json"]["stats_messages"][mtype] = msg_id
            bot.files.write("__statusreporter__.json")