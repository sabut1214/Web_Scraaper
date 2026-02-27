from typing import Optional
from selectolax.parser import HTMLParser
from config import get_settings
from core.logger import setup_logger

logger = setup_logger("html_cleaner")


class HTMLCleaner:
    REMOVE_TAGS = {
        "script",
        "style",
        "svg",
        "noscript",
        "iframe",
        "form",
        "input",
        "button",
        "select",
        "textarea",
        "meta",
        "link",
        "base",
        "area",
        "audio",
        "video",
        "source",
        "track",
        "canvas",
        "map",
        "embed",
        "object",
        "param",
        "picture",
        "portal",
        "slot",
    }
    
    REMOVE_ATTRIBUTES = [
        "onclick",
        "onload",
        "onerror",
        "onmouseover",
        "onmouseout",
        "onkeydown",
        "onkeyup",
        "onkeypress",
        "onchange",
        "onsubmit",
        "onfocus",
        "onblur",
        "oncontextmenu",
        "ondrag",
        "ondrop",
        "style",
        "class",
        "id",
        "data-*",
        "aria-*",
    ]
    
    def __init__(self):
        self.settings = get_settings()

    def clean(self, html: str, preserve_text: bool = True) -> str:
        try:
            parser = HTMLParser(html)
            
            for tag in self.REMOVE_TAGS:
                for node in parser.css(tag):
                    node.decompose()
            
            for node in parser.css("*"):
                for attr in list(node.attributes.keys()):
                    if any(
                        attr == ra or (ra.endswith("*") and attr.startswith(ra[:-1]))
                        for ra in self.REMOVE_ATTRIBUTES
                    ):
                        del node.attributes[attr]
            
            if preserve_text:
                return self._get_clean_text(parser)
            
            return parser.html()
        
        except Exception as e:
            logger.error(f"HTML cleaning failed: {e}")
            return html

    def _get_clean_text(self, parser: HTMLParser) -> str:
        body = parser.body
        if body is None:
            return ""
        
        text_parts = []
        
        def process_node(node):
            if node.tag == "script" or node.tag == "style":
                return
            
            if node.text:
                text_parts.append(node.text.strip())
            
            if hasattr(node, "childs"):
                for child in node.childs:
                    process_node(child)
        
        for child in body.childs:
            process_node(child)
        
        result = " ".join(filter(None, text_parts))
        
        import re
        result = re.sub(r"\s+", " ", result)
        result = re.sub(r"\n\s*\n", "\n\n", result)
        
        return result.strip()

    def clean_for_extraction(self, html: str, max_length: Optional[int] = None) -> str:
        cleaned = self.clean(html)
        
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
            logger.info(f"Cleaned HTML truncated to {max_length} characters")
        
        return cleaned


html_cleaner = HTMLCleaner()
