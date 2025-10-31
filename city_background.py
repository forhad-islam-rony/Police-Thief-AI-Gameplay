"""
Enhanced script to create a seamless tileable city background for the racing game.
This creates a vibrant, colorful city scene that tiles perfectly vertically.
"""
import pygame
import random

pygame.init()

# Create a large city background image (taller for better tiling)
width = 1500
height = 1400  # Make it taller so we can tile it seamlessly

surface = pygame.Surface((width, height))

# Sky with bright gradient (fills entire height for seamless tiling)
for y in range(height):
    # Cycle the gradient so top and bottom match
    normalized_y = (y / height)
    color_val = int(135 + abs(math.sin(normalized_y * 3.14159)) * 70)
    sky_blue = int(206 + abs(math.cos(normalized_y * 3.14159)) * 44)
    pygame.draw.line(surface, (color_val, sky_blue, 250), (0, y), (width, y))

# Add white fluffy clouds distributed throughout
import math
num_clouds = 30
for i in range(num_clouds):
    cx = random.randint(50, width - 50)
    cy = int((i / num_clouds) * height)
    radius = random.randint(35, 45)
    
    for j in range(5):
        offset_x = j * 18 - 36
        r = radius + random.randint(-5, 5) if j > 0 else radius
        pygame.draw.circle(surface, (255, 255, 255, 200), (cx + offset_x, cy), r)

# Ground/grass - vibrant green (appears periodically for tiling)
ground_height = 250
for section in range(0, height, ground_height * 2):
    pygame.draw.rect(surface, (80, 180, 80), (0, section + ground_height // 2, width, ground_height))
    
    # Add grass variation
    for i in range(0, width, 80):
        pygame.draw.rect(surface, (65, 165, 65), (i, section + ground_height // 2, 40, ground_height))

# Function to draw a building with consistent style
def draw_building(surf, x, y, w, h, color, windows_lit_ratio=0.6):
    """Draw a building with windows"""
    # Main body
    pygame.draw.rect(surf, color, (x, y, w, h))
    
    # Darker side for depth
    shadow_color = tuple(max(0, c - 20) for c in color)
    pygame.draw.rect(surf, shadow_color, (x + w - 15, y, 15, h))
    
    # Windows
    window_width = 8
    window_height = 10
    spacing_x = 16
    spacing_y = 18
    
    for wx in range(int(x + 12), int(x + w - 20), spacing_x):
        for wy in range(int(y + 15), int(y + h - 15), spacing_y):
            # Deterministic window lighting
            if ((wx + wy) % 100) < (windows_lit_ratio * 100):
                pygame.draw.rect(surf, (255, 250, 180), (wx, wy, window_width, window_height))
            else:
                pygame.draw.rect(surf, (25, 30, 40), (wx, wy, window_width, window_height))
    
    # Building outline
    pygame.draw.rect(surf, (40, 45, 55), (x, y, w, h), 3)

# Create building patterns that repeat
def create_building_row(y_position):
    """Create a row of buildings at given y position"""
    buildings = [
        # Left side buildings (0 to 750)
        (40, y_position, 80, 200, (70, 80, 100)),
        (140, y_position + 30, 75, 170, (85, 70, 95)),
        (235, y_position + 10, 90, 190, (60, 85, 110)),
        (345, y_position + 40, 70, 160, (90, 75, 85)),
        (435, y_position + 20, 85, 180, (70, 90, 95)),
        (540, y_position, 95, 210, (80, 70, 105)),
        (655, y_position + 35, 75, 165, (75, 85, 90)),
        
        # Right side buildings (750 to 1500)
        (770, y_position + 15, 90, 185, (85, 75, 100)),
        (880, y_position, 80, 200, (70, 90, 95)),
        (980, y_position + 25, 85, 175, (90, 80, 85)),
        (1085, y_position + 10, 75, 190, (65, 75, 110)),
        (1180, y_position + 40, 90, 160, (80, 85, 95)),
        (1290, y_position, 85, 210, (75, 70, 100)),
        (1395, y_position + 30, 80, 170, (85, 90, 90)),
    ]
    
    for x, y, w, h, color in buildings:
        draw_building(surface, x, y, w, h, color, windows_lit_ratio=0.65)

# Draw buildings at multiple positions for seamless vertical tiling
for row_y in [50, 400, 750, 1100]:
    create_building_row(row_y)

# Add colorful featured buildings at key positions
featured_buildings = [
    # (x, y, width, height, color, style)
    (530, 150, 130, 280, (55, 75, 110), 'glass'),
    (530, 600, 130, 280, (55, 75, 110), 'glass'),
    (530, 1050, 130, 280, (55, 75, 110), 'glass'),
]

for x, y, w, h, base_color, style in featured_buildings:
    pygame.draw.rect(surface, base_color, (x, y, w, h))
    
    if style == 'glass':
        # Glass building with blue tint
        for wx in range(x + 10, x + w - 10, 15):
            for wy in range(y + 20, y + h - 20, 18):
                if (wx + wy) % 35 < 28:
                    pygame.draw.rect(surface, (180, 210, 255), (wx, wy, 11, 14))
                else:
                    pygame.draw.rect(surface, (30, 45, 70), (wx, wy, 11, 14))
        
        # Reflection
        pygame.draw.rect(surface, (100, 140, 200), (x + 5, y + 10, 25, 60))
    
    pygame.draw.rect(surface, (40, 45, 55), (x, y, w, h), 3)

# Add houses/shops at ground level positions
def draw_house(surf, x, y, wall_color, roof_color):
    """Draw a small house"""
    w = 90
    h = 75
    
    # House body
    pygame.draw.rect(surf, wall_color, (x, y, w, h))
    pygame.draw.rect(surf, (60, 60, 70), (x, y, w, h), 2)
    
    # Roof
    roof_points = [(x - 5, y), (x + w // 2, y - 35), (x + w + 5, y)]
    pygame.draw.polygon(surf, roof_color, roof_points)
    pygame.draw.lines(surf, (50, 50, 60), False, roof_points + [roof_points[0]], 2)
    
    # Window
    pygame.draw.rect(surf, (180, 210, 240), (x + w - 30, y + 18, 20, 24))
    pygame.draw.rect(surf, (80, 90, 100), (x + w - 30, y + 18, 20, 24), 2)
    
    # Door
    pygame.draw.rect(surf, (150, 90, 60), (x + 12, y + h - 35, 22, 35))
    pygame.draw.rect(surf, (100, 60, 40), (x + 12, y + h - 35, 22, 35), 2)

# House colors
house_colors = [
    ((240, 220, 210), (180, 70, 60)),
    ((210, 230, 240), (80, 120, 180)),
    ((255, 250, 230), (140, 180, 100)),
    ((250, 240, 220), (200, 100, 70)),
    ((235, 220, 240), (150, 100, 180)),
]

# Draw houses at multiple ground level positions for tiling
for base_y in [300, 700, 1100]:
    for i, (wall_c, roof_c) in enumerate(house_colors):
        x_pos = 20 + i * 100
        draw_house(surface, x_pos, base_y, wall_c, roof_c)
        draw_house(surface, 800 + x_pos, base_y, wall_c, roof_c)

# Add trees distributed throughout
def draw_tree(surf, x, y, tree_color):
    """Draw a tree"""
    # Trunk
    pygame.draw.rect(surf, (110, 75, 50), (x - 6, y, 12, 40))
    
    # Foliage
    light_green = tuple(min(c + 20, 255) for c in tree_color)
    dark_green = tuple(max(c - 15, 0) for c in tree_color)
    
    pygame.draw.circle(surf, tree_color, (x, y - 8), 24)
    pygame.draw.circle(surf, dark_green, (x - 14, y + 4), 20)
    pygame.draw.circle(surf, light_green, (x + 14, y + 4), 20)

# Trees at various heights for tiling
tree_colors = [(70, 160, 70), (80, 150, 75), (65, 155, 65)]
for base_y in [290, 690, 1090]:
    for i in range(15):
        x_pos = 50 + i * 100
        tree_c = tree_colors[i % len(tree_colors)]
        draw_tree(surface, x_pos, base_y, tree_c)

# Add sidewalk/curb at regular intervals
curb_color = (220, 55, 55)
sidewalk_color = (190, 195, 200)

for y in range(0, height, 350):
    # Sidewalk
    pygame.draw.rect(surface, sidewalk_color, (0, y + 270, width, 16))
    
    # Curb with pattern
    pygame.draw.rect(surface, curb_color, (0, y + 286, width, 12))
    for i in range(0, width, 30):
        pygame.draw.rect(surface, (255, 80, 80), (i, y + 286, 15, 12))

# Save the image
pygame.image.save(surface, "city_bg.png")
print(f"Enhanced seamless city background created: {width}x{height} pixels")
print("The image is designed to tile vertically for smooth scrolling!")

pygame.quit()