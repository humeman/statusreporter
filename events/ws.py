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

        # Get the command
        action = data["action"]

        bot = data["data"]["bot"]

        humecord.terminal.log(f"helo,,, bot {bot}'s has offline,, please fix It right now", True)