import asyncio
from run_outreach import ColdMailerCLI
from core.database import init_db

async def start():
    await init_db()
    cli = ColdMailerCLI()
    await cli.run()

if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("\nExiting ColdMailer...")
