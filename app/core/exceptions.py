class LinkForgeException(Exception):
    pass


class ScrapingException(LinkForgeException):
    def __init__(self, message: str = "Scraping operation failed"):
        self.message = message
        super().__init__(self.message)


class AuthError(ScrapingException):
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class RateLimitError(ScrapingException):
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


class ScrapingError(ScrapingException):
    def __init__(self, message: str = "Scraping failed"):
        self.message = message
        super().__init__(self.message)


class AnalysisException(LinkForgeException):
    def __init__(self, message: str = "Analysis operation failed"):
        self.message = message
        super().__init__(self.message)


class DatabaseException(LinkForgeException):
    def __init__(self, message: str = "Database operation failed"):
        self.message = message
        super().__init__(self.message)


class NotFoundException(LinkForgeException):
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class ValidationException(LinkForgeException):
    def __init__(self, message: str = "Validation failed"):
        self.message = message
        super().__init__(self.message)


class RecommendationException(LinkForgeException):
    def __init__(self, message: str = "Recommendation generation failed"):
        self.message = message
        super().__init__(self.message)
