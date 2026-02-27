import random
import json
from typing import Dict, Any


def get_random_timezone() -> str:
    timezones = [
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Toronto",
        "America/Vancouver",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Australia/Sydney",
    ]
    return random.choice(timezones)


def get_random_locale() -> str:
    locales = [
        "en-US",
        "en-GB",
        "en-CA",
        "en-AU",
        "fr-FR",
        "de-DE",
        "es-ES",
        "it-IT",
        "ja-JP",
        "zh-CN",
    ]
    return random.choice(locales)


def get_canvas_fingerprint_override() -> str:
    return """
    Canvas.prototype.toDataURL = function() {
        return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
    };
    Canvas.prototype.getContext = function() {
        return {
            fillStyle: '',
            fillRect: function() {},
            fillText: function() {},
            strokeText: function() {},
            beginPath: function() {},
            moveTo: function() {},
            lineTo: function() {},
            stroke: function() {},
            arc: function() {},
            drawImage: function() {},
            createLinearGradient: function() {},
            createRadialGradient: function() {},
            addColorStop: function() {},
            getImageData: function() { return {data: new Uint8ClampedArray(1)}; },
            putImageData: function() {},
            scale: function() {},
            translate: function() {},
            transform: function() {},
            setTransform: function() {},
            resetTransform: function() {},
            globalAlpha: 1,
            fillStyle: '#000',
            strokeStyle: '#000',
            lineWidth: 1,
            lineCap: 'butt',
            lineJoin: 'miter',
            miterLimit: 10,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
            shadowBlur: 0,
            shadowColor: 'rgba(0, 0, 0, 0)',
            font: '10px sans-serif',
            textAlign: 'start',
            textBaseline: 'alphabetic',
            direction: 'ltr',
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'low'
        };
    };
    """


def get_webgl_vendor_override() -> str:
    vendors = [
        "Intel Inc.",
        "NVIDIA Corporation",
        "AMD",
        "Apple Inc.",
    ]
    renderer = random.choice(vendors)
    return f"""
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{
            return '{renderer}';
        }}
        if (parameter === 37446) {{
            return 'ANGLE';
        }}
        return getParameter.apply(this, arguments);
    }};
    
    const getExtension = WebGLRenderingContext.prototype.getExtension;
    WebGLRenderingContext.prototype.getExtension = function(name) {{
        if (name === 'WEBGL_debug_renderer_info') {{
            return {{
                UNMASKED_VENDOR_WEBGL: 37445,
                UNMASKED_RENDERER_WEBGL: 37446,
                getParameter: function(param) {{
                    if (param === 37445) {{
                        return '{renderer}';
                    }}
                    if (param === 37446) {{
                        return 'ANGLE';
                    }}
                    return null;
                }}
            }};
        }}
        return getExtension.apply(this, arguments);
    }};
    """


def get_stealth_js() -> str:
    return f"""
    {get_canvas_fingerprint_override()}
    {get_webgl_vendor_override()}
    
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined
    }});
    
    Object.defineProperty(navigator, 'plugins', {{
        get: () => [1, 2, 3, 4, 5]
    }});
    
    Object.defineProperty(navigator, 'languages', {{
        get: () => ['en-US', 'en']
    }});
    
    const originalChrome = window.chrome;
    Object.defineProperty(window, 'chrome', {{
        get: () => {{
            return {{
                runtime: {{}}
            }};
        }}
    }});
    
    window.navigator.chrome = {{
        runtime: {{}}
    }};
    
    const originalMatchMedia = window.matchMedia;
    window.matchMedia = function(query) {{
        return {{
            matches: false,
            media: query,
            onchange: null,
            addListener: function() {{}},
            removeListener: function() {{}},
            addEventListener: function() {{}},
            removeEventListener: function() {{}},
            dispatchEvent: function() {{ return true; }}
        }};
    }};
    """


def get_viewport_config() -> Dict[str, int]:
    viewports = [
        {"width": 1920, "height": 1080},
        {"width": 1440, "height": 900},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1280, "height": 720},
    ]
    return random.choice(viewports)
