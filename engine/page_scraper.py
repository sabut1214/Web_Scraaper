import asyncio
import time
from typing import Optional, Dict, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from config import get_settings
from engine.browser_manager import browser_manager
from engine.stealth.middleware import stealth_middleware
from core.logger import setup_logger

logger = setup_logger("page_scraper")


class ScrapeResult:
    def __init__(
        self,
        url: str,
        success: bool,
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ):
        self.url = url
        self.success = success
        self.html = html
        self.markdown = markdown
        self.data = data
        self.error = error
        self.duration_ms = duration_ms


class PageScraper:
    def __init__(self):
        self.settings = get_settings()

    async def scrape(
        self,
        url: str,
        mode: str = "full",
        wait_for: Optional[str] = None,
        timeout: Optional[int] = None,
        proxy: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        extraction_schema: Optional[Dict[str, Any]] = None,
        extraction_prompt: Optional[str] = None,
    ) -> ScrapeResult:
        start_time = time.time()
        
        context_options = stealth_middleware.get_context_options(proxy=proxy)
        
        if headers:
            context_options["extra_http_headers"] = headers
        
        context = await browser_manager.acquire_context(context_options)
        
        try:
            page = await context.new_page()
            
            timeout_ms = timeout or self.settings.playwright_timeout
            
            response = await page.goto(
                url,
                timeout=timeout_ms,
                wait_until="domcontentloaded",
            )
            
            if response and response.status >= 400:
                return ScrapeResult(
                    url=url,
                    success=False,
                    error=f"HTTP {response.status}",
                    duration_ms=int((time.time() - start_time) * 1000),
                )
            
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=timeout_ms)
                except PlaywrightTimeoutError:
                    logger.warning(f"Wait for selector '{wait_for}' timed out")
            
            await asyncio.sleep(1)
            
            html = await page.content()
            
            markdown = await self._extract_markdown(page)
            
            result = ScrapeResult(
                url=url,
                success=True,
                html=html,
                markdown=markdown,
                duration_ms=int((time.time() - start_time) * 1000),
            )
            
            if mode in ("extraction", "full") and extraction_schema:
                from extraction.extractor import extract_structured_data
                try:
                    data = await extract_structured_data(
                        html=html,
                        schema=extraction_schema,
                        prompt=extraction_prompt,
                    )
                    result.data = data
                except Exception as e:
                    logger.error(f"Extraction failed: {e}")
                    result.error = str(e)
            
            return result
            
        except PlaywrightTimeoutError:
            return ScrapeResult(
                url=url,
                success=False,
                error="Page load timeout",
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return ScrapeResult(
                url=url,
                success=False,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )
        finally:
            await browser_manager.release_context(context)

    async def _extract_markdown(self, page: Page) -> str:
        try:
            content = await page.evaluate("""
                () => {
                    const getText = (el) => {
                        if (el.nodeType === Node.TEXT_NODE) {
                            return el.textContent.trim();
                        }
                        if (el.nodeType !== Node.ELEMENT_NODE) {
                            return '';
                        }
                        const tag = el.tagName.toLowerCase();
                        if (['script', 'style', 'nav', 'footer', 'header'].includes(tag)) {
                            return '';
                        }
                        if (tag === 'a') {
                            const href = el.getAttribute('href');
                            const text = el.textContent.trim();
                            return text ? `[${text}](${href || ''})` : '';
                        }
                        if (['h1','h2','h3','h4','h5','h6'].includes(tag)) {
                            const level = tag.charAt(1);
                            const text = el.textContent.trim();
                            return text ? '\\n' + '#'.repeat(parseInt(level)) + ' ' + text + '\\n' : '';
                        }
                        if (tag === 'img') {
                            const alt = el.getAttribute('alt');
                            const src = el.getAttribute('src');
                            return alt ? `![${alt}](${src || ''})` : '';
                        }
                        if (tag === 'li') {
                            return '- ' + el.textContent.trim();
                        }
                        if (tag === 'p' || tag === 'div') {
                            const texts = Array.from(el.childNodes).map(getText).filter(t => t);
                            return texts.join(' ');
                        }
                        return el.textContent.trim();
                    };
                    
                    const body = document.body;
                    if (!body) return '';
                    
                    const blocks = Array.from(body.childNodes)
                        .map(getText)
                        .filter(t => t)
                        .join('\\n');
                    return blocks;
                }
            """)
            return content.strip()
        except Exception as e:
            logger.warning(f"Markdown extraction failed: {e}")
            return ""


page_scraper = PageScraper()
