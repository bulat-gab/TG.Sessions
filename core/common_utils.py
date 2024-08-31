import glob
import os
import sys
from typing import Optional, Union

from .config import settings
from . import logger
from pyrogram import Client
from better_proxy import Proxy
from .logger import logger

async def register_sessions() -> None:
    API_ID = settings.API_ID
    API_HASH = settings.API_HASH

    if not API_ID or not API_HASH:
        raise ValueError("Missing API_ID or API_HASH")

    session_name = input("Enter session name:")
    ensure_session_name_unique(session_name)

    proxy = input("Enter proxy ('PROTOCOL://USERNAME:PASSWORD@IP:PORT'): ")
    proxy_dict = get_proxy_dict(proxy)


    session = Client(
        name=session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="sessions/",
        proxy=proxy_dict
    )

    async with session:
        user_data = await session.get_me()

    logger.success(f"Session addded: {user_data.username} {user_data.first_name} {user_data.last_name}")

def ensure_session_name_unique(session_name: Optional[str]):
    if not session_name:
        return None
    
    existing_sessions = get_session_names()
    if session_name in existing_sessions:
        logger.error(f"Session {session_name} already exists.")
        sys.exit()

def get_proxy_dict(proxy_str: str) -> dict[str, Union[str, int]]:
    proxy = Proxy.from_str(proxy_str)
    if not proxy:
        logger.error(f"Could not parse proxy: {proxy_str}")

    proxy_dict = dict(
        scheme=proxy.protocol,
        hostname=proxy.host,
        port=proxy.port,
        username=proxy.login,
        password=proxy.password
    )

    return proxy_dict

def get_session_names() -> list[str]:
    session_names = glob.glob("sessions/*.session")
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names