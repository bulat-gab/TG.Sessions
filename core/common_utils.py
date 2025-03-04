import glob
import json
import os
import sys
from typing import Optional, Union
import aiohttp
import asyncio

from pyrogram import Client
from pyrogram import errors
from better_proxy import Proxy

from .logger import logger
from .config import settings


async def check_proxies() -> None:
    with open(settings.PROXY_FILE, 'r') as f:
        proxies: dict = json.load(f)

    invalid_proxies = []
    for name, proxy_str in proxies.items():
        result = await _validate_proxy_async(proxy_str)
        if not result:
            invalid_proxies.append(name)
    
    logger.success(f"check_proxies finished | Invalid proxies count: {len(invalid_proxies)}")
    logger.info(f"Invalid proxies: {','.join(invalid_proxies)}")
    

async def check_sessions() -> None:
    logger.info(f"Start checking sessions in '{settings.SESSIONS_PATH}' directory")
    
    if not os.path.exists(settings.SESSIONS_PATH):
        logger.error(f"Directory does not exist: '{settings.SESSIONS_PATH}'")
        sys.exit(1)
    
    with open(settings.PROXY_FILE, 'r') as f:
        proxies: dict = json.load(f)

    sessions = get_session_names()
    logger.info(f"Found '{len(sessions)}' sessions in '{settings.SESSIONS_PATH}'")

    valid_sessions = []
    for session in sessions:
        proxy_string = proxies.get(session)
        if not await _validate_proxy_async(proxy_string):
            continue

        proxy_dict = parse_proxy_string_into_dict(proxy_string)
        if not proxy_dict:
            logger.warning(f"Could not parse or get proxy for '{session}'. Skippping it.")
            continue

        result = await _validate_session(proxy_dict, session)
        if result:
            valid_sessions.append(session)

    
    logger.info(f"Valid sessions: {len(valid_sessions)}. All sessions: {len(sessions)}.")


async def _validate_session(proxy_dict: dict, session_name: str) -> bool:
    client = Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir=settings.SESSIONS_PATH,
        proxy=proxy_dict
    )

    try:
        async with client: 
            await client.get_me()
            logger.success(f"Session '{session_name}' is valid.")
            return True
    except (
            errors.ActiveUserRequired,
            errors.AuthKeyInvalid,
            errors.AuthKeyPermEmpty,
            errors.AuthKeyUnregistered,
            errors.AuthKeyDuplicated,
            errors.SessionExpired,
            errors.SessionPasswordNeeded,
            errors.SessionRevoked,
            errors.UserDeactivated,
            errors.UserDeactivatedBan,
            ) as e:
        logger.error(f"Session '{session_name}' is invalid. {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error for session '{session_name}' with proxy {proxy_dict.get('host', 'No Proxy')}: {e}")
        return False


async def register_sessions() -> None:
    API_ID = settings.API_ID
    API_HASH = settings.API_HASH

    if not API_ID or not API_HASH:
        raise ValueError("Missing API_ID or API_HASH")

    session_name = input("Enter session name:")
    ensure_session_name_unique(session_name)

    proxy = input("Enter proxy ('PROTOCOL://USERNAME:PASSWORD@IP:PORT'): ")
    proxy_dict = parse_proxy_string_into_dict(proxy)


    session = Client(
        name=session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=settings.SESSIONS_PATH,
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

def parse_proxy_string_into_dict(proxy_str: str) -> dict[str, Union[str, int]]:
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
    sessions_path_pattern = os.path.join(settings.SESSIONS_PATH, "*.session")
    session_names = glob.glob(sessions_path_pattern)
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names

async def _validate_proxy_async(proxy_str: str) -> bool:
    proxy_dict = parse_proxy_string_into_dict(proxy_str)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.ipify.org?format=json', proxy=proxy_str) as response:
                data = await response.json()
                if not data:
                    logger.error(f"Invalid proxy: Could not access api.ipify.org to check proxy")
                    return False
                
                actual_ip = data.get('ip')
                if actual_ip != proxy_dict["hostname"]:
                    logger.error(f"Invalid proxy: IPs mismatch")
                    return False

                return True
    except Exception as e:
        logger.error(f"Invalid proxy: Proxy '{proxy_str}' is not working. {e}")
        return False

    