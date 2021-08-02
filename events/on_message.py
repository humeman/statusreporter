import humecord

from humecord.utils import (
    discordutils
)

import discord

class OnMessageEvent:
    def __init__(
            self
        ):
        self.name = "on_message"

        self.event = "on_message"

        self.functions = {
            "check_humecord": {
                "function": self.check_humecord,
                "priority": 10
            }
        }

    async def check_humecord(
            self,
            message
        ):

        if message.channel.id == 849743627105468468:
            if message.webhook_id is not None:
                await message.publish()