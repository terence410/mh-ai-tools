from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from controllers.face_controller import FaceController
from controllers.log_controller import LogController
from ui.views.right_view import RightView
from ui.views.left_view import LeftView
from injector import inject, singleton, Injector
from PyQt6.QtCore import QRect

@singleton
class MainWindow(QMainWindow):
    @inject
    def __init__(self, log_controller: LogController, injector: Injector):
        super().__init__()
        self.setWindowTitle("Face Comparison System")
        self.setMinimumSize(1400, 800)
        
        # Set window position and size
        screen = self.screen()
        screen_geometry = screen.geometry()
        window_width = 1400
        window_height = 800
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(QRect(x, y, window_width, window_height))
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create columns using injector
        left_view = injector.get(LeftView)
        right_view = injector.get(RightView)
        
        # Add columns to layout
        layout.addWidget(left_view)
        
        # Set fixed width for right column
        right_view.setFixedWidth(400)
        layout.addWidget(right_view)
        
        # Set layout stretch factors (1:0)
        layout.setStretch(0, 1)  # Left column stretches
        layout.setStretch(1, 0)  # Right column fixed
        
        # Initialize system message area
        log_controller.log_message("System initialized and ready.")
    