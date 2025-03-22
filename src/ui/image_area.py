from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import (QDragEnterEvent, QDropEvent, QPixmap, QPainter, QPen)
import numpy as np

from controllers.image_controller import ImageController, RGBColorStats
from injector import inject

class ImageArea(QLabel):
    """Custom QLabel that accepts drag and drop"""
    @inject
    def __init__(self, parent=None, image_meta=None, logging=None):
        super().__init__(parent)
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
        self.image_meta = image_meta
        self.logging = logging
        self.image_controller = ImageController()
        
        # Add display pixmap for drawing operations
        self.display_pixmap = None
        
    def _fit_image_to_screen(self):
        # Scale the image to fit the label while maintaining aspect ratio
        scaled_pixmap = self.display_pixmap.scaled(
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

    def _draw_face_box(self, pixmap: QPixmap, face_location: tuple[int, int, int, int]) -> QPixmap:
        # Create a new pixmap to avoid modifying the original
        result_pixmap = QPixmap(pixmap)
        painter = QPainter(result_pixmap)
        
        # Calculate pen width based on the target display size (300x500 minimum)
        target_width = 300  # Minimum width of the display area
        scale_factor = pixmap.width() / target_width
        pen_width = max(1, int(2 * scale_factor))
        
        # Set up the pen for drawing
        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(pen_width)
        painter.setPen(pen)
        
        # Draw boxes for each detected face
        [top, left, bottom, right] = face_location
        painter.drawRect(left, top, right - left, bottom - top)
        
        painter.end()
        return result_pixmap

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
        scale_x = self.image_pixmap.width() / scaled_rect.width()
        scale_y = self.image_pixmap.height() / scaled_rect.height()

        # Transform selection box coordinates to original image coordinates
        orig_x1 = int((self.selection_box.left() - scaled_rect.left()) * scale_x)
        orig_y1 = int((self.selection_box.top() - scaled_rect.top()) * scale_y)
        orig_x2 = int((self.selection_box.right() - scaled_rect.left()) * scale_x)
        orig_y2 = int((self.selection_box.bottom() - scaled_rect.top()) * scale_y)

        # Get image data and calculate stats using image_controller
        image = self.image_pixmap.toImage()
        region = (orig_x1, orig_y1, orig_x2, orig_y2)
        stats = self.image_controller.calculate_region_rgb_color_stats(image, region)

        # Store stats and region
        self.region_color_stats = stats
        self.region = region

        # Update image info with results
        if self.logging:
            self.logging.setText(
                f"Total pixels: {stats.pixel_count}\n"
                f"R: {stats.avg_r:.0f} / {stats.r_sd:0.1f}, G: {stats.avg_g:.0f} / {stats.g_sd:0.1f}, B: {stats.avg_b:.0f} / {stats.b_sd:0.1f}\n"
                f"white: {stats.avg_white:.0f} / {stats.white_sd:0.1f}"
            )

    """ Begin: Overrriding methods"""
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            self.parent().load_image(file_path)
        else:
            event.ignore()

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
            self.update_selection_box(box)

    def paintEvent(self, event):
        """Override paint event to draw selection box"""
        super().paintEvent(event)
        if self.drawing or self.selection_box:
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

    def update_image(self, source: str):
        try:
            pixmap = QPixmap(source)
            if pixmap.isNull():
                self.logging.setTEet(f"Error: Could not load image {source.split('/')[-1]}")
                return
        except Exception as e:
            self.logging.setText(f"Error processing image: {str(e)}")
            return

        self.image_pixmap = pixmap
        self.display_pixmap = QPixmap(pixmap)  # Create a copy for display
        self.image_source = source
        self._fit_image_to_screen()
    
    def update_selection_box(self, box: QRect):
        self.selection_box = box
        self._calculate_selection_stats()

    def draw_face_box_on_image(self, face_location: tuple[int, int, int, int]) -> None:
        """Draw face detection box on the image area"""
        if not self.image_pixmap or not face_location:
            return
        
        # Draw box on the display pixmap
        self.display_pixmap = self._draw_face_box(self.display_pixmap, face_location)
            
        # Scale the image with box to fit the label
        scaled_image = self.display_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_image)

    def apply_from_color_stats(self, color_stats: RGBColorStats):
        if not self.region_color_stats or not self.region:
            return

        image = self.image_pixmap.toImage()
        updated_image = self.image_controller.apply_region_rgb_color_stats(
            image, 
            self.region, 
            self.region_color_stats, 
            color_stats
        )

        # Update both the original and display pixmaps
        qpixmap = QPixmap.fromImage(updated_image)
        self.image_pixmap = qpixmap
        self.display_pixmap = QPixmap(qpixmap)
        
        # Update the display
        scaled_pixmap = self.display_pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)

        # calculate stats again
        self._calculate_selection_stats()

