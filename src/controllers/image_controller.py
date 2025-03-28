from PyQt6.QtGui import QImage
from dataclasses import dataclass
from typing import Tuple
from injector import singleton, inject
import numpy as np

@dataclass
class RGBColorStats:
    pixel_count: int
    avg_r: float
    avg_g: float
    avg_b: float
    avg_white: float
    r_sd: float
    g_sd: float
    b_sd: float
    white_sd: float

@singleton
class ImageController:
    @inject
    def __init__(self):
        pass

    def calculate_region_rgb_color_stats(
        self,
        image: QImage,
        region: Tuple[int, int, int, int]
    ) -> RGBColorStats:
        """
        Calculate RGB and white color statistics for a specific region in an image
        
        Args:
            image: QImage to analyze
            region: Tuple of (x1, y1, x2, y2) coordinates
            
        Returns:
            RGBColorStats object containing RGB and white averages and standard deviations
        """
        x1, y1, x2, y2 = region
        
        # Initialize variables for calculation
        r_sum = g_sum = b_sum = white_sum = 0
        r_values = []
        g_values = []
        b_values = []
        white_values = []
        pixel_count = 0

        # Calculate sums and collect values
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                if x < 0 or y < 0 or x >= image.width() or y >= image.height():
                    continue
                    
                pixel = image.pixel(x, y)
                r = (pixel >> 16) & 0xFF
                g = (pixel >> 8) & 0xFF
                b = pixel & 0xFF
                
                r_sum += r
                g_sum += g
                b_sum += b
                
                # Calculate white value
                white_value = (r + g + b) / 3
                white_sum += white_value
                
                # Store values for SD calculation
                r_values.append(r)
                g_values.append(g)
                b_values.append(b)
                white_values.append(white_value)
                pixel_count += 1

        if pixel_count == 0:
            return RGBColorStats(0, 0, 0, 0, 0, 0, 0, 0, 0)

        # Calculate averages
        avg_r = r_sum / pixel_count
        avg_g = g_sum / pixel_count
        avg_b = b_sum / pixel_count
        avg_white = white_sum / pixel_count

        # Calculate standard deviations
        r_squared_diff_sum = sum((x - avg_r) ** 2 for x in r_values)
        g_squared_diff_sum = sum((x - avg_g) ** 2 for x in g_values)
        b_squared_diff_sum = sum((x - avg_b) ** 2 for x in b_values)
        white_squared_diff_sum = sum((x - avg_white) ** 2 for x in white_values)
        
        r_sd = (r_squared_diff_sum / pixel_count) ** 0.5
        g_sd = (g_squared_diff_sum / pixel_count) ** 0.5
        b_sd = (b_squared_diff_sum / pixel_count) ** 0.5
        white_sd = (white_squared_diff_sum / pixel_count) ** 0.5

        return RGBColorStats(
            pixel_count=pixel_count,
            avg_r=avg_r,
            avg_g=avg_g,
            avg_b=avg_b,
            avg_white=avg_white,
            r_sd=r_sd,
            g_sd=g_sd,
            b_sd=b_sd,
            white_sd=white_sd
        )

    def apply_region_rgb_color_stats(
        self,
        image: QImage,
        region: Tuple[int, int, int, int],
        color_stats: RGBColorStats,
        source_color_stats: RGBColorStats
    ) -> QImage:
        """
        Apply color transformation to match target color statistics in the specified region
        
        Args:
            image: QImage to modify
            region: Tuple of (x1, y1, x2, y2) coordinates
            color_stats: Current color statistics of the region
            target_color_stats: Target color statistics to match
            
        Returns:
            Modified QImage (note: the input image is also modified in-place)
            
        Note:
            After calling this function, to update the UI:
            1. Convert the QImage to QPixmap: original_pixmap = QPixmap.fromImage(image)
            2. Update your QLabel or other widget that displays the pixmap
            3. Call update() or repaint() on the widget to refresh the display
        """
        x1, y1, x2, y2 = region
        
        # For each color channel, calculate scaling and offset factors
        def transform_value(value: float, curr_avg: float, curr_sd: float, 
                        target_avg: float, target_sd: float) -> float:
            if curr_sd == 0:
                return target_avg
            # Scale the deviation from mean by the ratio of standard deviations
            scaled_deviation = (value - curr_avg) * (target_sd / curr_sd)
            # Center around the target mean
            return scaled_deviation + target_avg
        
        # Process each pixel in the region
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                if x < 0 or y < 0 or x >= image.width() or y >= image.height():
                    continue
                    
                pixel = image.pixel(x, y)
                r = (pixel >> 16) & 0xFF
                g = (pixel >> 8) & 0xFF
                b = pixel & 0xFF
                
                # Transform each color channel
                new_r = transform_value(r, color_stats.avg_r, color_stats.r_sd,
                                    source_color_stats.avg_r, source_color_stats.r_sd)
                new_g = transform_value(g, color_stats.avg_g, color_stats.g_sd,
                                    source_color_stats.avg_g, source_color_stats.g_sd)
                new_b = transform_value(b, color_stats.avg_b, color_stats.b_sd,
                                    source_color_stats.avg_b, source_color_stats.b_sd)
                
                # Clamp values to valid range [0, 255]
                new_r = max(0, min(255, round(new_r)))
                new_g = max(0, min(255, round(new_g)))
                new_b = max(0, min(255, round(new_b)))
                
                # Create new pixel value and set it
                new_pixel = (new_r << 16) | (new_g << 8) | new_b
                image.setPixel(x, y, new_pixel)

        return image 


    def apply_region_lighting_transfer(
        self,
        target_image: QImage,
        reference_image: QImage,
        region: Tuple[int, int, int, int],
    ) -> QImage:
        """
        Transfer lighting from reference image to target image using a two-step approach:
        1. Global color shift using RGB color statistics
        2. Local color transfer with smooth interpolation
        
        Args:
            target_image: QImage to modify
            reference_image: QImage to copy lighting from
            region: Tuple of (x1, y1, x2, y2) coordinates
            
        Returns:
            Modified QImage with transferred lighting
        """
        x1, y1, x2, y2 = region
        
        # Step 1: Apply global color shift
        target_stats = self.calculate_region_rgb_color_stats(target_image, region)
        ref_stats = self.calculate_region_rgb_color_stats(reference_image, region)
        
        # Apply global color shift first
        target_image = self.apply_region_rgb_color_stats(
            target_image, region, target_stats, ref_stats)
        
        # Step 2: Apply local color transfer
        window_size = 32  # Size of local window
        overlap = window_size // 2  # Overlap between windows
        
        # Create accumulator arrays for color values and weights
        width = x2 - x1 + 1
        height = y2 - y1 + 1
        acc_r = [[0.0] * width for _ in range(height)]
        acc_g = [[0.0] * width for _ in range(height)]
        acc_b = [[0.0] * width for _ in range(height)]
        acc_weights = [[0.0] * width for _ in range(height)]
        
        def create_weight_matrix(size):
            center = size // 2
            matrix = []
            for i in range(size):
                for j in range(size):
                    # Use smoother Gaussian weight
                    dx = (j - center) / center
                    dy = (i - center) / center
                    # Gaussian function: exp(-(x² + y²)/(2σ²))
                    weight = max(0, np.exp(-(dx*dx + dy*dy)/0.5))
                    matrix.append(weight)
            return matrix
        
        weights = create_weight_matrix(window_size)
        
        # Process image in overlapping windows
        for y in range(y1, y2 + 1, overlap):
            for x in range(x1, x2 + 1, overlap):
                # Define local window boundaries
                local_x1 = max(x1, x - window_size // 2)
                local_y1 = max(y1, y - window_size // 2)
                local_x2 = min(x2, x + window_size // 2)
                local_y2 = min(y2, y + window_size // 2)
                local_region = (local_x1, local_y1, local_x2, local_y2)
                
                # Calculate local statistics
                local_target_stats = self.calculate_region_rgb_color_stats(
                    target_image, local_region)
                local_ref_stats = self.calculate_region_rgb_color_stats(
                    reference_image, local_region)
                
                if local_target_stats.pixel_count == 0:
                    continue
                    
                # Process each pixel in the local window
                for ly in range(local_y1, local_y2 + 1):
                    for lx in range(local_x1, local_x2 + 1):
                        if (lx < 0 or ly < 0 or 
                            lx >= target_image.width() or 
                            ly >= target_image.height()):
                            continue
                        
                        # Calculate array indices
                        arr_x = lx - x1
                        arr_y = ly - y1
                        
                        # Calculate weight based on position in window
                        wx = lx - local_x1
                        wy = ly - local_y1
                        if wx >= window_size or wy >= window_size:
                            continue
                        weight = weights[wy * window_size + wx]
                        
                        pixel = target_image.pixel(lx, ly)
                        r = (pixel >> 16) & 0xFF
                        g = (pixel >> 8) & 0xFF
                        b = pixel & 0xFF
                        
                        # Transform colors using local statistics
                        def transform_value(value: float, curr_avg: float, curr_sd: float,
                                         target_avg: float, target_sd: float) -> float:
                            if curr_sd == 0:
                                return target_avg
                            scaled_deviation = (value - curr_avg) * (target_sd / curr_sd)
                            return scaled_deviation + target_avg
                        
                        # Calculate transformed colors
                        new_r = transform_value(r, local_target_stats.avg_r, 
                                             local_target_stats.r_sd,
                                             local_ref_stats.avg_r, 
                                             local_ref_stats.r_sd)
                        new_g = transform_value(g, local_target_stats.avg_g, 
                                             local_target_stats.g_sd,
                                             local_ref_stats.avg_g, 
                                             local_ref_stats.g_sd)
                        new_b = transform_value(b, local_target_stats.avg_b, 
                                             local_target_stats.b_sd,
                                             local_ref_stats.avg_b, 
                                             local_ref_stats.b_sd)
                        
                        # Accumulate weighted colors and weights
                        acc_r[arr_y][arr_x] += new_r * weight
                        acc_g[arr_y][arr_x] += new_g * weight
                        acc_b[arr_y][arr_x] += new_b * weight
                        acc_weights[arr_y][arr_x] += weight
        
        # Apply accumulated colors with normalization
        for y in range(height):
            for x in range(width):
                px = x + x1
                py = y + y1
                
                if px >= target_image.width() or py >= target_image.height():
                    continue
                    
                weight = acc_weights[y][x]
                if weight > 0:
                    # Normalize by total weight
                    final_r = int(max(0, min(255, acc_r[y][x] / weight)))
                    final_g = int(max(0, min(255, acc_g[y][x] / weight)))
                    final_b = int(max(0, min(255, acc_b[y][x] / weight)))
                    
                    new_pixel = (final_r << 16) | (final_g << 8) | final_b
                    target_image.setPixel(px, py, new_pixel)
        
        return target_image
