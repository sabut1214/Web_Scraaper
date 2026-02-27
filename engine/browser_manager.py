import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright
from config import get_settings
from core.logger import setup_logger

logger = setup_logger("browser_manager")


class BrowserManager:
    def __init__(self):
        self.settings = get_settings()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def initialize(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            
            browser_type = getattr(
                self._playwright,
                self.settings.playwright_browser_type
            )
            
            self._browser = await browser_type.launch(
                headless=self.settings.playwright_headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ]
            )
            
            self._semaphore = asyncio.Semaphore(
                self.settings.worker_browser_instances
            )
            
            logger.info(f"Browser pool initialized with {self.settings.worker_browser_instances} instances")

    async def acquire_context(self, context_options: Dict[str, Any] = None) -> BrowserContext:
        if self._semaphore:
            await self._semaphore.acquire()
        
        context_options = context_options or {}
        
        context = await self._browser.new_context(**context_options)
        
        from engine.stealth.middleware import stealth_middleware
        await stealth_middleware.apply_stealth(context)
        
        return context

    async def release_context(self, context: BrowserContext):
        try:
            await context.close()
        except Exception as e:
            logger.warning(f"Error closing context: {e}")
        finally:
            if self._semaphore:
                self._semaphore.release()

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("Browser pool closed")


browser_manager = BrowserManager()
