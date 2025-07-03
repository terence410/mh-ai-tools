from typing import Callable, Tuple
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import (QDragEnterEvent, QDropEvent, QPixmap, QPainter, QPen)
import numpy as np

from controllers.image_controller import ImageController, RGBColorStats
from injector import inject

class ImageArea(QLabel):
    """Custom QLabel that accepts drag and drop"""
    @inject
    def __init__(self, log_message = None):
        super().__init__()
        self.setAcceptDrops(True)
        # Add mouse interaction attributes
        self.drawing = False
        self.start_point = None
        self.current_point = None
        self.selection_box = None
        self.image_pixmap = None
        self.image_source = None
        self.region_color_stats = None
        self.region = None
        
        # Store references to meta and logging labels
        self._log_message = log_message
        self._image_controller = ImageController()
        
        # Add display pixmap for drawing operations
        self._display_pixmap = None
        
    def _fit_image_to_screen(self):
        # Scale the image to fit the label while maintaining aspect ratio
        scaled_pixmap = self._display_pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)

    def _get_scaled_image_rect(self):
        """Get the rectangle of the scaled image within the label"""
        if self.pixmap():
            scaled_size = self.pixmap().size()
            x = (self.width() - scaled_size.width()) // 2
            y = (self.height() - scaled_size.height()) // 2
            return QRect(x, y, scaled_size.width(), scaled_size.height())
        return QRect()

    def _draw_face_box(self):
        """Draw face detection box on the current widget considering image scaling and position"""
        if not self._display_pixmap or not hasattr(self, 'face_location') or not self.face_location:
            return
            
        # Get the current scaled image rectangle within the widget
        scaled_rect = self._get_scaled_image_rect()
        if not scaled_rect.isValid():
            return
            
        # Calculate scaling factors between original image and current display
        scale_x = scaled_rect.width() / self._display_pixmap.width()
        scale_y = scaled_rect.height() / self._display_pixmap.height()
        
        # Get face location coordinates
        top, left, bottom, right = self.face_location
        
        # Scale the coordinates to match current display size
        scaled_left = int(left * scale_x) + scaled_rect.left()
        scaled_top = int(top * scale_y) + scaled_rect.top()
        scaled_right = int(right * scale_x) + scaled_rect.left()
        scaled_bottom = int(bottom * scale_y) + scaled_rect.top()
        
        # Create painter for the widget
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up the pen for drawing
        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw the face box
        painter.drawRect(
            scaled_left,
            scaled_top,
            scaled_right - scaled_left,
            scaled_bottom - scaled_top
        )
        
        painter.end()

    def _draw_selection_box(self):
        painter = QPainter(self)
        
        # Enable antialiasing for smoother lines
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up the pen
        pen = QPen(Qt.GlobalColor.green)
        pen.setWidth(2)
        painter.setPen(pen)
        
        if self.drawing:
            # Draw current selection rectangle
            rect = QRect(self.start_point, self.current_point).normalized()
            painter.drawRect(rect)
        elif self.selection_box:
            # Draw final selection rectangle
            painter.drawRect(self.selection_box)
        
        painter.end()

    def _update_selection_box(self, box: QRect):
        self.selection_box = box
        # self._calculate_selection_stats()

    def _calculate_selection_stats(self):
        """Calculate and log statistics for the selected area"""
        # Get selection box from the image area
        if not self.selection_box or not self.image_pixmap:
            return

        # Convert selection box coordinates to original image coordinates
        scaled_rect = self._get_scaled_image_rect()
        if not scaled_rect.isValid():
            return

        # Calculate scaling factors
        width = self.image_pixmap.width()
        height = self.image_pixmap.height()
        scale_x = width / scaled_rect.width()
        scale_y = height / scaled_rect.height()

        # Transform selection box coordinates to original image coordinates
        selection_width = self.selection_box.width()
        selection_height = self.selection_box.height()
        orig_x1 = int((self.selection_box.left() - scaled_rect.left()) * scale_x)
        orig_y1 = int((self.selection_box.top() - scaled_rect.top()) * scale_y)
        orig_x2 = int((self.selection_box.right() - scaled_rect.left()) * scale_x)
        orig_y2 = int((self.selection_box.bottom() - scaled_rect.top()) * scale_y)

        # Get image data and calculate stats using image_controller
        image = self.image_pixmap.toImage()
        region = (orig_x1, orig_y1, orig_x2, orig_y2)
        stats = self._image_controller.calculate_region_rgb_color_stats(image, region)

        # Store stats and region
        self.region_color_stats = stats
        self.region = region

        # Update image info with results
        self._log_message(
            f"Total pixels: {stats.pixel_count}, {selection_width}x{selection_height}\n"
            f"R: {stats.avg_r:.0f} / {stats.r_sd:0.1f}, G: {stats.avg_g:.0f} / {stats.g_sd:0.1f}, B: {stats.avg_b:.0f} / {stats.b_sd:0.1f}\n"
            f"white: {stats.avg_white:.0f} / {stats.white_sd:0.1f}"
        )

    
    """ Begin: Overrriding methods"""
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if self.pixmap() and event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.current_point = event.pos()
            self.selection_box = None
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.drawing:
            self.current_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if self.drawing and event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            box = QRect(self.start_point, self.current_point).normalized()
            self._update_selection_box(box)

    def paintEvent(self, event):
        """Override paint event to draw selection box"""
        super().paintEvent(event)
        self._draw_selection_box()
        self._draw_face_box()

    """ End: Overrriding methods"""
    
    def clear_region(self):
        """Clear the selected region and related variables"""
        self.selection_box = None
        self.region = None
        self.region_color_stats = None
        self.start_point = None
        self.current_point = None
        self.drawing = False
        self.update()

    def load_image(self, source: str):
        try:
            # Load image using QImage first to handle ICC profile
            image = QImage(source)
            if image.isNull():
                self._log_message(f"Error: Could not load image {source.split('/')[-1]}")
                return
                
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(image)
        except Exception as e:
            self._log_message(f"Error processing image: {str(e)}")
            return


        self.image_pixmap = pixmap
        self._display_pixmap = QPixmap(pixmap)  # Create a copy for display
        self.image_source = source
        self._fit_image_to_screen()

        # check image size
        if self.image_pixmap.width() < 384 and self.image_pixmap.height() < 384:
            self._log_message(f"Image size is too small")

        return self.image_pixmap

    def copy_color_from_image(self, source_region: Tuple[int, int, int, int], source_image: QImage):
        image = self.image_pixmap.toImage()
        updated_image = self._image_controller.apply_region_lighting_transfer(
            image, 
            source_image,
            source_region, 
        )

        # Update both the original and display pixmaps
        qpixmap = QPixmap.fromImage(updated_image)
        self.image_pixmap = qpixmap
        self._display_pixmap = QPixmap(qpixmap)
        self._fit_image_to_screen()
        
        # calculate stats again
        self._calculate_selection_stats()

    
    def shift_to_color_stats(self, color_stats: RGBColorStats):
        if not self.region_color_stats or not self.region:
            return

        image = self.image_pixmap.toImage()
        updated_image = self._image_controller.apply_region_rgb_color_stats(
            image, 
            self.region, 
            self.region_color_stats, 
            color_stats
        )

        # Update both the original and display pixmaps
        qpixmap = QPixmap.fromImage(updated_image)
        self.image_pixmap = qpixmap
        self._display_pixmap = QPixmap(qpixmap)
        self._fit_image_to_screen()
        
        # calculate stats again
        self._calculate_selection_stats()

    def update_face_location(self, face_location: tuple[int, int, int, int]):
        self.face_location = face_location
        self.update()
