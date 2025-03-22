from contextlib import redirect_stdout
from io import StringIO
import json
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from dataclasses import dataclass
from typing import List, Tuple, Optional
from PIL import Image
from enum import Enum
import time
from injector import singleton, inject

@dataclass
class FaceMatchResult:
    similarity_score: float
    features_scores: List[float]
    face1_location: Tuple[int, int, int, int]
    face2_location: Tuple[int, int, int, int]
    processing_time: float
    face1_landmarks: Optional[np.ndarray] = None
    face2_landmarks: Optional[np.ndarray] = None

@singleton
class FaceController:
    @inject
    def __init__(self):
        # Initialize face analysis with more lenient detection for artwork
        self.app = FaceAnalysis(
            name='buffalo_l',  # or 'buffalo_l', 'buffalo_m', etc.
            root='.',  # Model download path
            providers=['CPUExecutionProvider'],
            allowed_modules=['detection', 'recognition', 'landmark_2d_106']
        )
        # Configure with larger detection size and lower threshold for illustrations
        self.app.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.3)

    def _process_image(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[List]]:
        """Process an image and detect faces"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = self.app.get(img)
            
            if not faces:
                return None, None

            return img, faces
            
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None, None

    def _standard_face_comparison(self, faces1, faces2) -> float:
        """Standard face comparison using InsightFace embeddings"""
        # Validate faces were detected
        if faces1 is None or faces1[0] is None or faces2 is None or faces2[0] is None:
            return 0.0
        
        # Get embeddings for the first face in each image
        embedding1 = faces1[0].embedding
        embedding2 = faces2[0].embedding
        
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        # Normalize embeddings to unit length
        embedding1_norm = embedding1 / np.linalg.norm(embedding1)
        embedding2_norm = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1_norm, embedding2_norm)
        
        # Ensure the similarity score is between 0 and 1
        similarity = max(0.0, min(1.0, float(similarity)))
        
        return similarity 

    def compare_images(self, image1_path: str, image2_path: str) -> FaceMatchResult:
        """Compare two images and return face match results"""
        # Start timing
        start_time = time.time()
        
        # Process images and get faces
        img1, faces1 = self._process_image(image1_path)
        img2, faces2 = self._process_image(image2_path)
        
        # Initialize face locations and landmarks
        face1_location = None
        face2_location = None
        face1_landmarks = None
        face2_landmarks = None
        
        # Get face locations if faces are detected
        if faces1 and faces1[0]:
            bbox1 = faces1[0].bbox.astype(int)
            face1_location = (bbox1[1], bbox1[0], bbox1[3], bbox1[2])
            if hasattr(faces1[0], 'landmark_2d_106') and faces1[0].landmark_2d_106 is not None:
                face1_landmarks = faces1[0].landmark_2d_106
        
        if faces2 and faces2[0]:
            bbox2 = faces2[0].bbox.astype(int)
            face2_location = (bbox2[1], bbox2[0], bbox2[3], bbox2[2])
            if hasattr(faces2[0], 'landmark_2d_106') and faces2[0].landmark_2d_106 is not None:
                face2_landmarks = faces2[0].landmark_2d_106
        
        # Get embedding similarity using the detected faces
        embedding_similarity = self._standard_face_comparison(faces1, faces2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return FaceMatchResult(
            similarity_score=embedding_similarity,
            features_scores=[],
            face1_location=face1_location,
            face2_location=face2_location,
            processing_time=processing_time,
            face1_landmarks=face1_landmarks,
            face2_landmarks=face2_landmarks
        ) 