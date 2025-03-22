from PyQt6.QtGui import QImage
from dataclasses import dataclass
from typing import Tuple

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

def calculate_region_rgb_color_stats(
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
    image: QImage,
    region: Tuple[int, int, int, int],
    color_stats: RGBColorStats,
    target_color_stats: RGBColorStats
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
                                  target_color_stats.avg_r, target_color_stats.r_sd)
            new_g = transform_value(g, color_stats.avg_g, color_stats.g_sd,
                                  target_color_stats.avg_g, target_color_stats.g_sd)
            new_b = transform_value(b, color_stats.avg_b, color_stats.b_sd,
                                  target_color_stats.avg_b, target_color_stats.b_sd)
            
            # Clamp values to valid range [0, 255]
            new_r = max(0, min(255, round(new_r)))
            new_g = max(0, min(255, round(new_g)))
            new_b = max(0, min(255, round(new_b)))
            
            # Create new pixel value and set it
            new_pixel = (new_r << 16) | (new_g << 8) | new_b
            image.setPixel(x, y, new_pixel)

    return image
