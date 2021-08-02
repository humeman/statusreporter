import libtmux
from humecord.utils import (
    discordutils,
    debug
)
import json
import asyncio

import humecord


class TmuxCommand:
    def __init__(
            self
        ):

        self.name = "tmux"
        self.description = "Controls tmux sessions."

        self.aliases = ["t", "screen"]

        self.permission = "bot.dev"

        self.subcommands = {
            "__default__": {
                "function": self.list,
                "description": "Lists active tmux sessions."
            },
            "start": {
                "function": self.start,
                "description": "Starts a session or window.",
                "syntax": "[target]"
            },
            "close": {
                "function": self.close,
                "description": "Closes a session or window.",
                "syntax": "[target]"
            },
            "kill": {
                "function": self.close,
                "description": "Kills a session or window.",
                "syntax": "[target]"
            },
            "restart": {
                "function": self.restart,
                "description": "Restarts a session or window.",
                "syntax": "[target]"
            },
            "show": {
                "function": self.show,
                "description": "Displays the console of a session or window.",
                "syntax": "[target]"
            },
            "send": {
                "function": self.send,
                "description": "Sends keypresses to a session or window.",
                "syntax": "[target] [command]"
            }
        }

        self.shortcuts = {
            "start": "tmux start",
            "kill": "tmux kill",
            "restart": "tmux restart",
            "show": "tmux show",
            "send": "tmux send"
        }

        global bot
        from humecord import bot

    async def list(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):

        await self.verify_server()

        active_sessions = {}

        # Iterate over each tmux session.
        for session in bot.tmux.list_sessions():
            # First, check if the ID is one we're supposed to watch.
            # For some reason, session_name isn't a thing?
            details = dict(session.items())

            name = details["session_name"]

            if name in bot.config.sr_tmux:
                active_sessions[name] = session


        fields = []
        # Start compiling into a message
        for session_name, windows in bot.config.sr_tmux.items():
            # Find out if the session exists.
            if session_name in active_sessions:
                emoji = bot.config.lang["emoji"]["status_green"]
                # Send info on each of the session's windows.
                session_comp = []

                active_windows = self.list_windows(active_sessions[session_name])

                for window in windows:
                    if window in active_windows:
                        session_comp.append(f"%-b% {bot.config.lang['emoji']['toggle_on']}  `{window}`")

                    else:
                        session_comp.append(f"%-b% {bot.config.lang['emoji']['toggle_off']}  `{window}`")
                
                details = "\n".join(session_comp)

            else:
                details = f"*Offline*"
                emoji = bot.config.lang["emoji"]["status_red"]

            fields.append(
                {
                    "name": f"%-a% {emoji}  {session_name}",
                    "value": details
                }
            )

        await resp.send(
            embed = discordutils.create_embed(
                "Tmux sessions",
                fields = fields
            )
        )

    async def start(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        
        # Check for args
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a session or window to start."
                )
            )
            return

        sessions = await self.extract_session(
            message,
            resp,
            args[2].lower(),
            preferred_gdb
        )

        if sessions is None:
            return

        session_actions = []

        for session_name, targets in sessions.items():
            details = bot.config.sr_tmux[session_name]

            actions = []

            # Get the session
            try:
                session = bot.tmux.find_where({"session_name": session_name})

            except:
                session = None

            if session is None:
                # Create it
                session = bot.tmux.new_session(
                    session_name = session_name,
                    attach = False
                )
                actions.append(f"Created session `{session_name}`")

            # Check for each window
            windows = self.list_windows(session)
            window_actions = []

            for window_name in targets:
                if window_name not in details:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid window!",
                            f"Window `{window_name}` isn't defined for session `{session_name}`."
                        )
                    )
                    return
                
                if details[window_name].get("start") is None:
                    continue

                # Check if the window exists
                if window_name not in windows:
                    # Create it
                    window_actions.append(
                        {
                            "window_name": window_name,
                            "action": "create"
                        }
                    )

                window_actions.append( # TODO: Detect if the bot's already running and don't do this
                    {
                        "window_name": window_name,
                        "action": "cmd",
                        "cmd": details[window_name]["start"]
                    }
                )

            session_actions.append([session, windows, window_actions])

        for acts in session_actions:
            actions += await self.execute_window_actions(*acts)

        # Send back feedback
        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Started {len(targets)} window{'' if len(targets) == 1 else 's'}",
                description = "\n".join([f"• {x}" for x in actions]),
                color = "success"
            )
        )

    async def close(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):

        etype = args[1].lower()

        if etype == "kill":
            safe = {}
            detail = "Killed"

        else:
            safe = {"safe": True}
            detail = "Closed"
        
        # Check for args
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a session or window to close."
                )
            )
            return

        sessions = await self.extract_session(
            message,
            resp,
            args[2].lower(),
            preferred_gdb
        )

        if sessions is None:
            return

        session_actions = []

        for session_name, targets in sessions.items():
            details = bot.config.sr_tmux[session_name]

            actions = []

            # Get the session
            try:
                session = bot.tmux.find_where({"session_name": session_name})

            except:
                session = None

            if session is None:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Can't close!",
                        f"Session `{session_name}` isn't online."
                    )
                )
                return

            # Check for each window
            windows = self.list_windows(session)
            window_actions = []

            for window_name in targets:
                if window_name not in details:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid window!",
                            f"Window `{window_name}` isn't defined for session `{session_name}`."
                        )
                    )
                    return

                if details[window_name].get("start") is None:
                    actions.append(f"Skipped `{window_name}` (disabled)")
                    continue

                # Check if the window exists
                if window_name not in windows:
                    # Create it
                    actions.append(f"Skipped `{window_name}` (not online)")

                else:
                    window_actions.append(
                        {
                            "window_name": window_name,
                            "action": "close",
                            **safe
                        }
                    )
        
            session_actions.append([session, windows, window_actions])

        for acts in session_actions:
            actions += await self.execute_window_actions(*acts)

        # Send back feedback
        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  {detail} {len(targets)} window{'' if len(targets) == 1 else 's'}",
                description = "\n".join([f"• {x}" for x in actions]),
                color = "success"
            )
        )

    async def restart(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        # Check for args
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a session or window to restart."
                )
            )
            return

        sessions = await self.extract_session(
            message,
            resp,
            args[2].lower(),
            preferred_gdb
        )

        if sessions is None:
            return

        session_actions = []

        for session_name, targets in sessions.items():
            details = bot.config.sr_tmux[session_name]

            actions = []

            # Get the session
            try:
                session = bot.tmux.find_where({"session_name": session_name})

            except:
                session = None

            if session is None:
                # Create it
                session = bot.tmux.new_session(
                    session_name = session_name,
                    attach = False
                )
                actions.append(f"Created session `{session_name}`")

            # Check for each window
            windows = self.list_windows(session)
            window_actions = []

            for window_name in targets:
                if window_name not in details:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid window!",
                            f"Window `{window_name}` isn't defined for session `{session_name}`."
                        )
                    )
                    return

                if details[window_name].get("start") is None:
                    actions.append(f"Skipped `{window_name}` (disabled)")
                    continue

                # Check if the window exists
                if window_name in windows:
                    # Need to shut it down
                    window_actions.append(
                        {
                            "window_name": window_name,
                            "action": "close",
                            "safe": True
                        }
                    )

                # Append create calls

                window_actions.append(
                    {
                        "window_name": window_name,
                        "action": "create"
                    }
                )

                window_actions.append( # TODO: Detect if the bot's already running and don't do this
                    {
                        "window_name": window_name,
                        "action": "cmd",
                        "cmd": details[window_name]["start"]
                    }
                )
        
            session_actions.append([session, windows, window_actions])

        for acts in session_actions:
            actions += await self.execute_window_actions(*acts)

        # Send back feedback
        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Restarted {len(targets)} window{'' if len(targets) == 1 else 's'}",
                description = "\n".join([f"• {x}" for x in actions]),
                color = "success"
            )
        )

    async def show(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        
        # Check for args
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a window to display."
                )
            )
            return

        sessions = await self.extract_session(
            message,
            resp,
            args[2].lower(),
            preferred_gdb
        )

        if sessions is None:
            return

        session_actions = []

        session_name = list(sessions)[0]

        targets = sessions[session_name]

        if len(targets) != 1 or len(sessions) > 1:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "I can only display one window at a time."
                )
            )
            return

        target = targets[0]
        
        # Find the window
        details = bot.config.sr_tmux[session_name]

        actions = []

        # Get the session
        try:
            session = bot.tmux.find_where({"session_name": session_name})

        except:
            session = None

        if session is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't display window!",
                    f"Window `{target}`'s session, `{session_name}`, is offline."
                )
            )
            return

        session.switch_client()

        # Check for each window
        windows = self.list_windows(session)
        window_actions = []

        if target not in windows:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid window!",
                    f"Window `{target}` isn't online."
                )
            )
            return

        # Get pane
        window = windows[target]
        pane = window.select_pane("0")

        # Create a dummy pane if it doesn't exist
        panes = window.list_panes()
        base_list = len(panes)
        created = []
        count = len(panes)

        while count < 3:
            created.append(
                window.split_window(
                    vertical = True if len(created) == 0 else False,
                    attach = False
                )
            )
            count += 1

        #old_opt = window.show_window_options("window-size")
        window.set_window_option("window-size", "latest")
        window.set_window_option("aggressive-resize", "off")
        size = pane.display_message('#{pane_width}x#{pane_height}', get_text = True)[0]

        width, height = size.split("x", 1)

        width, height = int(width), int(height)

        # Resize to discord friendly sizes
        pane.set_width(56)
        pane.set_height(70)

        pane.send_keys(
            "\x1b[A",
            enter = False,
            suppress_history = False
        )

        # Wait a bit
        await asyncio.sleep(0.5)

        size = pane.display_message('#{pane_width}x#{pane_height}', get_text = True)[0]

        err = False
        try:
            content = "\n".join(pane.capture_pane()).strip()

        except Exception as e:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Couldn't capture pane!",
                    f"Pane capture failed: `{str(e)}`"
                )
            )
            await debug.log_traceback()
            err = True

        pane.set_width(width)
        pane.set_height(height)

        # Delete old panes
        for pane in created:
            pane.send_keys(
                "\x04",
                suppress_history = False,
                enter = True
            )

        #window.set_window_option("window-size", old_opt)

        if err:
            return

        # Send back feedback
        await resp.send(
            embed = discordutils.create_embed(
                f"[{session_name}] {dict(window.items())['window_id']}:{target} $0",
                description = f"```{content}```"
            )
        )

    async def send(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        
        # Check for args
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a session or window to send to, plus a command to send."
                )
            )
            return

        command = " ".join(args[3:])

        sessions = await self.extract_session(
            message,
            resp,
            args[2].lower(),
            preferred_gdb
        )

        if sessions is None:
            return

        session_actions = []

        for session_name, targets in sessions.items():
            details = bot.config.sr_tmux[session_name]

            actions = []

            # Get the session
            try:
                session = bot.tmux.find_where({"session_name": session_name})

            except:
                session = None

            if session is None:
                # Create it
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Can't send command!",
                        f"Session `{session_name}` is offline."
                    )
                )
                return

            # Check for each window
            windows = self.list_windows(session)
            window_actions = []

            for window_name in targets:
                if window_name not in details:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid window!",
                            f"Window `{window_name}` isn't defined for session `{session_name}`."
                        )
                    )
                    return

                # Check if the window exists
                if window_name not in windows:
                    actions.append(f"Skipped window `{window_name}` (offline)")

                else:
                    window_actions.append(
                        {
                            "window_name": window_name,
                            "action": "cmd",
                            "cmd": command
                        }
                    )
        
            session_actions.append([session, windows, window_actions])

        for acts in session_actions:
            actions += await self.execute_window_actions(*acts)

        # Send back feedback
        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Ran command on {len(targets)} window{'' if len(targets) == 1 else 's'}",
                description = f"**Command:** `{command}`\n" + "\n".join([f"• {x}" for x in actions]),
                color = "success"
            )
        )

    async def verify_server(
            self
        ):

        bot.tmux = libtmux.Server()

    def list_windows(
            self,
            session
        ):

        windows = {}

        for window in session.list_windows():
            details = dict(window.items())

            windows[details["window_name"]] = window

            window.name = details["window_name"]

        return windows

    async def get_session(
            self,
            targets_: list
        ):
        sessions = {}

        for target in targets_:
            session_name = None
            targets = None
            # Find the target.
            if target in bot.config.sr_tmux:
                session_name = target
                targets = list(bot.config.sr_tmux[session_name])

            else:
                # Try to see if it's a window instead
                for name, windows in bot.config.sr_tmux.items():
                    for window, details in windows.items():
                        if (
                            target == window
                            or target in (details["aliases"] if "aliases" in details else [])
                        ):
                            session_name = name
                            targets = [window]
                            break

            if session_name is None:
                return target

            if session_name not in sessions:
                sessions[session_name] = []

            sessions[session_name] += targets

        return sessions

    async def extract_session(
            self,
            message,
            resp,
            target_list,
            preferred_gdb
        ):
        await self.verify_server()

        sessions = {}

        for target in target_list.split(","):
            # First, check if it's a category
            if target in bot.config.sr_categories:
                targets_ = bot.config.sr_categories[target]

            else:
                targets_ = [target]

            session_results = await self.get_session(
                targets_
            )

            if type(session_results) == str:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid target!",
                        f"No session, window, or category was found by name `{session_results}`. To list all options, run `{preferred_gdb['prefix']}tmux`."
                    )
                )
                return

            for session_name, targets in session_results.items():
                if session_name not in sessions:
                    sessions[session_name] = []

                for target_ in targets:
                    if target_ not in sessions[session_name]:
                        sessions[session_name].append(target_)

        return sessions

    async def execute_window_actions(
            self,
            session,
            windows: dict,
            actions: list
        ):

        ret = []

        for action in actions:
            if action["action"] == "create":
                window = session.new_window(
                    window_name = action["window_name"],
                    attach = False
                )

                windows[action["window_name"]] = window

                ret.append(f"Created window `{action['window_name']}`")

            elif action["action"] == "cmd":
                name = action["window_name"]
                if name in windows:
                    window = windows[name]
                    pane = window.select_pane("0")

                    pane.send_keys(
                        action["cmd"],
                        suppress_history = False,
                        enter = True
                    )

                    ret.append(f"Sent command `{action['cmd']}` to window `{name}`")

                else:
                    ret.append(f"Failed to run command on window `{name}`")

            elif action["action"] == "close":
                name = action["window_name"]
                
                if name in windows:
                    window = windows[name]

                    ext = ""
                    if "safe" in action:
                        if action["safe"] == True:
                            pane = window.select_pane("0")

                            pane.send_keys(
                                "\x04",
                                suppress_history = False,
                                enter = True
                            )

                            await asyncio.sleep(1.5)
                            ext = " (safe)"

                    window.kill_window()

                    ret.append(f"Closed window `{name}`{ext}")

                else:
                    ret.append(f"Failed to close window `{name}`")

        return ret