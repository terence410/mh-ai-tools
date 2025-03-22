from injector import singleton, inject

@singleton
class DisplayController:
    """Controller for display-related utilities"""
    
    @inject
    def __init__(self):
        pass

    def format_file_size(self, size: float) -> str:
        """
        Convert file size to human readable format
        
        Args:
            size: File size in bytes
            
        Returns:
            Formatted string with appropriate unit (B, KB, MB, GB, TB)
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB" 