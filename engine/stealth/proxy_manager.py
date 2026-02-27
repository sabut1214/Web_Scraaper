import random
from typing import List, Optional
from config import get_settings


class ProxyManager:
    def __init__(self):
        self.settings = get_settings()
        self._proxies: List[str] = self.settings.proxies.copy()
        self._current_index = 0

    def add_proxy(self, proxy: str):
        if proxy not in self._proxies:
            self._proxies.append(proxy)

    def remove_proxy(self, proxy: str):
        if proxy in self._proxies:
            self._proxies.remove(proxy)

    def get_random_proxy(self) -> Optional[str]:
        if not self._proxies:
            return None
        return random.choice(self._proxies)

    def get_next_proxy(self) -> Optional[str]:
        if not self._proxies:
            return None
        proxy = self._proxies[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._proxies)
        return proxy

    def get_all_proxies(self) -> List[str]:
        return self._proxies.copy()


proxy_manager = ProxyManager()
