from typing import Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt

class RightColumn(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create layout
        right_layout = QVBoxLayout(self)
        
        # Base style for similarity result
        self.style_template = """
            QTextEdit {
                background-color: COLOR;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                margin: 0px;
                text-align: center;
            }
        """
        
        # Add similarity result area (fixed height)
        self.similarity_result = QTextEdit()
        self.similarity_result.setReadOnly(True)
        self.similarity_result.setText("Similarity results will appear here...")
        self.similarity_result.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.similarity_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Calculate single line height using font metrics
        font_metrics = self.similarity_result.fontMetrics()
        line_height = font_metrics.height() + 20 + 2  # Add 2 pixels for padding
        self.similarity_result.setFixedHeight(line_height)
        self._update_similarity_style("#f8f8f8")  # Set initial background color
        right_layout.addWidget(self.similarity_result)  # No stretch for similarity result
        
        # Add message area (expandable)
        self.message_area = QTextEdit()
        self.message_area.setReadOnly(True)
        self.message_area.setPlaceholderText("System messages will appear here...")
        self.message_area.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        right_layout.addWidget(self.message_area)  # Stretch factor of 1 to fill remaining space

    def _interpret_similarity(self, similarity: float) -> Tuple[str, str]:
        """Interpret the similarity score based on InsightFace's typical thresholds"""
        if similarity > 0.6:
            return "#87E169", f"{similarity:.2f} - Highly likely to bethe same person"
        elif similarity > 0.5:
            return "#E1DF06", f"{similarity:.2f} - Likely to be the same person"
        elif similarity > 0.4:
            return "#E17F03", f"{similarity:.2f} - Some chance to be the same person"
        else:
            return "#999999", f"{similarity:.2f} - Different persons"

    def log_message(self, message: str):
        """Add a message to the system message area"""
        self.message_area.append(message) 

    def _update_similarity_style(self, background_color: str):
        """Update similarity result style with given background color"""
        self.similarity_result.setStyleSheet(self.style_template.replace("COLOR", background_color))

    def update_similarity_result(self, similarity: float):
        [color, message] = self._interpret_similarity(similarity)
        self._update_similarity_style(color)
        self.similarity_result.setText(message) 
        self.similarity_result.setAlignment(Qt.AlignmentFlag.AlignCenter)