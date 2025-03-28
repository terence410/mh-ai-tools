from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPen
from ui.blocks.image_drop_block import ImageDropBlock
from controllers.face_controller import FaceController
from controllers.log_controller import LogController
from injector import inject

class LeftView(QWidget):
    @inject
    def __init__(self, face_controller: FaceController, log_controller: LogController):
        super().__init__()
        self._face_controller = face_controller
        self._log_controller = log_controller
        
        # Create layout
        self.layout = QHBoxLayout(self)
        
        # Add Image 1 and Image 2 drop areas with equal stretch
        self.image_drop_block_1 = ImageDropBlock("Image 1")
        self.image_drop_block_1.setMinimumSize(300, 500)
        self.image_drop_block_2 = ImageDropBlock("Image 2")
        self.image_drop_block_2.setMinimumSize(300, 500)
        self.layout.addWidget(self.image_drop_block_1, 1)  # stretch factor of 1
        self.layout.addWidget(self.image_drop_block_2, 1)  # stretch factor of 1

        # Connect signals to centralized event handler
        self.image_drop_block_1.block_event.connect(self._on_block_event)
        self.image_drop_block_2.block_event.connect(self._on_block_event)

    def _on_block_event(self, event_type: str, param: str):
        """Centralized event handler for all block events"""
        if event_type == "image_loaded":
            self._on_check_and_compare()
        elif event_type == "shift_color":
            self._on_shift_color(param)
        elif event_type == "copy_color":
            self._on_copy_color(param)


    def _on_copy_color(self, target: str):
        self._log_controller.log_message(f"Copy color to {target}\n")

        if target == "Image 1":
            if self.image_drop_block_2.image_area.region:
                self.image_drop_block_1.image_area.copy_color_from_image(
                    self.image_drop_block_2.image_area.region,
                    self.image_drop_block_2.image_area.image_pixmap.toImage()
                ) 
        else:
            if self.image_drop_block_1.image_area.region:
                self.image_drop_block_2.image_area.copy_color_from_image(
                    self.image_drop_block_1.image_area.region,
                    self.image_drop_block_1.image_area.image_pixmap.toImage()
                ) 

    def _on_shift_color(self, target: str):
        """Copy color from image 1 to image 2"""
        self._log_controller.log_message(f"Shift color stats to {target}\n")

        if target == "Image 1":
            color_stats = self.image_drop_block_2.image_area.region_color_stats;
            if color_stats and color_stats.pixel_count > 1:
                self.image_drop_block_1.image_area.shift_to_color_stats(color_stats)
        else:
            color_stats = self.image_drop_block_1.image_area.region_color_stats;
            if color_stats and color_stats.pixel_count > 1:
                self.image_drop_block_2.image_area.shift_to_color_stats(color_stats)

    def _on_check_and_compare(self):
        """Check if both images are loaded and perform comparison"""
        if (self.image_drop_block_1.image_area.image_source and 
            self.image_drop_block_2.image_area.image_source):
            
            self._log_controller.log_message(">>> Starting Face Comparison")
            
            try:
                # Perform face comparison using face_controller
                result = self._face_controller.compare_images(
                    self.image_drop_block_1.image_area.image_source,
                    self.image_drop_block_2.image_area.image_source
                )
                
                # Log the results
                self._log_controller.update_similarity_score(result.similarity_score)

                # Draw face boxes on both images
                self.image_drop_block_1.image_area.update_face_location(result.face1_location)
                self.image_drop_block_2.image_area.update_face_location(result.face2_location)
                
                # Log the results
                self._log_controller.log_message(f"- Similarity Score: {result.similarity_score:.2f}")
                self._log_controller.log_message(f"- Processing Time: {result.processing_time:.2f} seconds\n")
                                
            except Exception as e:
                self._log_controller.log_message(f"Error during face comparison: {str(e)}\n")