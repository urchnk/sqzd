from dataclasses import dataclass

from environs import Env

env = Env()
env.read_env()


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    misc: Miscellaneous


def load_config():

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=[int(item) for item in env.list("ADMINS")],
            use_redis=env.bool("USE_REDIS", False),
        ),
        misc=Miscellaneous(),
    )
