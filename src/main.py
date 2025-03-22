import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from PIL import Image, ImageEnhance
import time
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 

