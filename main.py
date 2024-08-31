import asyncio
from contextlib import suppress

from core.common_utils import register_sessions

async def main():
    await register_sessions()


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
