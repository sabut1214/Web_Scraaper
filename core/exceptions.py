class ScraperException(Exception):
    pass


class BrowserException(ScraperException):
    pass


class ExtractionException(ScraperException):
    pass


class ProxyException(ScraperException):
    pass


class JobNotFoundException(ScraperException):
    pass


class InvalidRequestException(ScraperException):
    pass
