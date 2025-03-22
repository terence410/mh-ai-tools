from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from controllers.face_controller import FaceController
from controllers.log_controller import LogController
from ui.right_column import RightColumn
from ui.left_column import LeftColumn
from injector import inject, singleton, Injector

@singleton
class MainWindow(QMainWindow):
    @inject
    def __init__(self, log_controller: LogController, injector: Injector):
        super().__init__()
        self.setWindowTitle("Face Comparison System")
        self.setMinimumSize(1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create columns using injector
        left_column = injector.get(LeftColumn)
        right_column = injector.get(RightColumn)
        
        # Add columns to layout
        layout.addWidget(left_column)
        
        # Set fixed width for right column
        right_column.setFixedWidth(400)
        layout.addWidget(right_column)
        
        # Set layout stretch factors (1:0)
        layout.setStretch(0, 1)  # Left column stretches
        layout.setStretch(1, 0)  # Right column fixed
        
        # Initialize system message area
        log_controller.log_message("System initialized and ready.")
    