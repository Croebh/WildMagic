from random import choice

from disnake.ext import tasks, commands
from datetime import datetime
from dateparser import parse as timeparse
from pytz import timezone

from utils import checks

weather = [
    # Emoji, Type, Min, Max
    ("☀️", "Clear", 20, 30),
    ("⛅", "Overcast", 15, 23),
    ("☁️", "Foggy", 9, 16),
    ("🌧️", "Rain", 3, 15),
    ("⛈️", "Storms", -5, 12),
    ("🌨️", "Snow", -25, -5),
]


def get_time():
    tz = timezone("US/Eastern")
    now = datetime.now(tz)
    current_time = now.strftime("%I:00 %p").strip("0")
    return current_time


def get_weather():
    w_emoji, w_type, t_min, t_max = choice(weather)
    return f"{w_emoji} {w_type}🌡 {choice(list(range(t_min, t_max)))}°C"


class Locale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.get_weather = False

        self.current_time = "Server Time: LOADING"
        self.set_server_time.start()

        self.current_weather = "Current Weather: LOADING"
        self.set_server_weather.start()

    def cog_unload(self):
        self.set_server_time.cancel()
        self.set_server_weather.cancel()

    @tasks.loop(minutes=20)
    async def set_server_time(self):
        channel = self.bot.get_channel(973112925793439744)
        time = get_time()
        if channel.name != time:
            await channel.edit(name=time)

    @set_server_time.before_loop
    async def before_set_server_time(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=12)
    async def set_server_weather(self):
        channel = self.bot.get_channel(958400248517132349)
        # So we don't rate limit ourselves on reboots
        if not self.get_weather:
            self.get_weather = True
            return
        new_weather = get_weather()
        await channel.edit(name=new_weather)
        return new_weather

    @set_server_weather.before_loop
    async def before_set_server_weather(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @checks.is_owner()
    async def update_weather(self, ctx):
        async with ctx.typing():
            new_weather = await self.set_server_weather()
        await ctx.send(f"Weather updated - {new_weather}")

    @commands.command(aliases=["timer", "timestamp"])
    async def time(self, ctx: commands.Context, *, time: str):
        """Generates a Discord timestamp based on user input."""
        time = timeparse(time)
        if time:
            timestamp = int(time.timestamp())
            await ctx.send(f"""<t:{timestamp}> `<t:{timestamp}>`\n<t:{timestamp}:R> `<t:{timestamp}:R>`""")


def setup(bot):
    bot.add_cog(Locale(bot))
