
from humecord.utils import (
    discordutils
)


class ControlCommand:
    def __init__(
            self
        ):

        self.name = "control"
        self.description = "Controls all connected Humecord bots."

        self.aliases = ["c", "cmd", "ctrl", "run", "rcon"]

        self.permission = "bot.dev"

        self.shortcuts = {
        }

        global bot
        from humecord import bot

    async def run(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):

        # Check args
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a list of bots and an action to run."
                )
            )
            return

        bots = args[1].lower().split(",")

        comp = []

        for name in bots:
            if name in bot.config.sr_bots:
                comp.append(name)

            elif name in bot.config.sr_categories:
                comp += bot.config.sr_categories[name]

            else:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid bot!",
                        f"Name `{name}` didn't match any bots or categories."
                    )
                )
                return

        # Get action
        action = args[2].lower()
        data = {}
        if action == "reload":
            force = False
            if len(args) > 3:
                if args[3].lower() in ["force", "f"]:
                    force = True

            data["force"] = force

            detail = f"Reload (force: {'Yes' if force else 'No'})"

        elif action in ["shutdown", "literallyjustfuckingdieihateyousomuch"]:
            action = "shutdown"
            detail = "Shut down"

        elif action == "kill":
            detail = "Kill"

        elif action in ["command", "cmd", "run"]:
            action = "command"
            if len(args) < 4:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid syntax!",
                        f"Specify a command to run."
                    )
                )
                return

            data["command"] = " ".join(args[3:])

            detail = f"Command ({data['command']})"

        else:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid action!",
                    f"Valid actions include: `reload, shutdown, kill, command`"
                )
            )
            return

        

        # Execute action
        await bot.ws.send(
            "send_command",
            {
                "bots": comp,
                "action": action,
                "data": data
            }
        )

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Sent action to {len(bots)} bots.",
                description = f"**Action:** {detail}\n\n**Bot{'' if len(bots) == 1 else 's'}:** {','.join(bots)}",
                color = "success"
            )
        )