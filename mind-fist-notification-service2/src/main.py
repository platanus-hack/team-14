import asyncio

from dotenv import load_dotenv

from notification_stream import stream

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(stream())
