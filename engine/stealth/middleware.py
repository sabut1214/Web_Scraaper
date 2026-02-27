from typing import Optional, Dict, Any
from playwright.async_api import Page, BrowserContext
from config import get_settings
from engine.stealth.user_agents import get_random_user_agent
from engine.stealth.proxy_manager import proxy_manager
from engine.stealth.fingerprint import get_stealth_js, get_viewport_config, get_random_timezone, get_random_locale


class StealthMiddleware:
    def __init__(self):
        self.settings = get_settings()

    async def apply_stealth(self, context: BrowserContext):
        await context.add_init_script(get_stealth_js())
        
        viewport = get_viewport_config()
        await context.set_viewport_size(viewport)
        
        timezone = get_random_timezone()
        locale = get_random_locale()
        
        await context.set_extra_http_headers({
            "Accept-Language": f"{locale},en;q=0.9",
        })
        
        await context.add_cookies([{
            "name": "timezone",
            "value": timezone,
            "domain": ".",
            "path": "/",
        }])

    def get_context_options(
        self,
        proxy: Optional[Dict[str, Any]] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        options: Dict[str, Any] = {}
        
        if user_agent is None and self.settings.stealth_user_agent_rotation:
            user_agent = get_random_user_agent()
        
        if user_agent:
            options["user_agent"] = user_agent
        
        proxy_url = None
        if proxy:
            proxy_url = proxy.get("url")
        elif self.settings.stealth_proxy_rotation:
            proxy_url = proxy_manager.get_random_proxy()
        
        if proxy_url:
            proxy_config: Dict[str, Any] = {"server": proxy_url}
            
            if proxy and proxy.get("username") and proxy.get("password"):
                proxy_config["username"] = proxy["username"]
                proxy_config["password"] = proxy["password"]
            
            options["proxy"] = proxy_config
        
        options["ignore_https_errors"] = True
        
        return options


stealth_middleware = StealthMiddleware()
