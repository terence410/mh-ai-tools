from typing import List, Callable
from injector import singleton

@singleton
class LogController:
    def __init__(self):
        self._listeners: List[Callable[[str], None]] = []
        self._similarity_listeners: List[Callable[[float], None]] = []
    
    def add_listener(self, listener: Callable[[str], None]):
        """Add a new listener for log messages"""
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[str], None]):
        """Remove a listener"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def add_similarity_listener(self, listener: Callable[[float], None]):
        """Add a new listener for similarity score updates"""
        if listener not in self._similarity_listeners:
            self._similarity_listeners.append(listener)
    
    def remove_similarity_listener(self, listener: Callable[[float], None]):
        """Remove a similarity score listener"""
        if listener in self._similarity_listeners:
            self._similarity_listeners.remove(listener)
    
    def log_message(self, message: str):
        """Broadcast a log message to all listeners"""
        for listener in self._listeners:
            listener(message)
            
    def update_similarity_score(self, score: float):
        """Broadcast a similarity score update to all listeners"""
        for listener in self._similarity_listeners:
            listener(score)
