from PyQt6.QtWidgets import QLabel, QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import (QDragEnterEvent, QDropEvent, QPixmap, QKeyEvent, 
                        QPainter, QPen)

from lib.common import format_file_size
from lib.image_color import RGBColorStats
from .image_area import ImageArea
import os

class ImageDropView(QWidget):
    # Define signal for image loaded
    image_loaded_event = pyqtSignal()  # Signal with image path and title
    copy_color_event = pyqtSignal(str)  # Signal with color string parameter

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # add top bar
        self._add_top_bar_buttons()
        
        # Create image meta area
        self.image_meta = QLabel()
        self.image_meta.setFixedHeight(30)
        self.image_meta.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                padding: 5px;
            }
        """)
        
        # Create image info area
        self.logging = QLabel()
        self.logging.setFixedHeight(90)
        self.logging.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                padding: 5px;
            }
        """)
        
        # Create image area using ImageArea
        self.image_area = ImageArea(self, self.image_meta, self.logging)
        self.image_area.setMinimumSize(300, 500)
        self.image_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_area.setText(f"Drop {title} here")
        self.image_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f0f0f0;
                padding: 10px;
            }
        """)
        
        # Add widgets to layout
        self.layout.addWidget(self.image_area)
        self.layout.addWidget(self.image_meta)
        self.layout.addWidget(self.logging)
        
        # Initialize other attributes
        self.is_active = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _add_top_bar_buttons(self):
        """Add buttons to the top bar"""
        # Button style template
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """
        
        # Create a horizontal layout
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create paste button
        paste_button = QPushButton("Paste")
        paste_button.setFixedSize(80, 28)
        paste_button.clicked.connect(self._top_bar_paste_image)
        paste_button.setStyleSheet(button_style)
        
        # Create copy color button
        copy_color_button = QPushButton("Copy Color")
        copy_color_button.setFixedSize(80, 28)
        copy_color_button.clicked.connect(self._top_bar_copy_color)
        copy_color_button.setStyleSheet(button_style)

        download_button = QPushButton("Download")
        download_button.setFixedSize(80, 28)
        download_button.clicked.connect(self._top_bar_download_image)
        download_button.setStyleSheet(button_style)
        
        # Add buttons to layout
        top_bar_layout.addWidget(paste_button)
        top_bar_layout.addWidget(copy_color_button)
        top_bar_layout.addWidget(download_button)
        top_bar_layout.addStretch()  # Add stretch to push buttons to the left
        
        # Add the layout directly to the main layout
        self.layout.addLayout(top_bar_layout)

    def _top_bar_paste_image(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                # Save clipboard image to temp file
                temp_path = f"tmp/temp_{self.title}.png"
                pixmap = QPixmap.fromImage(image)
                pixmap.save(temp_path)
                self.load_image(temp_path)
            else:
                self._log_message("Error: Invalid image in clipboard")
        else:
            self._log_message("Error: No image in clipboard")

    def _top_bar_copy_color(self):
        self.copy_color_event.emit(self.title)

    def _top_bar_download_image(self):
        """Prompt to save the image if it exists"""
        if self.image_area.image_pixmap:  # Check if there is an image
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg);;All Files (*)")
            if file_name:  # If a file name is provided
                self.image_area.image_pixmap.save(file_name)  # Save the image
        else:
            self._log_message("Error: No image to download")  # Log error if no image

    def _log_message(self, message: str):
        """Add a message to the system message area"""
        self.logging.setText(message)

    def load_image(self, source: str):
        """Process and display the image from a file path"""
                
        # Store the original pixmap
        self.image_area.update_image(source)
        self.image_area.clear_region()
        
        # Get file size and dimensions
        width = self.image_area.image_pixmap.width()
        height = self.image_area.image_pixmap.height()
        file_size = os.path.getsize(source)
        size_str = format_file_size(file_size)
        
        # Update image meta with basic info
        self.image_meta.setText(f"{source.split('/')[-1]}, {width}x{height}, {size_str}")
        
        # Emit signal that image was loaded
        self.image_loaded_event.emit()
            
    
