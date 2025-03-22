from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPen
from ui.image_drop_view import ImageDropView
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ui.main_window import MainWindow

class LeftColumn(QWidget):
    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.main_window: "MainWindow" = main_window
        
        # Create layout
        self.layout = QHBoxLayout(self)
        
        # Add Image 1 and Image 2 drop areas with equal stretch
        self.image1_view = ImageDropView("Image 1")
        self.image1_view.setMinimumSize(300, 500)
        self.image2_view = ImageDropView("Image 2")
        self.image2_view.setMinimumSize(300, 500)
        self.layout.addWidget(self.image1_view, 1)  # stretch factor of 1
        self.layout.addWidget(self.image2_view, 1)  # stretch factor of 1

        # Connect signals
        self.image1_view.image_loaded_event.connect(self.on_check_and_compare)
        self.image2_view.image_loaded_event.connect(self.on_check_and_compare)

        self.image1_view.copy_color_event.connect(self.on_copy_color)
        self.image2_view.copy_color_event.connect(self.on_copy_color)

    def on_copy_color(self, target: str):
        """Copy color from image 1 to image 2"""
        self.main_window.log_message(f"Copy color to {target}\n")

        # check where to copy color
        if target == "Image 2":
            color_stats = self.image1_view.image_area.region_color_stats;
            if color_stats and color_stats.pixel_count > 1:
                self.image2_view.image_area.apply_from_color_stats(color_stats)
        else:
            color_stats = self.image2_view.image_area.region_color_stats;
            if color_stats and color_stats.pixel_count > 1:
                self.image1_view.image_area.apply_from_color_stats(color_stats)

    def on_check_and_compare(self):
        """Check if both images are loaded and perform comparison"""
        if (self.image1_view.image_area.image_source and 
            self.image2_view.image_area.image_source):
            
            self.main_window.log_message(">>> Starting Face Comparison")
            
            try:
                # Perform face comparison
                result = self.main_window.face_comparison.compare_images(
                    self.image1_view.image_area.image_source,
                    self.image2_view.image_area.image_source
                )
                
                # Log the results
                self.main_window.update_similarity_result(result.similarity_score);

                # Draw face boxes on both images
                self.image1_view.image_area.draw_face_box_on_image(result.face1_location)
                self.image2_view.image_area.draw_face_box_on_image(result.face2_location)
                                
            except Exception as e:
                self.main_window.log_message(f"Error during face comparison: {str(e)}\n") 

            self.main_window.log_message(f"- Processing Time: {result.processing_time:.2f} seconds\n")