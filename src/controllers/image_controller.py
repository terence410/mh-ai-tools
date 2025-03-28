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
        Transfer lighting from reference image to target image using a tiled approach with overlap:
        1. Split image into 16x16 tiles with 8-pixel overlap
        2. For each tile, calculate and apply color statistics
        3. Blend overlapping regions using accumulated weights from all contributing tiles
        
        Args:
            target_image: QImage to modify
            reference_image: QImage to copy lighting from
            region: Tuple of (x1, y1, x2, y2) coordinates
            
        Returns:
            Modified QImage with transferred lighting
        """
        x1, y1, x2, y2 = region
        TILE_SIZE = 32
        OVERLAP = 16
        
        # Create a copy of the target image to work with
        result_image = target_image.copy()
        
        # Create weight and color accumulation buffers
        width = x2 - x1 + 1
        height = y2 - y1 + 1
        weight_buffer = np.zeros((height, width), dtype=np.float32)
        color_buffer = np.zeros((height, width, 3), dtype=np.float32)
        
        # First pass: accumulate weights and transformed colors
        for tile_y in range(y1, y2, OVERLAP):
            for tile_x in range(x1, x2, OVERLAP):
                # Calculate tile boundaries
                tile_x1 = tile_x
                tile_y1 = tile_y
                tile_x2 = min(tile_x + TILE_SIZE - 1, x2)
                tile_y2 = min(tile_y + TILE_SIZE - 1, y2)
                
                # Skip if tile is completely outside the region
                if tile_x1 >= x2 or tile_y1 >= y2:
                    continue
                
                # Calculate effective tile size for this tile
                effective_width = tile_x2 - tile_x1 + 1
                effective_height = tile_y2 - tile_y1 + 1
                
                # Calculate color statistics for this tile
                tile_region = (tile_x1, tile_y1, tile_x2, tile_y2)
                target_stats = self.calculate_region_rgb_color_stats(target_image, tile_region)
                ref_stats = self.calculate_region_rgb_color_stats(reference_image, tile_region)
                
                # Process each pixel in the tile
                for y in range(tile_y1, tile_y2 + 1):
                    for x in range(tile_x1, tile_x2 + 1):
                        # Calculate relative position in the region
                        rel_x = x - x1
                        rel_y = y - y1
                        
                        # Calculate distance from tile center, adjusted for partial tiles
                        tile_center_x = tile_x1 + effective_width / 2
                        tile_center_y = tile_y1 + effective_height / 2
                        dx = abs(x - tile_center_x)
                        dy = abs(y - tile_center_y)
                        
                        # Calculate weight based on distance from center
                        # Use the effective tile size for max_dist
                        max_dist_x = effective_width / 2
                        max_dist_y = effective_height / 2
                        
                        # Calculate normalized distances
                        norm_dx = dx / max_dist_x
                        norm_dy = dy / max_dist_y
                        
                        # Use the maximum normalized distance for the weight
                        # This ensures smooth transitions even for rectangular tiles
                        norm_dist = max(norm_dx, norm_dy)
                        
                        if norm_dist >= 1.0:
                            weight = 0
                        else:
                            # Smooth falloff using cosine interpolation
                            weight = 0.5 * (1 + np.cos(norm_dist * np.pi))
                        
                        # Get original pixel
                        pixel = target_image.pixel(x, y)
                        r = (pixel >> 16) & 0xFF
                        g = (pixel >> 8) & 0xFF
                        b = pixel & 0xFF
                        
                        # Transform color values
                        def transform_value(value: float, curr_avg: float, curr_sd: float, 
                                        target_avg: float, target_sd: float) -> float:
                            if curr_sd == 0:
                                return target_avg
                            scaled_deviation = (value - curr_avg) * (target_sd / curr_sd)
                            return scaled_deviation + target_avg
                        
                        # Calculate transformed values
                        new_r = transform_value(r, target_stats.avg_r, target_stats.r_sd,
                                            ref_stats.avg_r, ref_stats.r_sd)
                        new_g = transform_value(g, target_stats.avg_g, target_stats.g_sd,
                                            ref_stats.avg_g, ref_stats.g_sd)
                        new_b = transform_value(b, target_stats.avg_b, target_stats.b_sd,
                                            ref_stats.avg_b, ref_stats.b_sd)
                        
                        # Clamp values
                        new_r = max(0, min(255, round(new_r)))
                        new_g = max(0, min(255, round(new_g)))
                        new_b = max(0, min(255, round(new_b)))
                        
                        # Accumulate weights and colors
                        weight_buffer[rel_y, rel_x] += weight
                        color_buffer[rel_y, rel_x, 0] += new_r * weight
                        color_buffer[rel_y, rel_x, 1] += new_g * weight
                        color_buffer[rel_y, rel_x, 2] += new_b * weight
        
        # Second pass: normalize and apply final colors
        for y in range(height):
            for x in range(width):
                if weight_buffer[y, x] > 0:
                    # Normalize colors by accumulated weight
                    final_r = round(color_buffer[y, x, 0] / weight_buffer[y, x])
                    final_g = round(color_buffer[y, x, 1] / weight_buffer[y, x])
                    final_b = round(color_buffer[y, x, 2] / weight_buffer[y, x])
                    
                    # Clamp values
                    final_r = max(0, min(255, final_r))
                    final_g = max(0, min(255, final_g))
                    final_b = max(0, min(255, final_b))
                    
                    # Set final pixel
                    final_pixel = (final_r << 16) | (final_g << 8) | final_b
                    result_image.setPixel(x + x1, y + y1, final_pixel)
        
        return result_image
