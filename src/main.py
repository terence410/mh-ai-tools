import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from PIL import Image, ImageEnhance
import time
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from injector import Injector
from di.app_module import DynamicAppModule

def main():
    # Define your dependency configuration
    dependency_config = {
        'FaceController': 'controllers.face_controller.FaceController',
        'ImageController': 'controllers.image_controller.ImageController',
        'DisplayController': 'controllers.display_controller.DisplayController',
        'MainWindow': 'ui.main_window.MainWindow',
        # Add any other dependencies here
    }

    # Create application
    app = QApplication(sys.argv)
    
    # Initialize injector with dynamic module
    injector = Injector([DynamicAppModule(dependency_config)])
    
    # Get main window instance
    window = injector.get(MainWindow)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 

