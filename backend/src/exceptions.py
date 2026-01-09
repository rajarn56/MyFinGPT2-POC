class MyFinGPTException(Exception):
    """Base exception for MyFinGPT"""
    pass


class AuthenticationError(MyFinGPTException):
    """Authentication-related errors"""
    pass


class SessionError(MyFinGPTException):
    """Session-related errors"""
    pass


class DatabaseError(MyFinGPTException):
    """Database-related errors"""
    pass


class ValidationError(MyFinGPTException):
    """Validation errors"""
    pass

