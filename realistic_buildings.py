# Realistic building drawing code - Copy this to replace the draw_background_scenery function

def draw_background_scenery(screen, camera_offset):
    """Draw realistic city background with detailed buildings"""
    
    # Sky with smooth gradient
    for i in range(SCREEN_HEIGHT // 2):
        ratio = i / (SCREEN_HEIGHT // 2)
        r = int(135 + ratio * 50)
        g = int(206 - ratio * 30)
        b = 250
        pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
    
    # Ground - smooth grass gradient
    for i in range(SCREEN_HEIGHT // 2, SCREEN_HEIGHT):
        ratio = (i - SCREEN_HEIGHT // 2) / (SCREEN_HEIGHT // 2)
        shade = int(60 + ratio * 40)
        pygame.draw.line(screen, (shade, int(160 + ratio * 20), shade), (0, i), (SCREEN_WIDTH, i))
    
    # Calculate scroll offset with smoother parallax
    scroll_offset = int(camera_offset * 0.3) % 200
    
    # Helper function to draw realistic building with shadows and details
    def draw_realistic_building(x, y, width, height, main_color, building_style):
        if y > SCREEN_HEIGHT or y + height < 0:
            return
            
        # Shadow on right side for depth
        shadow_color = tuple(max(0, c - 40) for c in main_color)
        pygame.draw.rect(screen, shadow_color, (x + width - 15, y, 15, height))
        
        # Main building body
        pygame.draw.rect(screen, main_color, (x, y, width - 15, height))
        
        # Top highlight for 3D effect
        highlight_color = tuple(min(255, c + 30) for c in main_color)
        pygame.draw.rect(screen, highlight_color, (x, y, width - 15, 8))
        
        if building_style == "office":
            # Modern office building with grid windows
            window_cols = 8
            window_rows = max(5, height // 35)
            window_w = (width - 30) // (window_cols + 1)
            window_h = 16
            
            for row in range(window_rows):
                for col in range(window_cols):
                    wx = x + 10 + col * (window_w + 3)
                    wy = y + 15 + row * (window_h + 8)
                    if wy + window_h < y + height - 5:
                        # Realistic glass effect - gradient windows
                        for i in range(window_h):
                            brightness = 200 - i * 3
                            pygame.draw.line(screen, (brightness, brightness, min(255, brightness + 30)), 
                                           (wx, wy + i), (wx + window_w, wy + i))
                        pygame.draw.rect(screen, (40, 40, 50), (wx, wy, window_w, window_h), 1)
                        
        elif building_style == "apartment":
            # Residential building with balconies
            floor_height = 30
            floors = max(4, height // floor_height)
            
            for floor in range(floors):
                floor_y = y + 10 + floor * floor_height
                if floor_y + 25 < y + height:
                    # Balcony railing
                    pygame.draw.rect(screen, tuple(max(0, c - 20) for c in main_color), 
                                   (x + 5, floor_y + 18, width - 25, 4))
                    
                    # Windows on each floor
                    for window_x in [x + 15, x + width//2 - 15, x + width - 55]:
                        # Window with frame
                        pygame.draw.rect(screen, (255, 255, 200), (window_x, floor_y, 25, 18))
                        pygame.draw.rect(screen, (60, 60, 70), (window_x, floor_y, 25, 18), 2)
                        # Window cross
                        pygame.draw.line(screen, (60, 60, 70), (window_x + 12, floor_y), 
                                       (window_x + 12, floor_y + 18), 1)
                        
        elif building_style == "tower":
            # Glass tower with reflective panels
            panel_width = width - 20
            panel_height = 40
            
            for panel_y in range(y, y + height - panel_height, panel_height):
                if panel_y > y and panel_y + panel_height < y + height:
                    # Reflective glass panels
                    for i in range(panel_height):
                        brightness = 100 + abs(20 - i) * 3
                        color = (main_color[0] // 3 + brightness, 
                                main_color[1] // 3 + brightness, 
                                main_color[2] // 3 + brightness)
                        pygame.draw.line(screen, color, (x + 5, panel_y + i), 
                                       (x + panel_width - 5, panel_y + i))
                    
                    # Panel separators
                    pygame.draw.line(screen, tuple(max(0, c - 60) for c in main_color), 
                                   (x + 5, panel_y), (x + panel_width - 5, panel_y), 2)
                    
        elif building_style == "house":
            # Residential house with detailed roof
            house_width = width - 40
            house_height = height - 40
            house_x = x + 20
            house_y = y + 40
            
            # House body
            pygame.draw.rect(screen, main_color, (house_x, house_y, house_width, house_height))
            
            # Pitched roof with shingles
            roof_points = [(house_x - 10, house_y), (house_x + house_width//2, y + 5), 
                          (house_x + house_width + 10, house_y)]
            pygame.draw.polygon(screen, (160, 60, 50), roof_points)
            
            # Roof shading
            for i in range(0, house_width + 20, 8):
                pygame.draw.line(screen, (140, 50, 40), 
                               (house_x - 10 + i, house_y), 
                               (house_x - 10 + i//2, y + 5 + i//4), 1)
            
            # Chimney
            pygame.draw.rect(screen, (120, 50, 40), (house_x + house_width - 30, y + 15, 15, 30))
            
            # Door
            pygame.draw.rect(screen, (80, 50, 30), (house_x + 15, house_y + house_height - 35, 25, 35))
            pygame.draw.circle(screen, (200, 180, 0), (house_x + 35, house_y + house_height - 18), 2)
            
            # Windows with frames
            window_positions = [(house_x + 50, house_y + 20), (house_x + house_width - 70, house_y + 20)]
            for wx, wy in window_positions:
                pygame.draw.rect(screen, (150, 200, 250), (wx, wy, 30, 25))
                pygame.draw.rect(screen, (80, 60, 50), (wx, wy, 30, 25), 2)
                pygame.draw.line(screen, (80, 60, 50), (wx + 15, wy), (wx + 15, wy + 25), 2)
                pygame.draw.line(screen, (80, 60, 50), (wx, wy + 12), (wx + 30, wy + 12), 2)
        
        # Building outline for definition
        pygame.draw.rect(screen, tuple(max(0, c - 50) for c in main_color), 
                        (x, y, width, height), 2)
    
    # LEFT SIDE Buildings
    left_x = 5
    building_spacing = 160
    
    for i in range(-2, (SCREEN_HEIGHT // building_spacing) + 3):
        y_pos = i * building_spacing - scroll_offset
        building_index = (i + int(camera_offset // building_spacing)) % 10
        
        if building_index == 0:
            draw_realistic_building(left_x, y_pos, 230, 180, (195, 75, 65), "office")
        elif building_index == 1:
            draw_realistic_building(left_x, y_pos, 230, 220, (55, 95, 175), "tower")
        elif building_index == 2:
            draw_realistic_building(left_x, y_pos, 230, 190, (210, 190, 95), "office")
        elif building_index == 3:
            draw_realistic_building(left_x, y_pos, 230, 200, (135, 95, 155), "apartment")
        elif building_index == 4:
            draw_realistic_building(left_x, y_pos, 230, 210, (230, 135, 65), "office")
        elif building_index == 5:
            draw_realistic_building(left_x, y_pos, 230, 185, (95, 175, 115), "apartment")
        elif building_index == 6:
            draw_realistic_building(left_x, y_pos, 230, 140, (235, 195, 175), "house")
        elif building_index == 7:
            draw_realistic_building(left_x, y_pos, 230, 195, (65, 175, 195), "tower")
        elif building_index == 8:
            draw_realistic_building(left_x, y_pos, 230, 205, (185, 85, 75), "apartment")
        else:
            draw_realistic_building(left_x, y_pos, 230, 175, (115, 145, 185), "office")
    
    # RIGHT SIDE Buildings
    right_x = SCREEN_WIDTH - 235
    
    for i in range(-2, (SCREEN_HEIGHT // building_spacing) + 3):
        y_pos = i * building_spacing - scroll_offset
        building_index = (i + int(camera_offset // building_spacing) + 5) % 10
        
        if building_index == 0:
            draw_realistic_building(right_x, y_pos, 230, 180, (195, 75, 65), "office")
        elif building_index == 1:
            draw_realistic_building(right_x, y_pos, 230, 220, (55, 95, 175), "tower")
        elif building_index == 2:
            draw_realistic_building(right_x, y_pos, 230, 190, (210, 190, 95), "office")
        elif building_index == 3:
            draw_realistic_building(right_x, y_pos, 230, 200, (135, 95, 155), "apartment")
        elif building_index == 4:
            draw_realistic_building(right_x, y_pos, 230, 210, (230, 135, 65), "office")
        elif building_index == 5:
            draw_realistic_building(right_x, y_pos, 230, 185, (95, 175, 115), "apartment")
        elif building_index == 6:
            draw_realistic_building(right_x, y_pos, 230, 140, (235, 195, 175), "house")
        elif building_index == 7:
            draw_realistic_building(right_x, y_pos, 230, 195, (65, 175, 195), "tower")
        elif building_index == 8:
            draw_realistic_building(right_x, y_pos, 230, 205, (185, 85, 75), "apartment")
        else:
            draw_realistic_building(right_x, y_pos, 230, 175, (115, 145, 185), "office")
    
    # Draw curbs (edges between sidewalk and road)
    pygame.draw.rect(screen, (100, 100, 100), (ROAD_X - 10, 0, 10, SCREEN_HEIGHT))
    pygame.draw.rect(screen, (100, 100, 100), (ROAD_X + ROAD_WIDTH, 0, 10, SCREEN_HEIGHT))
    
    # Street lamps along the road edges
    lamp_spacing = 100
    lamp_offset = int(camera_offset * 0.5) % lamp_spacing
    
    for i in range(-lamp_spacing, SCREEN_HEIGHT + lamp_spacing, lamp_spacing):
        lamp_y = i - lamp_offset
        # Left side lamps
        pygame.draw.rect(screen, (80, 80, 80), (ROAD_X - 45, lamp_y, 6, 60))
        pygame.draw.circle(screen, (255, 255, 200), (ROAD_X - 42, lamp_y), 12)
        pygame.draw.circle(screen, (255, 230, 150), (ROAD_X - 42, lamp_y), 8)
        
        # Right side lamps
        pygame.draw.rect(screen, (80, 80, 80), (ROAD_X + ROAD_WIDTH + 39, lamp_y, 6, 60))
        pygame.draw.circle(screen, (255, 255, 200), (ROAD_X + ROAD_WIDTH + 42, lamp_y), 12)
        pygame.draw.circle(screen, (255, 230, 150), (ROAD_X + ROAD_WIDTH + 42, lamp_y), 8)
