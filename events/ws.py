import humecord

from humecord.utils import (
    discordutils,
    logger,
    colors
)

class HCOnWSResponse:
    def __init__(
            self
        ):

        self.name = "hc_on_ws_response"
        self.description = "Receieves commands from the configured websocket."

        self.event = "hc_on_ws_response"

        self.functions = {
            "send_offline": {
                "function": self.send_offline,
                "priority": 5
            }
        }

        global bot
        from humecord import bot

    async def send_offline(
            self,
            action: str,
            data: dict
        ):

        if action != "send_offline":
            return

        # Get the bot
        name = data["bot"]

        if not data["error"]:
            # Connection closed with status 1000 or 1001. Carry on.
            #return
            pass

        # Get bot from API
        data = await bot.api.get(
            "status",
            "bot",
            {
                "bot": name
            }
        )

        # Check if the bot has properly shut down
        if data["online"]:
            # Improper shutdown. Send an alert.
            if name in bot.config.sr_bots:
                channel = bot.client.get_channel(bot.config.sr_bots[name]["channel"])

            else:
                channel = bot.debug_channel

            await channel.send(
                ", ".join([f"<@{x}>" for x in bot.config.sr_offline_mentions]),
                embed = discordutils.create_embed(
                    f"{bot.config.lang['emoji']['error']}  {name} has shut down improperly.",
                    color = "error"
                )
            )

            # Tell the API to set them to offline
            await bot.api.put(
                "status",
                "override",
                {
                    "bot": name,
                    "changes": {
                        "online": False,
                        "error": True
                    }
                }
            )