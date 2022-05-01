import socket

import disnake
from disnake.ext import commands, tasks

from ui.menu import MenuBase
from utils import checks


class SharpTV:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = None
        self.connected = False

    def connect(self):
        if self.socket is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.connected:
            return
        self.socket.connect((self.ip, self.port))
        self.connected = True
        print("Connected to TV")
        return "Connected to TV"

    def close(self):
        if not self.connected:
            return
        self.socket.close()
        self.socket = None
        self.connected = False
        print("Disconnected from TV")
        return "Disconnected from TV"

    def power(self, toggle: int = None):
        POWERSTATE = {"1": "On", "0": "Off"}
        out = []

        if toggle is not None:
            self.socket.send(f"POWR{toggle}   \r".encode())
            data = self.socket.recv(8).decode().strip()
            print(f"- Sent Power State: {POWERSTATE[str(toggle)]}")
            out.append(f"- Sent Power State: {POWERSTATE[str(toggle)]}")
            if data != "OK":
                print(f"Error: {data}")
                out.append(f"Error: {data}")
                return data, out

        self.socket.send(b"POWR?   \r")
        data = self.socket.recv(8).decode().strip()
        print(f"""Power Status: {POWERSTATE.get(data, "ERROR")}""")
        out.append(f"""Power Status: {POWERSTATE.get(data, "ERROR")}""")
        return data, out

    def input(self, change: int = None):
        out = []
        if change is not None:
            self.socket.send(f"IAVD{change}   \r".encode())
            data = self.socket.recv(8).decode().strip()
            print(f"- Sent Input: {change}")
            out.append(f"- Sent Input: {change}")
            if data != "OK":
                print(f"Error: {data}")
                out.append(f"Error: {data}")
                return

        self.socket.send(b"IAVD?   \r")
        data = self.socket.recv(8).decode().strip()
        print(f"""Input Status: {data}""")
        out.append(f"""Input Status: {data}""")
        return data, out

    def volume(self, change: int = None):
        out = []
        if change is not None:
            self.socket.send(f"VOLM{change:04d}\r".encode())
            data = self.socket.recv(8).decode().strip()
            print(f"- Sent Volume: {change}")
            out.append(f"- Sent Volume: {change}")
            if data != "OK":
                print(f"Error: {data}")
                out.append(f"Error: {data}")
                return

        self.socket.send(b"VOLM?   \r")
        data = self.socket.recv(8).decode().strip()
        print(f"""Volume Level: {data}""")
        out.append(f"""Volume Level: {data}""")
        return data, out

    def setup_kids(self):
        """Turns on the TV, ensures the input is on the Chromecast, and sets the volume to 33"""
        out = []
        cur_power, msg = self.power()
        out.extend(msg)
        if cur_power != "1":
            self.power(1)
        cur_input, msg = self.input()
        out.extend(msg)
        if cur_input != "3":  # Chromecast
            self.input(3)
        cur_vol, msg = self.volume()
        out.extend(msg)
        if cur_vol != "33":
            self.volume(33)
        return out


class TV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tv = SharpTV("10.0.0.4", 10002)

    @commands.command(hidden=True)
    @checks.is_owner()
    async def connect(self, ctx: commands.Context):
        """Connects to the TV"""
        if self.tv.connected:
            await ctx.send(f"```\nTV already connected\n```")
            return
        self.tv.connect()
        await ctx.send(f"```\nConnected to TV\n```")

    @commands.command(aliases=["disconnect"], hidden=True)
    @checks.is_owner()
    async def close(self, ctx: commands.Context):
        """Closes the connection to the TV"""
        if not self.tv.connected:
            await ctx.send(f"```\nTV already disconnected\n```")
            return
        self.tv.close()
        await ctx.send(f"```\nDisconnected from TV\n```")

    @commands.command(hidden=True)
    @checks.is_owner()
    async def power(self, ctx: commands.Context, change: int = None):
        """Checks the power status for the TV, or turns it on (1) or off (0)"""
        if self.tv.connected:
            await ctx.send("```\n" + '\n'.join(self.tv.power(change)[1]) + "\n```")

    @commands.command(hidden=True)
    @checks.is_owner()
    async def volume(self, ctx: commands.Context, change: int = None):
        """Checks the volume status for the TV, or sets it (0-100)."""
        if self.tv.connected:
            await ctx.send("```\n" + '\n'.join(self.tv.volume(change)[1]) + "\n```")

    @commands.command(hidden=True)
    @checks.is_owner()
    async def input(self, ctx: commands.Context, change: int = None):
        """Checks the input on the TV, or changes it. 3 is Chromecast"""
        if self.tv.connected:
            await ctx.send("```\n" + '\n'.join(self.tv.input(change)[1]) + "\n```")

    @commands.command(hidden=True)
    @checks.is_owner()
    async def setup_for_kids(self, ctx: commands.Context):
        """Powers On da tv, sets input to Chromecast, and volume to 33"""
        if not self.tv.connected:
            self.tv.connect()
        await ctx.send("```\n" + '\n'.join(self.tv.setup_kids()) + "\n```")

    @commands.command(hidden=True)
    async def tv(self, ctx):
        tv_ui = TVView.new(ctx.message.author)
        await tv_ui.send_to(ctx)


_VOLUME_OPTIONS = [
    disnake.SelectOption(label=f"{vol}", value=f"{vol}")
    for vol in range(0, 101, 5)
]


class TVView(MenuBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 30
        self.tv = SharpTV("10.0.0.4", 10002)
        self.tv.connect()
        self.power = self.tv.power()
        self.volume = self.tv.volume()
        self.input = self.tv.input()

    @classmethod
    def new(cls, owner: disnake.User):
        inst = cls(owner=owner)
        return inst

    async def on_timeout(self):
        self.tv.close()
        await self.message.edit(view=None)

    @disnake.ui.button(label="Toggle Power", style=disnake.ButtonStyle.primary)
    async def power_toggle(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.power = self.tv.power(0 if int(self.power[0]) else 1)
        if self.power[0] == "1":
            button.style = disnake.ButtonStyle.danger
        else:
            button.style = disnake.ButtonStyle.primary
        await self.refresh_content(interaction)

    @disnake.ui.button(label="Set to Chromecast", style=disnake.ButtonStyle.primary)
    async def chromecast(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.input = self.tv.input(3)
        await self.refresh_content(interaction)

    @disnake.ui.select(placeholder="Volume", options=_VOLUME_OPTIONS)
    async def volume_select(self, select: disnake.ui.Select, interaction: disnake.Interaction):
        value = int(select.values[0])
        self.volume = self.tv.volume(value)
        await self.refresh_content(interaction)

    @disnake.ui.button(label="Disconnect", style=disnake.ButtonStyle.danger, row=4)
    async def disconnect(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.tv.close()
        await self.message.edit(view=None)


    async def _before_send(self):
        self.power_toggle.style = disnake.ButtonStyle.danger if self.power[0] == "1" else disnake.ButtonStyle.primary

    async def get_content(self):
        embed = disnake.Embed(
            title=f"TV Controls",
            colour=disnake.Colour.blurple(),
        )
        embed.add_field(name="Power State",
                        value=self.power[1][-1])
        embed.add_field(name="Volume",
                        value=self.volume[1][-1] if self.volume else "Unknown")
        embed.add_field(name="Input (3 is Chromecast)",
                        value=self.input[1][-1] if self.input else "Unknown")

        return {"embed": embed}


def setup(bot):
    bot.add_cog(TV(bot))
