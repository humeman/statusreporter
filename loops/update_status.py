import humecord

from humecord.utils import (
    dateutils,
    discordutils,
    debug
)

import time

class UpdateStatusLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 15
        
        self.name = "update_status"

        global bot
        from humecord import bot

    async def run(
            self
        ):
        data = await bot.api.get(
            "status",
            "bot",
            {
                "bot": "all"
            }
        )

        channel = bot.client.get_channel(bot.config.sr_status_channel)

        for name, details in bot.config.sr_bots.items():
            if name in data:
                status = data[name]

                if status["online"]:
                    embed = discordutils.create_embed(
                        profile = [status["details"]["cool_name"], status["details"]["avatar"]],
                        description = status["details"]["info"],
                        fields = status["details"]["fields"],
                        color = "success"
                    )

                else:
                    embed = discordutils.create_embed(
                        profile = [status["details"]["cool_name"], status["details"]["avatar"]],
                        description = f"Offline since `{dateutils.get_timestamp(status['last_ping'])}` (`{dateutils.dateutils.get_duration(time.time() - status['last_ping'])}` ago)",
                        color = "error"
                    )
                
            else:
                embed = discordutils.create_embed(
                    profile = [name[0].upper() + name[1:], "https://cdn.discordapp.com/emojis/858193695164334110.png?v=1"],
                    description = f"Status unknown.",
                    color = "icon_gray"
                )

            # Fetch message
            if name not in bot.files.files["__statusreporter__.json"]["status_messages"]:
                bot.files.files["__statusreporter__.json"]["status_messages"][name] = None

            msg_id = bot.files.files["__statusreporter__.json"]["status_messages"][name]

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
                    debug.print_traceback(f"Generate new status message for {name}")
                    continue
                
                msg_id = msg.id
                edit = False

            if edit:
                try:
                    await msg.edit(
                        embed = embed
                    )

                except:
                    debug.print_traceback(f"Edit status message for {name}")

            bot.files.files["__statusreporter__.json"]["status_messages"][name] = msg_id
            bot.files.write("__statusreporter__.json")