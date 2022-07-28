import re
from random import choice, choices

from disnake.ext import tasks, commands
from datetime import datetime
from dateparser import parse as timeparse
from pytz import timezone

from utils import checks

weather = [
    {"emoji": "☀", "desc": "Clear", "temp_min": 20, "temp_max": 30, "weight": 30},
    {"emoji": "⛅", "desc": "Overcast", "temp_min": 15, "temp_max": 23, "weight": 15},
    {"emoji": "⛈", "desc": "Storms", "temp_min": -5, "temp_max": 12, "weight": 10},
    {"emoji": "☁", "desc": "Foggy", "temp_min": 9, "temp_max": 16, "weight": 10},
    {"emoji": "🌧", "desc": "Rain", "temp_min": 3, "temp_max": 15, "weight": 10},
    {"emoji": "🌨", "desc": "Snow", "temp_min": -20, "temp_max": -5, "weight": 10},
    {"emoji": "💨", "desc": "High Winds", "temp_min": 18, "temp_max": 24, "weight": 5},
    {"emoji": "🧊", "desc": "Blizzard", "temp_min": -40, "temp_max": -15, "weight": 2},
    {"emoji": "🔥", "desc": "Heatwave", "temp_min": 30, "temp_max": 45, "weight": 2},
    {"emoji": "⏳", "desc": "Sandstorm", "temp_min": 25, "temp_max": 30, "weight": 2},
]


def get_weather(weather_type=None):
    w_emoji, w_type, t_min, t_max, _ = next(
        (w for w in weather if weather_type and weather_type.lower() in w["desc"].lower()),
        choices(weather, weights=[w["weight"] for w in weather]),
    )[0].values()
    return f"{w_emoji} {w_type}🌡 {choice(list(range(t_min, t_max)))}°C"


def get_time():
    tz = timezone("US/Eastern")
    now = datetime.now(tz)
    current_time = now.strftime("%I:00 %p").strip("0")
    return current_time


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

    @tasks.loop(hours=6)
    async def set_server_weather(self, weather_type=None):
        channel = self.bot.get_channel(958400248517132349)
        update_thread = self.bot.get_channel(990459956379648040)
        # So we don't rate limit ourselves on reboots
        if not self.get_weather:
            self.get_weather = True
            return
        new_weather = get_weather(weather_type)
        await channel.edit(name=new_weather)
        await update_thread.send(new_weather)
        return new_weather

    @set_server_weather.before_loop
    async def before_set_server_weather(self):
        await self.bot.wait_until_ready()

    @commands.command(
        help=f"""Weather type from the following: 
        {", ".join([f"`{i['desc'].lower()}`" for i in weather])}
        
        Not selecting a type, or selecting an invalid type, will cause it to roll randomly

        Resets the 6 hour timer."""
    )
    @checks.is_owner()
    async def update_weather(self, ctx, weather_type=None):
        async with ctx.typing():
            new_weather = await self.set_server_weather(weather_type)
        await ctx.send(f"Weather updated - {new_weather}")
        self.get_weather = False
        self.set_server_weather.restart()

    @commands.command()
    async def convert(self, ctx):
        """Converts the current weather into celsius for the silly Americans"""
        channel = self.bot.get_channel(958400248517132349)
        current_weather = channel.name

        regex = r".+🌡 (.+)°C"
        celsius = re.match(regex, current_weather).group(1)
        fahrenheit = int((int(celsius) * (9 / 5)) + 32)
        await ctx.send(f"Current Weather: {current_weather.replace(celsius, str(fahrenheit))[:-1]}F")

    @commands.command(aliases=["timer", "timestamp"])
    async def time(self, ctx: commands.Context, *, time: str):
        """Generates a Discord timestamp based on user input."""
        time = timeparse(time)
        if time:
            timestamp = int(time.timestamp())
            await ctx.send(f"""<t:{timestamp}> `<t:{timestamp}>`\n<t:{timestamp}:R> `<t:{timestamp}:R>`""")


def setup(bot):
    bot.add_cog(Locale(bot))
