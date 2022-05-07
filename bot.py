import logging
import tracemalloc
import asyncio
import nest_asyncio
import requests

from motor.motor_asyncio import AsyncIOMotorClient
from aiogram import Bot, Dispatcher, executor, types
from config import config


nest_asyncio.apply()
tracemalloc.start()


client = AsyncIOMotorClient(config["db"])
db = client["db"]
users = db["users"]
servers = db["servers"]


logging.basicConfig(level=logging.INFO)

bot = Bot(config["token"])
dp = Dispatcher(bot)
server_prefix = {}


def debug(obj: object): # Работает - не трогай
    if config["debug"] is True:
        print(obj)


async def get_alerts() -> dict:
    r = requests.get("https://api.alerts.in.ua/v2/alerts/active.json")
    alerts = r.json() # {'alerts': [{'u': 1649405066, 's': 1649090739, 'n': 'Луганська', 't': 'o'}], 'meta': {'last_updated_at': '2022/05/07 18:46:28 +0000', 'type': 'compact'}, 'contact': 'api@alerts.in.ua'}
    alerts_updated = alerts["meta"]["last_updated_at"].split()

    return {"alerts": [alert["n"] for alert in alerts["alerts"]], "updated_at": f"{alerts_updated[0]} {alerts_updated[1]}"}


async def load_server_prefix(*args): # Работает - не трогай
    documents = await servers.find().to_list(length=100)

    try:
        for document in documents:
            server_prefix.update({document["id"]: document["prefix"]})
    except Exception as e:
        debug(e)


class Command:
    def __init__(self, msg: types.Message, command: str, permissions: str = "all"):
        self.msg = msg
        self.id = self.msg.chat.id
        self.command = command
        self.permissions = permissions


    def __bool__(self):
        prefix = server_prefix[self.id] if id in server_prefix.keys() else config["prefix"]
        check = self.msg.text.lower()[:len(self.command) + len(prefix)] == prefix + self.command

        match self.permissions:
            case "all":
                return check
            case "admin":
                return check and self.msg.from_user.id in [id.user.id for id in self.get_admins()]
            case "dev":
                return check and self.msg.from_user.id == config["dev"]

    
    def get_admins(self) -> "list":
        loop = asyncio.get_event_loop()
        admins = [i.user.id for i in (loop.run_until_complete(asyncio.gather(self._get_admins()))[0])]
        return admins

    
    async def _get_admins(self):
        return await self.msg.chat.get_administrators()


@dp.message_handler(commands=["alerts"])
async def alerts(message: types.Message):
    try:
        alerts = await get_alerts()
        places = '/n'.join([alert + ' обл.' if alert.endswith('а') else '' for alert in alerts['alerts']])
        updated_at = alerts['updated_at']
        await message.answer(f"*Список місць з повітряною тревогою*:\n\n{places}\n\nДані станом на: `{updated_at}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"*Помилка!*\n```{e}```\n[FOUREX](tg://user?id={config['dev']})", parse_mode="Markdown")


@dp.message_handler(commands=["help"])
async def help(message: types.Message):
    await message.answer(f"[Розробник](tg://user?id={config['dev']})|[GitHub](https://github.com/FOUREX/Kabanos)", parse_mode="Markdown")


@dp.message_handler(commands=["help_admin"])
async def help_admin(message: types.Message):
    await message.answer("Недоступно")


@dp.message_handler(commands=["set_prefix"])
async def set_prefix(message: types.Message):
    await message.answer("Недоступно")
    """id = message.chat.id
    if message.from_user.id in [id.user.id for id in (await message.chat.get_administrators())] or message.from_user.id == config["dev"]:
        prefix = message.text.split()[1]

        if await servers.find_one({"id": id}) is None:
            await servers.insert_one({"id": id, "prefix": prefix})
        else:
            await servers.update_one({"id": id}, {"$set": {"prefix": prefix}})

        await load_server_prefix()
    else:
        await message.reply("Ця команда доступна лише адміністаторам чату!")"""


@dp.message_handler()
async def yep(message: types.Message):
    """id = message.chat.id
    if not message.chat.id in server_prefix.keys():
        if await servers.find_one({"id": id}) is None:
            await servers.insert_one({"id": id, "prefix": config["prefix"]})
        else:
            await servers.update_one({"id": id}, {"$set": {"prefix": config["prefix"]}})

        await load_server_prefix()"""


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=load_server_prefix)