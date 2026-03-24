import asyncio
from cli.dashboard import ColdMailerApp
from core.database import init_db

async def start():
    await init_db()
    app = ColdMailerApp()
    await app.main_menu()

if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("\nExiting ColdMailer...")
