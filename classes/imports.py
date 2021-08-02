import humecord

humecord.add_path("/home/camden/humecord/global")

class Imports:
    def __init__(self):
        # Commands
        self.loader = {
            "commands": {
                "control": [
                    {
                        "imp": "from commands import control",
                        "module": "control",
                        "class": "ControlCommand"
                    },
                    {
                        "imp": "from commands import tmux",
                        "module": "tmux",
                        "class": "TmuxCommand"
                    }
                ],
                "music": [
                    {
                        "imp": "from commands import music",
                        "module": "music",
                        "class": "MusicCommand"
                    }
                ]
            },
            "events": [
                {
                    "imp": "from events import on_message",
                    "module": "on_message",
                    "class": "OnMessageEvent"
                },
                {
                    "imp": "from events import ws",
                    "module": "ws",
                    "class": "HCOnWSResponse"
                }
            ],
            "loops": [
                {
                    "imp": "from loops import watch_music",
                    "module": "watch_music",
                    "class": "WatchMusicLoop"
                },
                {
                    "imp": "from loops import update_status",
                    "module": "update_status",
                    "class": "UpdateStatusLoop"
                },
                {
                    "imp": "from loops import update_stats",
                    "module": "update_stats",
                    "class": "UpdateStatsLoop"
                }
            ]
        }