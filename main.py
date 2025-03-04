import asyncio
from contextlib import suppress
import sys

from core.common_utils import register_sessions, check_sessions, check_proxies

async def main():
    args = sys.argv
    if len(args) < 2:
        print("Please provide arguments.")
        sys.exit()

    action = args[1]
    if action == "register":
        await register_sessions()
    elif action == "check_sessions":
        await check_sessions()
    elif action == "check_proxies":
        await check_proxies()
    else:
        print(f"Action {action} is not supported.")

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
