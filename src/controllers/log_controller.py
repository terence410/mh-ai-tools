from typing import List, Callable
from injector import singleton

@singleton
class LogController:
    def __init__(self):
        self._listeners: List[Callable[[str], None]] = []
    
    def add_listener(self, listener: Callable[[str], None]):
        """Add a new listener for log messages"""
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[str], None]):
        """Remove a listener"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def log_message(self, message: str):
        """Broadcast a log message to all listeners"""
        for listener in self._listeners:
            listener(message)
