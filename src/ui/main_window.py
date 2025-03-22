from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from controllers.face_controller import FaceController
from ui.right_column import RightColumn
from ui.left_column import LeftColumn
from injector import inject

class MainWindow(QMainWindow):
    @inject
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Comparison System")
        self.setMinimumSize(1200, 800)
        
        # Store injected controller
        self.face_controller = FaceController()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Add left column
        self.left_column = LeftColumn(self)
        layout.addWidget(self.left_column)
        
        # Add right column
        self.right_column = RightColumn()
        self.right_column.setFixedWidth(400)  # Set fixed width for right column
        layout.addWidget(self.right_column)
        
        # Set layout stretch factors (1:0)
        layout.setStretch(0, 1)  # Left column stretches
        layout.setStretch(1, 0)  # Right column fixed
        
        # Initialize system message area
        self.log_message("System initialized and ready.")
    
    def update_similarity_result(self, similarity_score: float):
        """Add a message to the system message area"""
        self.right_column.update_similarity_result(similarity_score)

    def log_message(self, message: str):
        """Add a message to the system message area"""
        self.right_column.log_message(message)