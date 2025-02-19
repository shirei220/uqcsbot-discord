import logging
import os
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from aiohttp import web

class UQCSBot(commands.Bot):
    """ An extended bot client to add extra functionality. """

    # Checks for an Azure specific environment variable, if it exists we're running as prod.
    SERVER_ID = 813324385179271168 if os.environ.get("WEBSITE_SITE_NAME") != None else 836589565237264415

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scheduler = AsyncIOScheduler()
        self.start_time = datetime.now()

    def schedule_task(self, func, *args, **kwargs):
        """ Schedule a function to be run at a later time. A wrapper for apscheduler add_job. """
        self._scheduler.add_job(func, *args, **kwargs)

    def set_db_engine(self, db_engine: Engine):
        """ Creates a sessionmaker from the provided database engine which can be called from commands. """
        self.create_db_session = sessionmaker(bind=db_engine)

    async def setup_hook(self):
        await self.web_server()

    # Web server binds to port 8080. This is a basic template to ensure
    # that Azure has something for a health check.
    async def web_server(self):
        def handle(request):
            return web.Response(text="UQCSbot is running")

        app = web.Application()
        app.router.add_get('/', handle)
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, '0.0.0.0', 8080)
        await self.site.start()

    async def on_ready(self):
        """ Once the bot is loaded and has connected, run these commands first. """
        self._scheduler.start()
        logging.info(f"Bot online and logged in: [Name=\"{self.user.name}\", ID={self.user.id}]")
        
        # Get the UQCS server object and store it centrally
        self.uqcs_server = self.get_guild(self.SERVER_ID)

        # Sync the app comamand tree with servers.
        await self.tree.sync()
        logging.info(f"Synced app command tree with guilds.")
