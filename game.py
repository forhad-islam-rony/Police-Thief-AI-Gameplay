import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🏁 Road Rush: Police Chase")

# No image loading needed - we'll draw directly

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
GREEN = (34, 139, 34)
YELLOW = (255, 215, 0)
RED = (220, 20, 60)
BLUE = (30, 144, 255)
ORANGE = (255, 140, 0)
ROAD_GRAY = (60, 60, 60)
GRASS_GREEN = (50, 150, 50)
SKY_BLUE = (135, 206, 250)
DARK_GREEN = (34, 100, 34)
LIGHT_GRAY = (150, 150, 150)
BROWN = (139, 90, 43)
PURPLE = (138, 43, 226)

# Game settings
FPS = 60
ROAD_WIDTH = 500
ROAD_X = (SCREEN_WIDTH - ROAD_WIDTH) // 2
FINISH_LINE_DISTANCE = 50000  # 50 KM track for extended gameplay
LANE_WIDTH = ROAD_WIDTH // 3

# CSP (Constraint Satisfaction Problem) Solver for AI Decision Making
class CSPDecisionMaker:
    """
    Advanced AI decision system using Constraint Satisfaction Problem algorithm.
    Makes optimal decisions by considering multiple constraints simultaneously.
    """
    
    def __init__(self):
        self.lane_positions = [
            ROAD_X + LANE_WIDTH // 2,
            ROAD_X + LANE_WIDTH + LANE_WIDTH // 2,
            ROAD_X + 2 * LANE_WIDTH + LANE_WIDTH // 2
        ]
    
    def solve_lane_decision(self, vehicle, traffic_cars, powerups, opponent=None, 
                           ghost_mode=False, is_police=False):
        """
        CSP solver that returns optimal lane and speed decision.
        
        Variables:
        - target_lane: 0, 1, or 2
        - speed_action: 'accelerate', 'maintain', 'brake'
        
        Constraints:
        - Safety: avoid imminent collisions
        - Distance: maintain safe spacing
        - Objective: collect powerups (thief) or chase target (police)
        - Speed: appropriate for current situation
        """
        
        # Generate all possible actions (domain)
        actions = []
        for lane_idx in range(3):
            for speed_action in ['accelerate', 'maintain', 'brake']:
                actions.append({
                    'lane': lane_idx,
                    'lane_x': self.lane_positions[lane_idx],
                    'speed_action': speed_action
                })
        
        # Filter actions based on hard constraints (must satisfy)
        valid_actions = []
        for action in actions:
            if self._satisfies_hard_constraints(action, vehicle, traffic_cars, 
                                                ghost_mode, opponent, is_police):
                valid_actions.append(action)
        
        # If no valid actions (rare), allow current lane with brake
        if not valid_actions:
            current_lane = self._get_current_lane(vehicle.x)
            return {
                'lane': current_lane,
                'lane_x': self.lane_positions[current_lane],
                'speed_action': 'brake'
            }
        
        # Score remaining actions based on soft constraints (optimize)
        best_action = max(valid_actions, 
                         key=lambda a: self._calculate_utility_score(
                             a, vehicle, traffic_cars, powerups, opponent, is_police))
        
        return best_action
    
    def _satisfies_hard_constraints(self, action, vehicle, traffic_cars, 
                                    ghost_mode, opponent, is_police):
        """Check if action satisfies all mandatory constraints"""
        
        # Constraint 1: Safety - avoid immediate collisions
        if not ghost_mode:
            for car in traffic_cars:
                # Check if car is in target lane and dangerously close
                car_lane = self._get_current_lane(car.x)
                if car_lane == action['lane']:
                    distance_to_car = abs(car.distance - vehicle.distance)
                    lateral_distance = abs(car.x - action['lane_x'])
                    
                    # Hard constraint: don't move into occupied space
                    if distance_to_car < 120 and lateral_distance < 40:
                        return False
        
        # Constraint 2: Boundary - must stay on road
        if action['lane_x'] < ROAD_X + 35 or action['lane_x'] > ROAD_X + ROAD_WIDTH - 35:
            return False
        
        # Constraint 3: Physical limits - can't change lanes too quickly at high speed
        current_lane = self._get_current_lane(vehicle.x)
        lane_change_distance = abs(action['lane'] - current_lane)
        if lane_change_distance > 1 and vehicle.speed > 6:
            # Can't jump 2 lanes at high speed
            return False
        
        return True
    
    def _calculate_utility_score(self, action, vehicle, traffic_cars, 
                                 powerups, opponent, is_police):
        """Calculate utility score for an action (higher is better)"""
        score = 0.0
        
        if is_police:
            # Police objective: catch the thief
            score += self._score_police_pursuit(action, vehicle, opponent)
        else:
            # Thief objective: escape and collect powerups
            score += self._score_thief_escape(action, vehicle, opponent)
            score += self._score_powerup_collection(action, vehicle, powerups)
        
        # Common objectives
        score += self._score_traffic_clearance(action, vehicle, traffic_cars)
        score += self._score_speed_optimization(action, vehicle)
        score += self._score_lane_preference(action, vehicle)
        
        return score
    
    def _score_police_pursuit(self, action, vehicle, opponent):
        """Score based on how well action helps police catch thief"""
        if not opponent:
            return 0.0
        
        score = 0.0
        
        # Reward moving toward thief's lane
        thief_lane = self._get_current_lane(opponent.x)
        if action['lane'] == thief_lane:
            score += 50.0
        else:
            lane_distance = abs(action['lane'] - thief_lane)
            score -= lane_distance * 15.0
        
        # Reward closing distance
        distance_to_thief = abs(opponent.distance - vehicle.distance)
        if action['speed_action'] == 'accelerate' and distance_to_thief > 100:
            score += 30.0
        elif action['speed_action'] == 'maintain' and distance_to_thief < 100:
            score += 20.0
        
        # Reward intercepting path
        if opponent.distance > vehicle.distance and action['lane'] == thief_lane:
            score += 40.0  # Block escape route
        
        return score
    
    def _score_thief_escape(self, action, vehicle, opponent):
        """Score based on how well action helps thief escape police"""
        if not opponent:
            return 0.0
        
        score = 0.0
        
        # Reward staying away from police lane
        police_lane = self._get_current_lane(opponent.x)
        if action['lane'] != police_lane:
            score += 35.0
        else:
            score -= 25.0
        
        # Reward maintaining high speed when police is far
        distance_to_police = abs(opponent.distance - vehicle.distance)
        if distance_to_police > 200 and action['speed_action'] == 'accelerate':
            score += 25.0
        elif distance_to_police < 150:
            # Police close - prefer evasive maneuvering
            if action['lane'] != police_lane:
                score += 40.0
        
        # Reward being ahead
        if vehicle.distance > opponent.distance:
            score += 20.0
        
        return score
    
    def _score_powerup_collection(self, action, vehicle, powerups):
        """Score based on powerup collection opportunity"""
        score = 0.0
        
        for powerup in powerups:
            if powerup.collected:
                continue
            
            # Check if powerup matches vehicle type
            if vehicle.is_police and not powerup.for_police:
                continue  # Police ignores thief powerups
            if not vehicle.is_police and powerup.for_police:
                continue  # Thief ignores police powerups
            
            # Check if powerup is ahead and reachable
            distance_to_powerup = powerup.distance - vehicle.distance
            if 0 < distance_to_powerup < 600:
                powerup_lane = powerup.lane
                
                # High reward for moving to powerup lane
                if action['lane'] == powerup_lane:
                    proximity_bonus = max(0, 50 - distance_to_powerup / 10)
                    score += proximity_bonus
                    
                    # Extra reward for valuable powerups
                    if vehicle.is_police:
                        # Police power-up priorities
                        if powerup.power_type == 'emp':
                            score += 18.0  # High priority - disables thief
                        elif powerup.power_type == 'turbo':
                            score += 15.0
                        elif powerup.power_type == 'magnet':
                            score += 14.0
                        elif powerup.power_type == 'spike':
                            score += 12.0
                        elif powerup.power_type == 'roadblock':
                            score += 10.0
                    else:
                        # Thief power-up priorities
                        if powerup.power_type == 'freeze':
                            score += 15.0
                        elif powerup.power_type == 'shield':
                            score += 12.0
                        elif powerup.power_type == 'boost':
                            score += 10.0
        
        return score
    
    def _score_traffic_clearance(self, action, vehicle, traffic_cars):
        """Score based on traffic avoidance and clearance"""
        score = 0.0
        
        # Calculate clearance in target lane
        min_clearance = 1000.0
        traffic_ahead_count = 0
        
        for car in traffic_cars:
            car_lane = self._get_current_lane(car.x)
            if car_lane == action['lane']:
                distance_to_car = car.distance - vehicle.distance
                
                # Only consider cars ahead
                if 0 < distance_to_car < 400:
                    traffic_ahead_count += 1
                    min_clearance = min(min_clearance, distance_to_car)
        
        # Reward lanes with more clearance
        if min_clearance > 300:
            score += 30.0
        elif min_clearance > 200:
            score += 20.0
        elif min_clearance > 100:
            score += 10.0
        else:
            score -= 20.0  # Penalize crowded lanes
        
        # Penalize lanes with multiple cars
        score -= traffic_ahead_count * 8.0
        
        return score
    
    def _score_speed_optimization(self, action, vehicle):
        """Score based on optimal speed management"""
        score = 0.0
        
        # Generally prefer maintaining high speed
        if action['speed_action'] == 'accelerate' and vehicle.speed < vehicle.max_speed * 0.9:
            score += 15.0
        elif action['speed_action'] == 'maintain' and vehicle.speed > vehicle.max_speed * 0.7:
            score += 10.0
        elif action['speed_action'] == 'brake':
            score -= 5.0  # Slight penalty for braking
        
        return score
    
    def _score_lane_preference(self, action, vehicle):
        """Score based on strategic lane positioning"""
        score = 0.0
        
        # Slight preference for center lane (more options)
        if action['lane'] == 1:
            score += 5.0
        
        # Penalize excessive lane changes
        current_lane = self._get_current_lane(vehicle.x)
        if action['lane'] != current_lane:
            score -= 3.0  # Small penalty for lane change
        
        return score
    
    def _get_current_lane(self, x_position):
        """Determine which lane a given x position is in"""
        for i, lane_x in enumerate(self.lane_positions):
            if abs(x_position - lane_x) < LANE_WIDTH // 2:
                return i
        # Default to center lane if unclear
        return 1

# Particle system
particles = []

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(1, 4)
        self.color = color
        self.life = 30
        self.size = random.randint(2, 5)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.vy += 0.2
        
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / 30))
            color_with_alpha = (*self.color, alpha)
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color_with_alpha, (self.size, self.size), self.size)
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class PowerUp:
    """Collectible power-ups on the road"""
    def __init__(self, lane, distance, power_type, for_police=False):
        self.lane = lane
        self.distance = distance
        self.power_type = power_type
        self.for_police = for_police  # Police-exclusive power-ups
        self.width = 45
        self.height = 45
        self.collected = False
        self.rotation = 0
        
        # Power-up types and their properties
        # Thief power-ups
        self.types = {
            'freeze': {'color': (100, 200, 255), 'icon': '❄️', 'name': 'Freeze Police'},
            'boost': {'color': (255, 200, 0), 'icon': '⚡', 'name': 'Speed Boost'},
            'shield': {'color': (150, 255, 150), 'icon': '🛡️', 'name': 'Shield'},
            'ghost': {'color': (200, 150, 255), 'icon': '👻', 'name': 'Ghost Mode'},
            # Police-exclusive power-ups (red theme)
            'spike': {'color': (255, 50, 50), 'icon': '🔺', 'name': 'Spike Strip'},
            'emp': {'color': (255, 100, 255), 'icon': '⚡', 'name': 'EMP Blast'},
            'turbo': {'color': (255, 150, 0), 'icon': '🔥', 'name': 'Turbo Boost'},
            'roadblock': {'color': (200, 50, 50), 'icon': '🚧', 'name': 'Roadblock'},
            'magnet': {'color': (150, 150, 255), 'icon': '🧲', 'name': 'Magnetic Pull'}
        }
    
    def update(self, camera_offset):
        """Update power-up animation"""
        self.rotation = (self.rotation + 3) % 360
    
    def draw(self, screen, camera_offset):
        """Draw the power-up with fancy effects"""
        if self.collected:
            return
        
        # Calculate screen position
        lane_x = ROAD_X + self.lane * LANE_WIDTH + LANE_WIDTH // 2
        screen_y = SCREEN_HEIGHT // 2 - (self.distance - camera_offset)
        
        # Only draw if visible on screen
        if -100 < screen_y < SCREEN_HEIGHT + 100:
            props = self.types[self.power_type]
            
            # Floating animation
            float_offset = math.sin(pygame.time.get_ticks() / 300 + self.distance) * 8
            final_y = screen_y + float_offset
            
            # Pulsing glow effect (more intense for police powerups)
            pulse_speed = 300 if self.for_police else 400
            pulse = abs(math.sin(pygame.time.get_ticks() / pulse_speed)) * 20 + 15
            
            # Draw multiple glow layers
            for r in range(int(pulse), 0, -3):
                alpha = int(100 * (r / pulse))
                glow_surf = pygame.Surface((self.width + r*2, self.height + r*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*props['color'], alpha), 
                                 (self.width//2 + r, self.height//2 + r), self.width//2 + r)
                screen.blit(glow_surf, (int(lane_x - self.width//2 - r), int(final_y - self.height//2 - r)))
            
            # Main power-up circle (hexagon for police powerups)
            if self.for_police:
                # Draw hexagon for police powers
                points = []
                sides = 6
                for i in range(sides):
                    angle = (self.rotation + i * (360 / sides)) * math.pi / 180
                    x = lane_x + math.cos(angle) * (self.width//2)
                    y = final_y + math.sin(angle) * (self.height//2)
                    points.append((int(x), int(y)))
                pygame.draw.polygon(screen, props['color'], points)
                pygame.draw.polygon(screen, WHITE, points, 3)
            else:
                # Draw circle for thief powers
                pygame.draw.circle(screen, props['color'], (int(lane_x), int(final_y)), self.width//2)
            
            # Inner circle with gradient effect
            inner_color = tuple(min(255, c + 80) for c in props['color'])
            pygame.draw.circle(screen, inner_color, (int(lane_x), int(final_y)), self.width//2 - 5)
            
            # Draw icon
            font_icon = pygame.font.Font(None, 36)
            icon_text = font_icon.render(props['icon'], True, WHITE)
            icon_rect = icon_text.get_rect(center=(int(lane_x), int(final_y)))
            screen.blit(icon_text, icon_rect)
            
            # Rotating border (square for police, circle for thief)
            border_points = []
            segments = 4 if self.for_police else 8
            rotation_speed = 2 if self.for_police else 1
            for i in range(segments):
                angle = (self.rotation * rotation_speed + i * (360 / segments)) * math.pi / 180
                x = lane_x + math.cos(angle) * (self.width//2 + 8)
                y = final_y + math.sin(angle) * (self.height//2 + 8)
                border_points.append((int(x), int(y)))
            
            for i in range(len(border_points)):
                start = border_points[i]
                end = border_points[(i + 1) % len(border_points)]
                border_color = RED if self.for_police else WHITE
                pygame.draw.line(screen, border_color, start, end, 3)
    
    def check_collision(self, player_x, player_y, player_width, player_height, camera_offset):
        """Check if player collected this power-up"""
        if self.collected:
            return False
        
        lane_x = ROAD_X + self.lane * LANE_WIDTH + LANE_WIDTH // 2
        screen_y = SCREEN_HEIGHT // 2 - (self.distance - camera_offset)
        
        # Simple circle collision
        dist = math.sqrt((player_x - lane_x)**2 + (player_y - screen_y)**2)
        if dist < (self.width//2 + player_width//2):
            self.collected = True
            return True
        return False

class Vehicle:
    def __init__(self, x, y, color, is_player=False, is_police=False):
        self.x = x
        self.y = y
        self.color = color
        self.width = 50
        self.height = 90
        self.speed = 0
        self.max_speed = 8
        self.is_player = is_player
        self.is_police = is_police
        self.distance = 0
        self.wheel_rotation = 0
        
        # Power-up effects
        self.active_powerups = {}
        self.shield_active = False
        self.ghost_mode = False
        self.crashed = False
        self.crash_timer = 0
        self.crash_spin = 0
    
    def crash(self):
        """Handle vehicle crash"""
        self.crashed = True
        self.crash_timer = 60  # 1 second at 60 FPS
        self.crash_spin = random.choice([-15, 15])  # Spin direction
        self.speed = max(0, self.speed * 0.3)  # Reduce speed dramatically
        
    def update_crash(self):
        """Update crash state"""
        if self.crashed and self.crash_timer > 0:
            self.crash_timer -= 1
            if self.crash_timer == 0:
                self.crashed = False
                self.crash_spin = 0
    
    def ai_decision_csp(self, traffic_cars, powerups, opponent, ghost_mode, csp_solver):
        """
        Advanced AI decision making using CSP algorithm.
        Considers multiple constraints simultaneously for optimal decision.
        """
        if self.crashed:
            return
        
        # Use CSP solver to get optimal decision
        decision = csp_solver.solve_lane_decision(
            vehicle=self,
            traffic_cars=traffic_cars,
            powerups=powerups,
            opponent=opponent,
            ghost_mode=ghost_mode,
            is_police=self.is_police
        )
        
        # Execute the decision with smooth transitions
        target_x = decision['lane_x']
        speed_action = decision['speed_action']
        
        # Smooth steering towards target lane
        if abs(target_x - self.x) > 5:
            # Adaptive steering speed based on urgency and current speed
            steering_speed = 4 if self.speed > 6 else 5
            
            if target_x < self.x:
                self.x = max(ROAD_X + 35, self.x - steering_speed)
            else:
                self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
        
        # Execute speed action
        if not self.crashed:
            if speed_action == 'accelerate':
                self.speed = min(self.speed + 0.2, self.max_speed)
            elif speed_action == 'maintain':
                # Maintain current speed with slight drift toward max
                if self.speed < self.max_speed * 0.95:
                    self.speed = min(self.speed + 0.05, self.max_speed)
            elif speed_action == 'brake':
                self.speed = max(self.speed - 0.3, self.max_speed * 0.5)
    
    def ai_decision(self, traffic_cars, powerups, police_distance, camera_offset, ghost_mode):
        """
        Legacy AI decision making (kept for compatibility).
        Note: This is replaced by ai_decision_csp for better performance.
        """
        if self.crashed:
            return
        
        # Simple fallback logic
        target_speed = self.max_speed
        
        # Speed control
        if not self.crashed:
            if self.speed < target_speed:
                self.speed = min(self.speed + 0.15, target_speed)
            elif self.speed > target_speed:
                self.speed = max(self.speed - 0.1, target_speed * 0.7)
    
    def draw(self, screen, camera_offset):
        # Draw vehicle body with 3D effect
        # Calculate y position based on distance from camera
        y_pos = self.distance - camera_offset + SCREEN_HEIGHT // 2
        
        # Shadow
        shadow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 80), shadow_surface.get_rect())
        screen.blit(shadow_surface, (self.x - self.width//2 - 5, y_pos + self.height//2))
        
        # Shield effect (if active)
        if self.shield_active:
            pulse = abs(math.sin(pygame.time.get_ticks() / 200))
            shield_radius = int(self.width * 0.9 + pulse * 10)
            for i in range(3):
                alpha = int(80 - i * 20)
                shield_color = (150, 255, 150, alpha)
                shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(shield_surface, shield_color, (shield_radius, shield_radius), shield_radius - i * 5, 3)
                screen.blit(shield_surface, (self.x - shield_radius, y_pos - shield_radius))
        
        # Ghost mode effect (if active)
        if self.ghost_mode:
            # Make vehicle semi-transparent with ghostly aura
            ghost_pulse = abs(math.sin(pygame.time.get_ticks() / 150))
            for i in range(3):
                ghost_radius = int(self.width * 0.8 + ghost_pulse * 8 + i * 8)
                alpha = int(50 - i * 15)
                ghost_color = (200, 150, 255, alpha)
                ghost_surface = pygame.Surface((ghost_radius * 2, ghost_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(ghost_surface, ghost_color, (ghost_radius, ghost_radius), ghost_radius)
                screen.blit(ghost_surface, (self.x - ghost_radius, y_pos - ghost_radius))
        
        # Determine vehicle color (gray if crashed)
        vehicle_color = GRAY if self.crashed else self.color
        
        # Flash effect when crashed
        if self.crashed and (self.crash_timer // 5) % 2 == 0:
            vehicle_color = tuple(min(c + 100, 255) for c in vehicle_color)
        
        # Main body with gradient effect
        body_rect = pygame.Rect(self.x - self.width//2, y_pos - self.height//2, self.width, self.height)
        
        # Apply rotation if crashed
        if self.crashed and self.crash_timer > 0:
            # Create surface for rotation
            temp_surface = pygame.Surface((self.width + 40, self.height + 40), pygame.SRCALPHA)
            temp_rect = temp_surface.get_rect(center=(self.width // 2 + 20, self.height // 2 + 20))
            
            # Draw vehicle on temp surface
            draw_x = 20
            draw_y = 20
            pygame.draw.rect(temp_surface, vehicle_color, 
                           (draw_x, draw_y, self.width, self.height), border_radius=10)
            
            # Rotate the surface
            rotation_angle = self.crash_spin * (1 - self.crash_timer / 60)
            rotated_surface = pygame.transform.rotate(temp_surface, rotation_angle)
            rotated_rect = rotated_surface.get_rect(center=(self.x, y_pos))
            screen.blit(rotated_surface, rotated_rect)
            
            # Crash particles/sparks
            if self.crash_timer > 40:
                for i in range(3):
                    spark_x = self.x + random.randint(-20, 20)
                    spark_y = y_pos + random.randint(-20, 20)
                    pygame.draw.circle(screen, ORANGE, (int(spark_x), int(spark_y)), 
                                     random.randint(2, 5))
        else:
            # Normal drawing (no crash)
            # Draw body with multiple layers for depth
            pygame.draw.rect(screen, vehicle_color, body_rect, border_radius=10)
            
            # Highlight on top
            highlight_color = tuple(min(c + 50, 255) for c in vehicle_color)
            highlight_rect = pygame.Rect(self.x - self.width//2 + 5, y_pos - self.height//2 + 5, 
                                          self.width - 10, 15)
            pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=5)
            
            # Windshield with reflection
            windshield_color = (100, 200, 255, 200)
            windshield_surface = pygame.Surface((self.width - 12, 30), pygame.SRCALPHA)
            pygame.draw.rect(windshield_surface, windshield_color, windshield_surface.get_rect(), border_radius=5)
            screen.blit(windshield_surface, (self.x - self.width//2 + 6, y_pos - self.height//2 + 12))
            
            # Windows on sides
            pygame.draw.rect(screen, (80, 160, 220), (self.x - self.width//2 + 3, y_pos - self.height//2 + 20, 8, 15))
            pygame.draw.rect(screen, (80, 160, 220), (self.x + self.width//2 - 11, y_pos - self.height//2 + 20, 8, 15))
            
            # Wheels with rotation effect
            wheel_color = (40, 40, 40)
            wheel_highlight = (80, 80, 80)
            
            # Front wheels
            for wheel_x in [self.x - self.width//2 + 8, self.x + self.width//2 - 8]:
                pygame.draw.circle(screen, wheel_color, (int(wheel_x), int(y_pos - self.height//2 + 15)), 8)
                pygame.draw.circle(screen, wheel_highlight, (int(wheel_x), int(y_pos - self.height//2 + 15)), 4)
                
            # Back wheels
            for wheel_x in [self.x - self.width//2 + 8, self.x + self.width//2 - 8]:
                pygame.draw.circle(screen, wheel_color, (int(wheel_x), int(y_pos + self.height//2 - 15)), 8)
                pygame.draw.circle(screen, wheel_highlight, (int(wheel_x), int(y_pos + self.height//2 - 15)), 4)
            
            # Headlights with glow
            if not self.is_police:
                # Glow effect
                for radius in [8, 6, 4]:
                    alpha = 80 - radius * 8
                    glow_color = (*YELLOW, alpha)
                    glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, glow_color, (radius * 2, radius * 2), radius)
                    screen.blit(glow_surface, (int(self.x - self.width//2 + 10 - radius * 2), 
                                               int(y_pos - self.height//2 + 5 - radius * 2)))
                    screen.blit(glow_surface, (int(self.x + self.width//2 - 10 - radius * 2), 
                                               int(y_pos - self.height//2 + 5 - radius * 2)))
                
                pygame.draw.circle(screen, YELLOW, (int(self.x - self.width//2 + 10), int(y_pos - self.height//2 + 5)), 5)
                pygame.draw.circle(screen, YELLOW, (int(self.x + self.width//2 - 10), int(y_pos - self.height//2 + 5)), 5)
            
            # Police lights with enhanced animation
            if self.is_police:
                light_offset = (pygame.time.get_ticks() // 150) % 2
                
                # Siren bar
                pygame.draw.rect(screen, (20, 20, 20), (self.x - 20, y_pos - self.height//2 + 2, 40, 8), border_radius=2)
                
                if light_offset == 0:
                    # Red light with glow
                    for radius in [10, 7, 5]:
                        alpha = 100 - radius * 8
                        glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surface, (*RED, alpha), (radius * 2, radius * 2), radius)
                        screen.blit(glow_surface, (int(self.x - 12 - radius * 2), int(y_pos - self.height//2 + 6 - radius * 2)))
                    
                    pygame.draw.circle(screen, RED, (int(self.x - 12), int(y_pos - self.height//2 + 6)), 6)
                    pygame.draw.circle(screen, BLUE, (int(self.x + 12), int(y_pos - self.height//2 + 6)), 4)
                else:
                    # Blue light with glow
                    for radius in [10, 7, 5]:
                        alpha = 100 - radius * 8
                        glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surface, (*BLUE, alpha), (radius * 2, radius * 2), radius)
                        screen.blit(glow_surface, (int(self.x + 12 - radius * 2), int(y_pos - self.height//2 + 6 - radius * 2)))
                    
                    pygame.draw.circle(screen, BLUE, (int(self.x + 12), int(y_pos - self.height//2 + 6)), 6)
                    pygame.draw.circle(screen, RED, (int(self.x - 12), int(y_pos - self.height//2 + 6)), 4)
            
            # Tail lights
            pygame.draw.circle(screen, (180, 0, 0), (int(self.x - self.width//2 + 10), int(y_pos + self.height//2 - 8)), 4)
            pygame.draw.circle(screen, (180, 0, 0), (int(self.x + self.width//2 - 10), int(y_pos + self.height//2 - 8)), 4)
            
            # Side mirrors
            pygame.draw.rect(screen, DARK_GRAY, (self.x - self.width//2 - 5, y_pos - 5, 5, 8))
            pygame.draw.rect(screen, DARK_GRAY, (self.x + self.width//2, y_pos - 5, 5, 8))
        
        # Label with better styling
        font = pygame.font.Font(None, 24)
        if self.is_player:
            label = font.render("THIEF", True, WHITE)
            # Label background
            label_bg = pygame.Surface((label.get_width() + 10, label.get_height() + 6), pygame.SRCALPHA)
            pygame.draw.rect(label_bg, (255, 0, 0, 180), label_bg.get_rect(), border_radius=5)
            screen.blit(label_bg, (self.x - label.get_width()//2 - 5, y_pos - self.height//2 - 30))
            screen.blit(label, (self.x - label.get_width()//2, y_pos - self.height//2 - 28))
        elif self.is_police:
            label = font.render("POLICE", True, WHITE)
            label_bg = pygame.Surface((label.get_width() + 10, label.get_height() + 6), pygame.SRCALPHA)
            pygame.draw.rect(label_bg, (0, 0, 255, 180), label_bg.get_rect(), border_radius=5)
            screen.blit(label_bg, (self.x - label.get_width()//2 - 5, y_pos - self.height//2 - 30))
            screen.blit(label, (self.x - label.get_width()//2, y_pos - self.height//2 - 28))

class TrafficCar:
    def __init__(self, lane, distance):
        self.lane = lane
        self.x = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH // 2
        self.distance = distance
        self.width = 48
        self.height = 75
        self.colors = [(220, 20, 60), (30, 144, 255), (34, 139, 34), (255, 140, 0), 
                       (138, 43, 226), (255, 215, 0), (220, 220, 220)]
        self.color = random.choice(self.colors)
        self.speed = random.uniform(2, 4)
        
    def update(self):
        self.distance -= self.speed
        
    def draw(self, screen, camera_offset):
        y_pos = self.distance - camera_offset + SCREEN_HEIGHT // 2
        
        if -100 < y_pos < SCREEN_HEIGHT + 100:
            # Shadow
            shadow_surface = pygame.Surface((self.width + 8, self.height + 8), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, 60), shadow_surface.get_rect())
            screen.blit(shadow_surface, (self.x - self.width//2 - 4, y_pos + self.height//2))
            
            # Car body
            pygame.draw.rect(screen, self.color, 
                           (self.x - self.width//2, y_pos - self.height//2, self.width, self.height), 
                           border_radius=8)
            
            # Highlight
            highlight_color = tuple(min(c + 40, 255) for c in self.color)
            pygame.draw.rect(screen, highlight_color, 
                           (self.x - self.width//2 + 4, y_pos - self.height//2 + 4, self.width - 8, 12), 
                           border_radius=4)
            
            # Windshield
            windshield_surface = pygame.Surface((self.width - 10, 20), pygame.SRCALPHA)
            pygame.draw.rect(windshield_surface, (100, 180, 255, 180), windshield_surface.get_rect(), border_radius=4)
            screen.blit(windshield_surface, (self.x - self.width//2 + 5, y_pos + self.height//2 - 28))
            
            # Wheels
            wheel_color = (40, 40, 40)
            for wx in [self.x - self.width//2 + 7, self.x + self.width//2 - 7]:
                for wy in [y_pos - self.height//2 + 12, y_pos + self.height//2 - 12]:
                    pygame.draw.circle(screen, wheel_color, (int(wx), int(wy)), 6)
                    pygame.draw.circle(screen, (80, 80, 80), (int(wx), int(wy)), 3)
            
            # Tail lights
            pygame.draw.circle(screen, (180, 0, 0), (int(self.x - self.width//2 + 8), int(y_pos + self.height//2 - 6)), 3)
            pygame.draw.circle(screen, (180, 0, 0), (int(self.x + self.width//2 - 8), int(y_pos + self.height//2 - 6)), 3)

def draw_background_scenery(screen, camera_offset):
    """Draw vibrant city background with colorful buildings"""
    
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
    
    # Helper to draw building with shadow
    def draw_building_with_shadow(x, y, w, h, color):
        if y > SCREEN_HEIGHT or y + h < 0:
            return
        # Shadow
        shadow = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(screen, shadow, (x + w - 12, y, 12, h))
        # Main body
        pygame.draw.rect(screen, color, (x, y, w - 12, h))
        # Highlight on top
        highlight = tuple(min(255, c + 25) for c in color)
        pygame.draw.rect(screen, highlight, (x, y, w - 12, 6))
        # Border
        border = tuple(max(0, c - 50) for c in color)
        pygame.draw.rect(screen, border, (x, y, w, h), 2)
    
    # LEFT SIDE - Colorful buildings with scrolling
    left_x = 5
    building_spacing = 160
    
    for i in range(-2, (SCREEN_HEIGHT // building_spacing) + 3):
        y_base = i * building_spacing - scroll_offset
        building_type = (i + int(camera_offset // building_spacing)) % 8
        
        if building_type == 0:
            # Red brick building with detailed windows
            draw_building_with_shadow(left_x, y_base, 230, 180, (195, 75, 65))
            for wx in range(left_x + 12, left_x + 200, 24):
                for wy in range(y_base + 15, y_base + 165, 28):
                    if wy + 20 < y_base + 180:
                        # Gradient windows
                        for j in range(18):
                            bright = 250 - j * 4
                            pygame.draw.line(screen, (bright, bright - 10, min(255, bright + 20)), 
                                           (wx, wy + j), (wx + 18, wy + j))
                        pygame.draw.rect(screen, (40, 40, 50), (wx, wy, 18, 18), 1)
            
        elif building_type == 1:
            # Blue glass tower with reflective panels
            draw_building_with_shadow(left_x, y_base, 230, 220, (55, 95, 175))
            for panel_y in range(y_base + 10, y_base + 210, 40):
                if panel_y + 35 < y_base + 220:
                    for j in range(35):
                        bright = 110 + abs(17 - j) * 2
                        pygame.draw.line(screen, (bright, bright + 20, bright + 50), 
                                       (left_x + 5, panel_y + j), (left_x + 210, panel_y + j))
                    pygame.draw.line(screen, (35, 65, 135), (left_x + 5, panel_y), (left_x + 210, panel_y), 2)
            
        elif building_type == 2:
            # Yellow office with grid windows
            draw_building_with_shadow(left_x, y_base, 230, 190, (210, 190, 95))
            for wx in range(left_x + 15, left_x + 200, 26):
                for wy in range(y_base + 20, y_base + 175, 30):
                    if wy + 22 < y_base + 190:
                        pygame.draw.rect(screen, (255, 255, 200), (wx, wy, 20, 22))
                        pygame.draw.rect(screen, (60, 60, 70), (wx, wy, 20, 22), 2)
                        pygame.draw.line(screen, (60, 60, 70), (wx + 10, wy), (wx + 10, wy + 22), 1)
            
        elif building_type == 3:
            # Purple apartment with balconies
            draw_building_with_shadow(left_x, y_base, 230, 200, (135, 95, 155))
            floor_h = 33
            for floor in range(6):
                floor_y = y_base + 15 + floor * floor_h
                if floor_y + 25 < y_base + 200:
                    # Balcony
                    pygame.draw.rect(screen, (115, 75, 135), (left_x + 5, floor_y + 20, 210, 4))
                    # Windows
                    for window_x in [left_x + 20, left_x + 100, left_x + 180]:
                        pygame.draw.rect(screen, (255, 245, 180), (window_x, floor_y, 22, 18))
                        pygame.draw.rect(screen, (55, 55, 65), (window_x, floor_y, 22, 18), 2)
            
        elif building_type == 4:
            # Orange modern building
            draw_building_with_shadow(left_x, y_base, 230, 210, (230, 135, 65))
            for band in range(0, 210, 42):
                pygame.draw.rect(screen, (200, 110, 50), (left_x, y_base + band, 218, 5))
            for wx in range(left_x + 12, left_x + 200, 24):
                for wy in range(y_base + 18, y_base + 195, 28):
                    if wy + 20 < y_base + 210:
                        pygame.draw.rect(screen, (255, 255, 180), (wx, wy, 19, 20))
                        pygame.draw.rect(screen, (180, 100, 50), (wx, wy, 19, 20), 1)
            
        elif building_type == 5:
            # Green eco building
            draw_building_with_shadow(left_x, y_base, 230, 185, (95, 175, 115))
            for wx in range(left_x + 18, left_x + 200, 28):
                for wy in range(y_base + 18, y_base + 170, 30):
                    if wy + 22 < y_base + 185:
                        pygame.draw.rect(screen, (235, 255, 200), (wx, wy, 22, 22))
                        pygame.draw.rect(screen, (65, 145, 85), (wx, wy, 22, 22), 2)
            
        elif building_type == 6:
            # Detailed house with pitched roof
            house_x, house_y = left_x + 15, y_base + 35
            draw_building_with_shadow(house_x, house_y, 200, 115, (235, 195, 175))
            # Roof with shingles
            roof_pts = [(house_x - 8, house_y), (house_x + 94, y_base + 8), (house_x + 196, house_y)]
            pygame.draw.polygon(screen, (170, 65, 55), roof_pts)
            for j in range(0, 200, 10):
                pygame.draw.line(screen, (145, 50, 45), (house_x - 8 + j, house_y), 
                               (house_x - 8 + j//2, y_base + 8 + j//4), 1)
            # Chimney
            pygame.draw.rect(screen, (125, 55, 45), (house_x + 150, y_base + 15, 14, 25))
            # Door
            pygame.draw.rect(screen, (85, 55, 35), (house_x + 20, house_y + 75, 25, 40))
            pygame.draw.circle(screen, (200, 170, 0), (house_x + 40, house_y + 95), 3)
            # Windows
            for wx, wy in [(house_x + 60, house_y + 20), (house_x + 130, house_y + 20)]:
                pygame.draw.rect(screen, (150, 200, 250), (wx, wy, 30, 28))
                pygame.draw.rect(screen, (75, 60, 50), (wx, wy, 30, 28), 2)
                pygame.draw.line(screen, (75, 60, 50), (wx + 15, wy), (wx + 15, wy + 28), 2)
                pygame.draw.line(screen, (75, 60, 50), (wx, wy + 14), (wx + 30, wy + 14), 2)
        
        else:
            # Cyan modern tower
            draw_building_with_shadow(left_x, y_base, 230, 195, (65, 175, 195))
            for wx in range(left_x + 10, left_x + 200, 22):
                for wy in range(y_base + 14, y_base + 180, 25):
                    if wy + 20 < y_base + 195:
                        for j in range(20):
                            bright = 210 - j * 3
                            pygame.draw.line(screen, (bright - 30, bright, bright + 10), 
                                           (wx, wy + j), (wx + 18, wy + j))
                        pygame.draw.rect(screen, (45, 135, 155), (wx, wy, 18, 20), 1)
    
    # RIGHT SIDE - Same buildings mirrored
    right_x = SCREEN_WIDTH - 235
    
    for i in range(-2, (SCREEN_HEIGHT // building_spacing) + 3):
        y_base = i * building_spacing - scroll_offset
        building_type = (i + int(camera_offset // building_spacing) + 4) % 8
        
        if building_type == 0:
            draw_building_with_shadow(right_x, y_base, 230, 180, (195, 75, 65))
            for wx in range(right_x + 12, right_x + 200, 24):
                for wy in range(y_base + 15, y_base + 165, 28):
                    if wy + 20 < y_base + 180:
                        for j in range(18):
                            bright = 250 - j * 4
                            pygame.draw.line(screen, (bright, bright - 10, min(255, bright + 20)), 
                                           (wx, wy + j), (wx + 18, wy + j))
                        pygame.draw.rect(screen, (40, 40, 50), (wx, wy, 18, 18), 1)
            
        elif building_type == 1:
            draw_building_with_shadow(right_x, y_base, 230, 220, (55, 95, 175))
            for panel_y in range(y_base + 10, y_base + 210, 40):
                if panel_y + 35 < y_base + 220:
                    for j in range(35):
                        bright = 110 + abs(17 - j) * 2
                        pygame.draw.line(screen, (bright, bright + 20, bright + 50), 
                                       (right_x + 5, panel_y + j), (right_x + 210, panel_y + j))
                    pygame.draw.line(screen, (35, 65, 135), (right_x + 5, panel_y), (right_x + 210, panel_y), 2)
            
        elif building_type == 2:
            draw_building_with_shadow(right_x, y_base, 230, 190, (210, 190, 95))
            for wx in range(right_x + 15, right_x + 200, 26):
                for wy in range(y_base + 20, y_base + 175, 30):
                    if wy + 22 < y_base + 190:
                        pygame.draw.rect(screen, (255, 255, 200), (wx, wy, 20, 22))
                        pygame.draw.rect(screen, (60, 60, 70), (wx, wy, 20, 22), 2)
                        pygame.draw.line(screen, (60, 60, 70), (wx + 10, wy), (wx + 10, wy + 22), 1)
            
        elif building_type == 3:
            draw_building_with_shadow(right_x, y_base, 230, 200, (135, 95, 155))
            floor_h = 33
            for floor in range(6):
                floor_y = y_base + 15 + floor * floor_h
                if floor_y + 25 < y_base + 200:
                    pygame.draw.rect(screen, (115, 75, 135), (right_x + 5, floor_y + 20, 210, 4))
                    for window_x in [right_x + 20, right_x + 100, right_x + 180]:
                        pygame.draw.rect(screen, (255, 245, 180), (window_x, floor_y, 22, 18))
                        pygame.draw.rect(screen, (55, 55, 65), (window_x, floor_y, 22, 18), 2)
            
        elif building_type == 4:
            draw_building_with_shadow(right_x, y_base, 230, 210, (230, 135, 65))
            for band in range(0, 210, 42):
                pygame.draw.rect(screen, (200, 110, 50), (right_x, y_base + band, 218, 5))
            for wx in range(right_x + 12, right_x + 200, 24):
                for wy in range(y_base + 18, y_base + 195, 28):
                    if wy + 20 < y_base + 210:
                        pygame.draw.rect(screen, (255, 255, 180), (wx, wy, 19, 20))
                        pygame.draw.rect(screen, (180, 100, 50), (wx, wy, 19, 20), 1)
            
        elif building_type == 5:
            draw_building_with_shadow(right_x, y_base, 230, 185, (95, 175, 115))
            for wx in range(right_x + 18, right_x + 200, 28):
                for wy in range(y_base + 18, y_base + 170, 30):
                    if wy + 22 < y_base + 185:
                        pygame.draw.rect(screen, (235, 255, 200), (wx, wy, 22, 22))
                        pygame.draw.rect(screen, (65, 145, 85), (wx, wy, 22, 22), 2)
            
        elif building_type == 6:
            house_x, house_y = right_x + 15, y_base + 35
            draw_building_with_shadow(house_x, house_y, 200, 115, (235, 195, 175))
            roof_pts = [(house_x - 8, house_y), (house_x + 94, y_base + 8), (house_x + 196, house_y)]
            pygame.draw.polygon(screen, (170, 65, 55), roof_pts)
            for j in range(0, 200, 10):
                pygame.draw.line(screen, (145, 50, 45), (house_x - 8 + j, house_y), 
                               (house_x - 8 + j//2, y_base + 8 + j//4), 1)
            pygame.draw.rect(screen, (125, 55, 45), (house_x + 150, y_base + 15, 14, 25))
            pygame.draw.rect(screen, (85, 55, 35), (house_x + 20, house_y + 75, 25, 40))
            pygame.draw.circle(screen, (200, 170, 0), (house_x + 40, house_y + 95), 3)
            for wx, wy in [(house_x + 60, house_y + 20), (house_x + 130, house_y + 20)]:
                pygame.draw.rect(screen, (150, 200, 250), (wx, wy, 30, 28))
                pygame.draw.rect(screen, (75, 60, 50), (wx, wy, 30, 28), 2)
                pygame.draw.line(screen, (75, 60, 50), (wx + 15, wy), (wx + 15, wy + 28), 2)
                pygame.draw.line(screen, (75, 60, 50), (wx, wy + 14), (wx + 30, wy + 14), 2)
        
        else:
            draw_building_with_shadow(right_x, y_base, 230, 195, (65, 175, 195))
            for wx in range(right_x + 10, right_x + 200, 22):
                for wy in range(y_base + 14, y_base + 180, 25):
                    if wy + 20 < y_base + 195:
                        for j in range(20):
                            bright = 210 - j * 3
                            pygame.draw.line(screen, (bright - 30, bright, bright + 10), 
                                           (wx, wy + j), (wx + 18, wy + j))
                        pygame.draw.rect(screen, (45, 135, 155), (wx, wy, 18, 20), 1)
    
    # Draw curbs (edges between sidewalk and road)
    pygame.draw.rect(screen, (100, 100, 100), (ROAD_X - 10, 0, 10, SCREEN_HEIGHT))
    pygame.draw.rect(screen, (100, 100, 100), (ROAD_X + ROAD_WIDTH, 0, 10, SCREEN_HEIGHT))
    
    # Street lamps along the road edges
    lamp_spacing = 100
    lamp_offset = int(camera_offset % lamp_spacing)
    for i in range(-1, SCREEN_HEIGHT // lamp_spacing + 2):
        y = i * lamp_spacing - lamp_offset
        if 0 < y < SCREEN_HEIGHT:
            draw_street_lamp(screen, ROAD_X - 25, y)
            draw_street_lamp(screen, ROAD_X + ROAD_WIDTH + 25, y)

def draw_simple_building(screen, x, y, width, height, base_color):
    """Draw a simple background building"""
    if 0 < y < SCREEN_HEIGHT + 50:
        # Main body
        pygame.draw.rect(screen, base_color, (x, y, width, height))
        
        # Windows (simple grid)
        window_color = (80, 85, 70)
        for wx in range(int(x + 8), int(x + width - 8), 12):
            for wy in range(int(y + 10), int(y + height - 10), 15):
                if (wx + wy) % 30 < 20:
                    pygame.draw.rect(screen, window_color, (wx, wy, 4, 6))
        
        # Outline
        pygame.draw.rect(screen, (40, 45, 55), (x, y, width, height), 1)

def draw_skyscraper(screen, x, y, width, height):
    """Draw a modern skyscraper"""
    if y < SCREEN_HEIGHT + 50 and y + height > 0:
        # Determine building color based on position (consistent per position)
        color_seed = int(x + y) % 3
        if color_seed == 0:
            building_color = (65, 75, 90)
            window_lit = (255, 255, 180)
        elif color_seed == 1:
            building_color = (75, 80, 95)
            window_lit = (200, 220, 255)
        else:
            building_color = (80, 70, 85)
            window_lit = (255, 240, 200)
        
        # Main building body
        pygame.draw.rect(screen, building_color, (x, y, width, height))
        
        # Darker side for depth
        shadow_color = tuple(max(0, c - 20) for c in building_color)
        pygame.draw.rect(screen, shadow_color, (x + width - 15, y, 15, height))
        
        # Building edge outline
        pygame.draw.rect(screen, (40, 45, 55), (x, y, width, height), 3)
        
        # Windows in a grid pattern
        window_width = 8
        window_height = 10
        spacing_x = 16
        spacing_y = 18
        
        window_seed = int(x * 7 + y * 13)
        for wx in range(int(x + 12), int(x + width - 20), spacing_x):
            for wy in range(int(y + 15), int(y + height - 15), spacing_y):
                # Deterministic lit/unlit windows based on position
                window_seed = (window_seed * 9301 + 49297) % 233280
                if window_seed % 100 > 35:
                    pygame.draw.rect(screen, window_lit, (wx, wy, window_width, window_height))
                else:
                    pygame.draw.rect(screen, (25, 30, 40), (wx, wy, window_width, window_height))
        
        # Rooftop
        pygame.draw.rect(screen, (50, 55, 65), (x, y - 5, width, 5))
        
def draw_office_building(screen, x, y, width, height):
    """Draw an office building"""
    if y < SCREEN_HEIGHT + 50 and y + height > 0:
        # Consistent color based on position
        color_seed = int(x + y) % 3
        if color_seed == 0:
            building_color = (90, 80, 85)
        elif color_seed == 1:
            building_color = (95, 90, 80)
        else:
            building_color = (80, 90, 100)
        
        # Main body
        pygame.draw.rect(screen, building_color, (x, y, width, height))
        
        # Side shadow
        shadow_color = tuple(max(0, c - 25) for c in building_color)
        pygame.draw.rect(screen, shadow_color, (x + width - 12, y, 12, height))
        
        # Horizontal bands
        band_count = int(height // 45)
        for i in range(band_count):
            band_y = y + i * 45
            pygame.draw.rect(screen, (55, 55, 65), (x, band_y, width, 5))
        
        # Windows
        window_size = 9
        spacing = 18
        window_seed = int(x * 11 + y * 7)
        for wx in range(int(x + 14), int(x + width - 14), spacing):
            for wy in range(int(y + 20), int(y + height - 20), spacing):
                window_seed = (window_seed * 9301 + 49297) % 233280
                if window_seed % 100 > 45:
                    pygame.draw.rect(screen, (255, 250, 200), (wx, wy, window_size, window_size))
                else:
                    pygame.draw.rect(screen, (35, 40, 50), (wx, wy, window_size, window_size))
        
        # Building outline
        pygame.draw.rect(screen, (50, 55, 65), (x, y, width, height), 3)

def draw_apartment(screen, x, y, width, height):
    """Draw an apartment building"""
    if y < SCREEN_HEIGHT + 50 and y + height > 0:
        # Consistent color based on position
        color_seed = int(x + y) % 4
        if color_seed == 0:
            building_color = (105, 85, 80)
        elif color_seed == 1:
            building_color = (90, 100, 90)
        elif color_seed == 2:
            building_color = (100, 90, 100)
        else:
            building_color = (95, 95, 85)
        
        # Main body
        pygame.draw.rect(screen, building_color, (x, y, width, height))
        
        # Side shadow
        shadow_color = tuple(max(0, c - 30) for c in building_color)
        pygame.draw.rect(screen, shadow_color, (x + width - 10, y, 10, height))
        
        # Balconies
        balcony_spacing = 30
        for i, wy in enumerate(range(int(y + 25), int(y + height - 15), balcony_spacing)):
            # Balcony floor
            pygame.draw.rect(screen, (65, 60, 60), (x, wy, width, 4))
            # Balcony railing lines
            for bx in range(int(x + 6), int(x + width - 6), 10):
                pygame.draw.line(screen, (50, 50, 55), (bx, wy), (bx, wy + 10), 2)
        
        # Windows
        window_width = 10
        spacing_x = 18
        window_seed = int(x * 13 + y * 9)
        for wx in range(int(x + 12), int(x + width - 12), spacing_x):
            for wy in range(int(y + 15), int(y + height - 15), balcony_spacing):
                window_seed = (window_seed * 9301 + 49297) % 233280
                if window_seed % 100 > 35:
                    pygame.draw.rect(screen, (255, 250, 180), (wx, wy, window_width, 15))
                else:
                    pygame.draw.rect(screen, (40, 45, 55), (wx, wy, window_width, 15))
        
        # Building outline
        pygame.draw.rect(screen, (55, 60, 65), (x, y, width, height), 3)

def draw_shop(screen, x, y, width, height):
    """Draw a small shop/store"""
    if y < SCREEN_HEIGHT + 50 and y + height > 0:
        # Consistent shop color based on position
        color_seed = int(x + y) % 4
        if color_seed == 0:
            building_color = (130, 85, 80)
            awning_color = (200, 50, 50)
        elif color_seed == 1:
            building_color = (85, 130, 100)
            awning_color = (50, 150, 60)
        elif color_seed == 2:
            building_color = (110, 110, 130)
            awning_color = (60, 60, 200)
        else:
            building_color = (130, 100, 80)
            awning_color = (200, 130, 50)
        
        # Main shop body
        pygame.draw.rect(screen, building_color, (x, y, width, height))
        
        # Awning
        awning_height = 15
        awning_y = y + height - 50
        pygame.draw.rect(screen, awning_color, (x, awning_y, width, awning_height))
        
        # Awning stripes
        stripe_color = tuple(max(0, c - 60) for c in awning_color)
        for i in range(0, int(width), 15):
            if i % 30 == 0:
                pygame.draw.rect(screen, stripe_color, (x + i, awning_y, 15, awning_height))
        
        # Awning shadow
        pygame.draw.rect(screen, (30, 30, 30), (x, awning_y + awning_height, width, 3))
        
        # Shop window/display
        window_y = y + height - 35
        pygame.draw.rect(screen, (130, 170, 210), (x + 10, window_y, width - 20, 28))
        pygame.draw.rect(screen, (70, 80, 100), (x + 10, window_y, width - 20, 28), 3)
        
        # Door
        door_color = (65, 50, 35)
        pygame.draw.rect(screen, door_color, (x + width//2 - 10, y + height - 7, 20, 7))
        
        # Shop sign
        sign_y = y + 12
        pygame.draw.rect(screen, (25, 25, 30), (x + 8, sign_y, width - 16, 18))
        sign_color = (255, 200, 50)
        pygame.draw.rect(screen, sign_color, (x + 10, sign_y + 2, width - 20, 14))
        
        # Building outline
        pygame.draw.rect(screen, (55, 60, 65), (x, y, width, height), 3)

def draw_street_lamp(screen, x, y):
    """Draw a street lamp"""
    if 0 < y < SCREEN_HEIGHT:
        # Pole
        pygame.draw.rect(screen, (60, 60, 60), (x - 2, y - 30, 4, 35))
        
        # Lamp head
        pygame.draw.circle(screen, (80, 80, 80), (int(x), int(y - 30)), 6)
        
        # Light glow
        glow_color = (255, 255, 150, 60)
        glow_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, glow_color, (10, 10), 10)
        screen.blit(glow_surface, (x - 10, y - 40))
        
        # Bright center
        pygame.draw.circle(screen, (255, 255, 200), (int(x), int(y - 30)), 3)

def draw_tree(screen, x, y, size):
    """Draw a simple tree"""
    if 0 < y < SCREEN_HEIGHT:
        # Trunk
        trunk_width = size // 5
        trunk_height = size
        pygame.draw.rect(screen, BROWN, (x - trunk_width//2, y, trunk_width, trunk_height))
        
        # Leaves (3 circles)
        leaf_color = DARK_GREEN
        pygame.draw.circle(screen, leaf_color, (int(x), int(y)), int(size * 0.6))
        pygame.draw.circle(screen, leaf_color, (int(x - size//3), int(y + size//4)), int(size * 0.5))
        pygame.draw.circle(screen, leaf_color, (int(x + size//3), int(y + size//4)), int(size * 0.5))

def draw_road(screen, camera_offset):
    """Draw 3D perspective road with city elements"""
    # Draw narrow sidewalks only near the road (don't cover buildings)
    sidewalk_width = 40  # Much narrower sidewalk
    
    # Left sidewalk with pattern (only near road edge)
    for i in range(0, SCREEN_HEIGHT, 20):
        y = i - int(camera_offset % 20)
        color = (140, 140, 140) if (i // 20) % 2 == 0 else (150, 150, 150)
        pygame.draw.rect(screen, color, (ROAD_X - sidewalk_width, y, sidewalk_width - 10, 20))
    
    # Right sidewalk with pattern (only near road edge)
    for i in range(0, SCREEN_HEIGHT, 20):
        y = i - int(camera_offset % 20)
        color = (140, 140, 140) if (i // 20) % 2 == 0 else (150, 150, 150)
        pygame.draw.rect(screen, color, (ROAD_X + ROAD_WIDTH + 10, y, sidewalk_width - 10, 20))
    
    # Draw curbs (edges between sidewalk and road)
    pygame.draw.rect(screen, (100, 100, 100), (ROAD_X - 10, 0, 10, SCREEN_HEIGHT))
    pygame.draw.rect(screen, (100, 100, 100), (ROAD_X + ROAD_WIDTH, 0, 10, SCREEN_HEIGHT))
    
    # Draw road with gradient for depth effect
    for y in range(SCREEN_HEIGHT):
        darkness = int(50 - (y / SCREEN_HEIGHT) * 15)
        road_color = (darkness, darkness, darkness)
        pygame.draw.line(screen, road_color, (ROAD_X, y), (ROAD_X + ROAD_WIDTH, y))
    
    # Draw road edge white lines
    pygame.draw.rect(screen, WHITE, (ROAD_X, 0, 4, SCREEN_HEIGHT))
    pygame.draw.rect(screen, WHITE, (ROAD_X + ROAD_WIDTH - 4, 0, 4, SCREEN_HEIGHT))
    
    # Draw lane dividers with animation
    dash_height = 50
    dash_gap = 40
    offset = int(camera_offset % (dash_height + dash_gap))
    
    for lane in range(1, 3):
        x = ROAD_X + lane * LANE_WIDTH
        for y in range(-offset, SCREEN_HEIGHT, dash_height + dash_gap):
            # Dashed lines with perspective
            width = 4 + int((y / SCREEN_HEIGHT) * 2)
            pygame.draw.rect(screen, WHITE, (x - width//2, y, width, dash_height))

def draw_hud(screen, player, police, traffic_cars, freeze_timer=0, boost_timer=0, shield_timer=0, ghost_timer=0, powerups_collected=0):
    """Enhanced HUD with modern styling"""
    # Top bar with gradient
    top_bar = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
    for i in range(120):
        alpha = int(200 - (i * 1.2))
        pygame.draw.line(top_bar, (0, 0, 0, alpha), (0, i), (SCREEN_WIDTH, i))
    screen.blit(top_bar, (0, 0))
    
    # Title with glow effect
    font_title = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 32)
    font_small = pygame.font.Font(None, 26)
    
    # Title with outline
    title_text = "🏁 ROAD RUSH"
    for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
        title = font_title.render(title_text, True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 130 + offset[0], 15 + offset[1]))
    title = font_title.render(title_text, True, ORANGE)
    screen.blit(title, (SCREEN_WIDTH // 2 - 130, 15))
    
    # Subtitle
    subtitle = font_small.render("🤖 AI vs AI Mode", True, YELLOW)
    screen.blit(subtitle, (SCREEN_WIDTH // 2 - 75, 58))
    
    # Speed gauge with bar
    speed_label = font_small.render("SPEED", True, WHITE)
    screen.blit(speed_label, (30, 85))
    
    speed_value = int(player.speed * 25)
    speed_text = font_medium.render(f"{speed_value} km/h", True, YELLOW)
    screen.blit(speed_text, (110, 80))
    
    # Speed bar
    bar_width = 150
    bar_height = 20
    pygame.draw.rect(screen, (50, 50, 50), (30, 110, bar_width, bar_height), border_radius=10)
    
    # Filled portion
    filled_width = int((speed_value / 200) * bar_width)
    if speed_value > 150:
        bar_color = RED
    elif speed_value > 100:
        bar_color = ORANGE
    else:
        bar_color = GREEN
    
    if filled_width > 0:
        pygame.draw.rect(screen, bar_color, (30, 110, filled_width, bar_height), border_radius=10)
    
    # Distance to finish
    player_distance_left = max(0, FINISH_LINE_DISTANCE - player.distance)
    distance_text = font_small.render(f"FINISH: {int(player_distance_left)}m", True, WHITE)
    screen.blit(distance_text, (SCREEN_WIDTH - 220, 85))
    
    # Progress bar
    progress = player.distance / FINISH_LINE_DISTANCE
    progress_width = 180
    progress_height = 20
    pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH - 220, 110, progress_width, progress_height), border_radius=10)
    
    filled_progress = int(progress * progress_width)
    if filled_progress > 0:
        pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 220, 110, filled_progress, progress_height), border_radius=10)
    
    # Power-ups collected counter (top right corner)
    if powerups_collected > 0:
        powerup_font = pygame.font.Font(None, 28)
        powerup_text = powerup_font.render(f"⭐ Power-ups: {powerups_collected}", True, YELLOW)
        screen.blit(powerup_text, (SCREEN_WIDTH - 220, 50))
    
    # Active power-up indicators (right side)
    powerup_icon_size = 50
    powerup_y_start = 160
    powerup_x = SCREEN_WIDTH - 80
    active_powerup_y = powerup_y_start
    
    if freeze_timer > 0:
        # Freeze power-up indicator
        powerup_bg = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(powerup_bg, (100, 200, 255, 200), powerup_bg.get_rect(), border_radius=10)
        screen.blit(powerup_bg, (powerup_x - 10, active_powerup_y - 10))
        
        freeze_font = pygame.font.Font(None, 48)
        freeze_icon = freeze_font.render("❄️", True, WHITE)
        screen.blit(freeze_icon, (powerup_x, active_powerup_y))
        
        # Timer bar
        timer_width = 60
        timer_progress = (freeze_timer / 180) * timer_width
        pygame.draw.rect(screen, (50, 50, 80), (powerup_x - 5, active_powerup_y + 55, timer_width, 8), border_radius=4)
        pygame.draw.rect(screen, (100, 200, 255), (powerup_x - 5, active_powerup_y + 55, int(timer_progress), 8), border_radius=4)
        
        active_powerup_y += 80
    
    if boost_timer > 0:
        # Boost power-up indicator
        powerup_bg = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(powerup_bg, (255, 200, 0, 200), powerup_bg.get_rect(), border_radius=10)
        screen.blit(powerup_bg, (powerup_x - 10, active_powerup_y - 10))
        
        boost_font = pygame.font.Font(None, 48)
        boost_icon = boost_font.render("⚡", True, WHITE)
        screen.blit(boost_icon, (powerup_x, active_powerup_y))
        
        # Timer bar
        timer_width = 60
        timer_progress = (boost_timer / 240) * timer_width
        pygame.draw.rect(screen, (80, 60, 0), (powerup_x - 5, active_powerup_y + 55, timer_width, 8), border_radius=4)
        pygame.draw.rect(screen, (255, 200, 0), (powerup_x - 5, active_powerup_y + 55, int(timer_progress), 8), border_radius=4)
        
        active_powerup_y += 80
    
    if shield_timer > 0:
        # Shield power-up indicator
        powerup_bg = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(powerup_bg, (150, 255, 150, 200), powerup_bg.get_rect(), border_radius=10)
        screen.blit(powerup_bg, (powerup_x - 10, active_powerup_y - 10))
        
        shield_font = pygame.font.Font(None, 48)
        shield_icon = shield_font.render("🛡️", True, WHITE)
        screen.blit(shield_icon, (powerup_x, active_powerup_y))
        
        # Timer bar
        timer_width = 60
        timer_progress = (shield_timer / 360) * timer_width
        pygame.draw.rect(screen, (50, 80, 50), (powerup_x - 5, active_powerup_y + 55, timer_width, 8), border_radius=4)
        pygame.draw.rect(screen, (150, 255, 150), (powerup_x - 5, active_powerup_y + 55, int(timer_progress), 8), border_radius=4)
        
        active_powerup_y += 80
    
    if ghost_timer > 0:
        # Ghost power-up indicator
        powerup_bg = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(powerup_bg, (200, 150, 255, 200), powerup_bg.get_rect(), border_radius=10)
        screen.blit(powerup_bg, (powerup_x - 10, active_powerup_y - 10))
        
        ghost_font = pygame.font.Font(None, 48)
        ghost_icon = ghost_font.render("👻", True, WHITE)
        screen.blit(ghost_icon, (powerup_x, active_powerup_y))
        
        # Timer bar
        timer_width = 60
        timer_progress = (ghost_timer / 300) * timer_width
        pygame.draw.rect(screen, (60, 50, 80), (powerup_x - 5, active_powerup_y + 55, timer_width, 8), border_radius=4)
        pygame.draw.rect(screen, (200, 150, 255), (powerup_x - 5, active_powerup_y + 55, int(timer_progress), 8), border_radius=4)
    
    # Police distance indicator
    distance_diff = abs(player.distance - police.distance)
    
    # Center bottom info panel
    panel_width = 350
    panel_height = 60
    panel_x = (SCREEN_WIDTH - panel_width) // 2
    panel_y = SCREEN_HEIGHT - panel_height - 20
    
    panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (0, 0, 0, 160), panel_surface.get_rect(), border_radius=15)
    screen.blit(panel_surface, (panel_x, panel_y))
    
    # Police status with icon
    if player.distance > police.distance:
        status_color = GREEN
        status_icon = "✓"
        status_text = f"{status_icon} Police Behind: {int(distance_diff)}m"
    else:
        status_color = RED
        status_icon = "⚠"
        status_text = f"{status_icon} Police Ahead: {int(distance_diff)}m"
    
    police_status = font_medium.render(status_text, True, status_color)
    screen.blit(police_status, (panel_x + 20, panel_y + 15))
    
    # Mini-map or warning
    if distance_diff < 200:
        warning_font = pygame.font.Font(None, 28)
        warning = warning_font.render("⚠ POLICE NEARBY!", True, RED)
        flash = (pygame.time.get_ticks() // 300) % 2
        if flash:
            screen.blit(warning, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 120))
    
    # Crash status indicator
    if player.crashed:
        crash_font = pygame.font.Font(None, 36)
        crash_text = crash_font.render("💥 CRASHED! RECOVERING...", True, RED)
        crash_bg = pygame.Surface((crash_text.get_width() + 20, crash_text.get_height() + 10), pygame.SRCALPHA)
        pygame.draw.rect(crash_bg, (0, 0, 0, 180), crash_bg.get_rect(), border_radius=10)
        screen.blit(crash_bg, (SCREEN_WIDTH // 2 - crash_text.get_width() // 2 - 10, 150))
        screen.blit(crash_text, (SCREEN_WIDTH // 2 - crash_text.get_width() // 2, 155))
    
    if police.crashed:
        police_crash_font = pygame.font.Font(None, 28)
        police_crash = police_crash_font.render("✓ Police Crashed!", True, GREEN)
        screen.blit(police_crash, (SCREEN_WIDTH // 2 - 80, 190))
    
    # Freeze effect notification
    if freeze_timer > 0:
        freeze_notif_font = pygame.font.Font(None, 32)
        freeze_notif = freeze_notif_font.render("❄️ POLICE FROZEN!", True, (100, 200, 255))
        screen.blit(freeze_notif, (SCREEN_WIDTH // 2 - 100, 220))

def draw_finish_line(screen, camera_offset, finish_distance):
    """Enhanced finish line with celebration effect"""
    y_pos = finish_distance - camera_offset + SCREEN_HEIGHT // 2
    
    if -300 < y_pos < SCREEN_HEIGHT + 300:
        # Checkered pattern with 3D effect
        square_size = 35
        for i in range(ROAD_WIDTH // square_size + 1):
            for j in range(4):
                color = WHITE if (i + j) % 2 == 0 else BLACK
                pygame.draw.rect(screen, color, 
                               (ROAD_X + i * square_size, y_pos - 60 + j * square_size, 
                                square_size, square_size))
        
        # Finish banner
        banner_height = 80
        banner_surface = pygame.Surface((ROAD_WIDTH, banner_height), pygame.SRCALPHA)
        
        # Banner gradient
        for i in range(banner_height):
            alpha = int(180 - (abs(i - banner_height//2) * 2))
            pygame.draw.line(banner_surface, (255, 215, 0, alpha), 
                           (0, i), (ROAD_WIDTH, i))
        
        screen.blit(banner_surface, (ROAD_X, y_pos - 120))
        
        # Finish text with multiple styles
        font_huge = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 36)
        
        # Shadow
        finish_shadow = font_huge.render("★ FINISH LINE ★", True, BLACK)
        screen.blit(finish_shadow, (SCREEN_WIDTH // 2 - 195, y_pos - 95))
        
        # Main text
        finish_text = font_huge.render("★ FINISH LINE ★", True, YELLOW)
        screen.blit(finish_text, (SCREEN_WIDTH // 2 - 197, y_pos - 97))
        
        # Flashing effect
        if (pygame.time.get_ticks() // 200) % 2:
            glow_surface = pygame.Surface((ROAD_WIDTH + 100, 200), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (255, 255, 0, 30), glow_surface.get_rect())
            screen.blit(glow_surface, (ROAD_X - 50, y_pos - 150))

def draw_speed_lines(screen, player_speed):
    """Draw motion blur effect based on speed"""
    if player_speed > 3:
        line_count = int(player_speed * 3)
        for _ in range(line_count):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            length = random.randint(10, 30)
            alpha = int((player_speed / 8) * 100)
            
            line_surface = pygame.Surface((3, length), pygame.SRCALPHA)
            pygame.draw.line(line_surface, (255, 255, 255, alpha), (1, 0), (1, length), 2)
            screen.blit(line_surface, (x, y))

def show_start_screen(screen):
    """Ultra-attractive start screen with smooth animations"""
    clock = pygame.time.Clock()
    waiting = True
    start_time = pygame.time.get_ticks()
    particles_bg = []
    
    # Create background particles for animation
    for _ in range(50):
        particles_bg.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'speed': random.uniform(0.5, 2),
            'size': random.randint(1, 3)
        })
    
    while waiting:
        elapsed = pygame.time.get_ticks() - start_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
        
        # Smooth gradient background (dark blue to purple)
        for i in range(SCREEN_HEIGHT):
            ratio = i / SCREEN_HEIGHT
            r = int(20 + ratio * 40)
            g = int(20 + math.sin(ratio * math.pi) * 30)
            b = int(40 + ratio * 60)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        # Animated particles
        for particle in particles_bg:
            particle['y'] += particle['speed']
            if particle['y'] > SCREEN_HEIGHT:
                particle['y'] = 0
                particle['x'] = random.randint(0, SCREEN_WIDTH)
            
            alpha = int(150 + math.sin(elapsed / 500 + particle['x']) * 50)
            color = (alpha, alpha, 255)
            pygame.draw.circle(screen, color, (int(particle['x']), int(particle['y'])), particle['size'])
        
        # Animated road lines on sides
        line_offset = (elapsed // 20) % 60
        for y in range(-60, SCREEN_HEIGHT + 60, 60):
            y_pos = y + line_offset
            # Left side
            pygame.draw.rect(screen, (100, 100, 120), (50, y_pos, 15, 40))
            # Right side  
            pygame.draw.rect(screen, (100, 100, 120), (SCREEN_WIDTH - 65, y_pos, 15, 40))
        
        font_huge = pygame.font.Font(None, 120)
        font_title = pygame.font.Font(None, 96)
        font_subtitle = pygame.font.Font(None, 52)
        font_text = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 30)
        
        # Main title with 3D effect and pulse
        pulse = math.sin(elapsed / 300) * 8
        title_y = 120 + pulse
        
        # Shadow layers for 3D depth
        for depth in range(8, 0, -1):
            shadow_color = (20 + depth * 5, 10 + depth * 3, 0)
            shadow_title = font_huge.render("ROAD RUSH", True, shadow_color)
            shadow_rect = shadow_title.get_rect(center=(SCREEN_WIDTH // 2 + depth, title_y + depth))
            screen.blit(shadow_title, shadow_rect)
        
        # Glowing outline
        glow_intensity = abs(math.sin(elapsed / 400)) * 100 + 100
        for offset_x, offset_y in [(-2, -2), (2, -2), (-2, 2), (2, 2), (-3, 0), (3, 0), (0, -3), (0, 3)]:
            glow_color = (255, int(glow_intensity), 0)
            glow_title = font_huge.render("ROAD RUSH", True, glow_color)
            glow_rect = glow_title.get_rect(center=(SCREEN_WIDTH // 2 + offset_x, title_y + offset_y))
            screen.blit(glow_title, glow_rect)
        
        # Main title
        gradient_y = int(title_y)
        title_text = font_huge.render("ROAD RUSH", True, (255, 200, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, gradient_y))
        screen.blit(title_text, title_rect)
        
        # Shiny overlay effect
        shine_pos = (elapsed // 10) % (title_text.get_width() + 200) - 100
        shine_surf = pygame.Surface((50, title_text.get_height()), pygame.SRCALPHA)
        for i in range(50):
            alpha = int(100 * (1 - abs(i - 25) / 25))
            pygame.draw.line(shine_surf, (255, 255, 255, alpha), (i, 0), (i, title_text.get_height()))
        screen.blit(shine_surf, (title_rect.x + shine_pos, title_rect.y))
        
        # Subtitle with wave effect
        wave_offset = math.sin(elapsed / 800) * 6
        subtitle = font_subtitle.render("🚔 Police Chase Edition 🚗", True, (255, 255, 100))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220 + wave_offset))
        
        # Subtitle glow
        for r in [8, 6, 4]:
            s_glow = pygame.Surface((subtitle.get_width() + r*2, subtitle.get_height() + r*2), pygame.SRCALPHA)
            alpha = 40 - r * 3
            pygame.draw.rect(s_glow, (255, 215, 0, alpha), s_glow.get_rect(), border_radius=15)
            screen.blit(s_glow, (subtitle_rect.x - r, subtitle_rect.y - r))
        
        screen.blit(subtitle, subtitle_rect)
        
        # Animated decorative lines with gradient
        line_width = 650
        line_x = SCREEN_WIDTH // 2 - line_width // 2
        line_y = 285
        
        for i in range(line_width):
            ratio = i / line_width
            r = int(255 * (1 - ratio) + 100 * ratio)
            g = int(150 * (1 - ratio) + 50 * ratio)
            b = int(0 * (1 - ratio) + 100 * ratio)
            pygame.draw.line(screen, (r, g, b), (line_x + i, line_y), (line_x + i, line_y + 4))
        
        # Modern glass-morphism panel for controls
        panel_y = 310
        panel_width = 750
        panel_height = 290  # Reduced height since removing objective section
        panel_x = SCREEN_WIDTH // 2 - panel_width // 2
        
        # Panel with blur effect (simulated with semi-transparent layers)
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (40, 40, 70, 160), panel_surface.get_rect(), border_radius=25)
        
        # Border with gradient glow
        border_glow = abs(math.sin(elapsed / 600)) * 50 + 150
        pygame.draw.rect(panel_surface, (int(border_glow), 140, 255, 200), panel_surface.get_rect(), 3, border_radius=25)
        
        # Inner highlight
        pygame.draw.rect(panel_surface, (255, 255, 255, 30), (5, 5, panel_width - 10, panel_height - 10), 2, border_radius=22)
        
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Animated icon and instructions
        icon_bounce = abs(math.sin(elapsed / 400) * 4)
        
        # Game Mode section
        controls_y = panel_y + 35
        mode_title = font_subtitle.render("🤖 AI vs AI MODE", True, (100, 255, 255))
        mode_rect = mode_title.get_rect(center=(SCREEN_WIDTH // 2, controls_y + icon_bounce))
        screen.blit(mode_title, mode_rect)
        
        # Game info with icons
        info_data = [
            ("🚗", "Smart Thief AI", (100, 255, 150)),
            ("🚔", "Aggressive Police AI", (255, 120, 120)),
            ("⭐", "Collect Power-ups", (255, 200, 0)),
        ]
        
        info_y = controls_y + 70
        for icon, text, color in info_data:
            # Icon box
            icon_x = SCREEN_WIDTH // 2 - 250
            icon_surf = pygame.Surface((70, 45), pygame.SRCALPHA)
            pygame.draw.rect(icon_surf, (color[0]//3, color[1]//3, color[2]//3, 180), icon_surf.get_rect(), border_radius=8)
            pygame.draw.rect(icon_surf, color, icon_surf.get_rect(), 2, border_radius=8)
            screen.blit(icon_surf, (icon_x, info_y - 5))
            
            # Icon text
            icon_text = font_text.render(icon, True, color)
            icon_rect = icon_text.get_rect(center=(icon_x + 35, info_y + 17))
            screen.blit(icon_text, icon_rect)
            
            # Description
            desc_text = font_text.render(text, True, (230, 230, 255))
            desc_rect = desc_text.get_rect(midleft=(icon_x + 85, info_y + 17))
            screen.blit(desc_text, desc_rect)
            
            info_y += 58
        
        # Watch AI compete text
        watch_text = font_small.render("⚡ Watch AI compete in high-speed chase!", True, (255, 255, 150))
        watch_rect = watch_text.get_rect(center=(SCREEN_WIDTH // 2, info_y + 5))
        screen.blit(watch_text, watch_rect)
        
        # Press Space to Start button inside panel
        start_button_y = info_y + 30
        flash_cycle = (elapsed // 400) % 3
        
        if flash_cycle < 2:
            button_scale = 1 + math.sin(elapsed / 150) * 0.03
            
            # Button background with glow
            button_surf = pygame.Surface((520, 50), pygame.SRCALPHA)
            pygame.draw.rect(button_surf, (0, 255, 100, 200), button_surf.get_rect(), border_radius=25)
            
            # Animated border
            border_color = (100, 255, 150) if flash_cycle == 0 else (150, 255, 100)
            pygame.draw.rect(button_surf, border_color, button_surf.get_rect(), 3, border_radius=25)
            
            # Glow layers (smaller)
            for r in range(12, 0, -3):
                glow_surf = pygame.Surface((520 + r*2, 50 + r*2), pygame.SRCALPHA)
                alpha = 12 - r // 2
                pygame.draw.rect(glow_surf, (100, 255, 150, alpha), glow_surf.get_rect(), border_radius=25 + r)
                screen.blit(glow_surf, (SCREEN_WIDTH // 2 - 260 - r, start_button_y - r))
            
            # Scale button
            scaled_surf = pygame.transform.scale(button_surf, 
                                                (int(520 * button_scale), int(50 * button_scale)))
            scaled_rect = scaled_surf.get_rect(center=(SCREEN_WIDTH // 2, start_button_y + 25))
            screen.blit(scaled_surf, scaled_rect)
            
            # Button text (smaller font)
            font_button = pygame.font.Font(None, 42)
            start_text = font_button.render("▶  PRESS SPACE TO START  ◀", True, (0, 50, 0))
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, start_button_y + 25))
            screen.blit(start_text, start_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return True

def show_end_screen(screen, winner):
    """Ultra-attractive end screen with spectacular animations"""
    clock = pygame.time.Clock()
    waiting = True
    start_time = pygame.time.get_ticks()
    
    # Create celebration particles
    celebration_particles = []
    if winner == "thief":
        for _ in range(100):
            celebration_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(-200, 0),
                'speed': random.uniform(2, 6),
                'size': random.randint(3, 8),
                'color': random.choice([(255, 215, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255)])
            })
    else:
        # Police lights particles
        for _ in range(60):
            celebration_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(20, 40),
                'flash': random.randint(0, 10)
            })
    
    while waiting:
        elapsed = pygame.time.get_ticks() - start_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
        
        # Professional racing game background - similar to landing page
        if winner == "thief":
            # Victory - Calm professional gradient with subtle animation
            for i in range(SCREEN_HEIGHT):
                ratio = i / SCREEN_HEIGHT
                r = int(25 + ratio * 50)
                g = int(50 + ratio * 80)
                b = int(35 + ratio * 80)
                pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
            
            # Subtle floating particles (less noisy)
            for particle in celebration_particles[:30]:  # Reduce particle count
                particle['y'] += particle['speed'] * 0.5  # Slower movement
                if particle['y'] > SCREEN_HEIGHT:
                    particle['y'] = random.randint(-50, -10)
                    particle['x'] = random.randint(0, SCREEN_WIDTH)
                
                # Draw subtle particles
                alpha = int(100 + math.sin(elapsed / 500 + particle['x']) * 50)
                color = (alpha, alpha, min(255, alpha + 50))
                pygame.draw.circle(screen, color, (int(particle['x']), int(particle['y'])), 2)
        
        else:
            # Game Over - Professional dark gradient
            for i in range(SCREEN_HEIGHT):
                ratio = i / SCREEN_HEIGHT
                r = int(30 + ratio * 40)
                g = int(15 + ratio * 30)
                b = int(40 + ratio * 50)
                pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
            
            # Subtle particles for atmosphere
            for particle in celebration_particles[:30]:  # Reduce particle count
                alpha = int(80 + math.sin(elapsed / 400 + particle['x']) * 40)
                color = (alpha, alpha // 2, alpha)
                pygame.draw.circle(screen, color, (int(particle['x']), int(particle['y'])), 2)
        
        # Animated road lines on sides (like landing page)
        line_offset = (elapsed // 20) % 60
        for y in range(-60, SCREEN_HEIGHT + 60, 60):
            y_pos = y + line_offset
            # Left side
            pygame.draw.rect(screen, (80, 80, 100), (50, y_pos, 12, 35))
            # Right side  
            pygame.draw.rect(screen, (80, 80, 100), (SCREEN_WIDTH - 62, y_pos, 12, 35))
        
        # Fonts
        font_mega = pygame.font.Font(None, 130)
        font_title = pygame.font.Font(None, 96)
        font_subtitle = pygame.font.Font(None, 56)
        font_text = pygame.font.Font(None, 40)
        font_small = pygame.font.Font(None, 34)
        
        # Main result panel with glassmorphism
        panel_width = 800
        panel_height = 480
        panel_x = SCREEN_WIDTH // 2 - panel_width // 2
        panel_y = SCREEN_HEIGHT // 2 - panel_height // 2 - 20
        
        # Panel layers for depth
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
        if winner == "thief":
            # Victory panel - green/gold theme
            pygame.draw.rect(panel_surface, (30, 60, 30, 200), panel_surface.get_rect(), border_radius=35)
            glow_color = (100, 255, 100, 180)
            
            # Animated border
            border_pulse = abs(math.sin(elapsed / 400)) * 3 + 2
            for i in range(int(border_pulse)):
                alpha = int(150 - i * 30)
                pygame.draw.rect(panel_surface, (*glow_color[:3], alpha), 
                               (i, i, panel_width - i*2, panel_height - i*2), 5 - i, border_radius=35)
        else:
            # Game Over panel - red theme
            pygame.draw.rect(panel_surface, (60, 20, 20, 200), panel_surface.get_rect(), border_radius=35)
            glow_color = (255, 50, 50, 180)
            
            # Flashing border
            border_flash = abs(math.sin(elapsed / 200)) * 3 + 2
            for i in range(int(border_flash)):
                alpha = int(150 - i * 30)
                pygame.draw.rect(panel_surface, (*glow_color[:3], alpha), 
                               (i, i, panel_width - i*2, panel_height - i*2), 5 - i, border_radius=35)
        
        # Inner highlight
        pygame.draw.rect(panel_surface, (255, 255, 255, 40), 
                        (8, 8, panel_width - 16, panel_height - 16), 2, border_radius=30)
        
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Result title with spectacular effects
        if winner == "thief":
            # VICTORY with bouncing animation
            bounce = abs(math.sin(elapsed / 250) * 15)
            rotate_offset = math.sin(elapsed / 300) * 3
            
            title_y = panel_y + 80 + bounce
            
            # 3D shadow layers
            for depth in range(10, 0, -1):
                shadow_color = (10 + depth * 3, 40 + depth * 5, 10 + depth * 2)
                shadow = font_mega.render("VICTORY!", True, shadow_color)
                shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + depth, title_y + depth))
                screen.blit(shadow, shadow_rect)
            
            # Glowing outline
            glow_intensity = abs(math.sin(elapsed / 300)) * 100 + 150
            for offset in [(-4, -4), (4, -4), (-4, 4), (4, 4), (-5, 0), (5, 0), (0, -5), (0, 5)]:
                glow = font_mega.render("VICTORY!", True, (100, int(glow_intensity), 50))
                glow_rect = glow.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], title_y + offset[1]))
                screen.blit(glow, glow_rect)
            
            # Main title - gradient effect
            title = font_mega.render("VICTORY!", True, (255, 255, 100))
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, title_y))
            screen.blit(title, title_rect)
            
            # Trophy icons with float
            trophy_bounce = abs(math.sin(elapsed / 200) * 8)
            trophy_font = pygame.font.Font(None, 90)
            trophy_left = trophy_font.render("🏆", True, (255, 215, 0))
            trophy_right = trophy_font.render("🏆", True, (255, 215, 0))
            screen.blit(trophy_left, (panel_x + 60, title_y - 20 + trophy_bounce))
            screen.blit(trophy_right, (panel_x + panel_width - 120, title_y - 20 - trophy_bounce))
            
            # Subtitle with shimmer
            subtitle_y = panel_y + 180
            subtitle = font_subtitle.render("You Escaped the Police!", True, (200, 255, 200))
            
            # Shimmer effect
            shimmer_pos = (elapsed // 15) % (subtitle.get_width() + 150) - 75
            shimmer_surf = pygame.Surface((60, subtitle.get_height()), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(120 * (1 - abs(i - 30) / 30))
                pygame.draw.line(shimmer_surf, (255, 255, 255, alpha), (i, 0), (i, subtitle.get_height()))
            
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, subtitle_y))
            screen.blit(subtitle, subtitle_rect)
            screen.blit(shimmer_surf, (subtitle_rect.x + shimmer_pos, subtitle_rect.y))
            
            # Animated stats with checkmarks appearing
            stats_y = panel_y + 250
            stats_data = [
                ("✓", "Mission Complete", (100, 255, 100)),
                ("✓", "Freedom Achieved", (255, 255, 100)),
                ("✓", "Police Outrun Successfully", (100, 255, 255))
            ]
            
            for idx, (icon, text, color) in enumerate(stats_data):
                stat_y = stats_y + idx * 50
                delay = idx * 500
                
                if elapsed > delay:
                    # Slide in animation
                    slide_progress = min(1.0, (elapsed - delay) / 300)
                    slide_x = int(-200 * (1 - slide_progress))
                    
                    # Icon with glow
                    icon_x = panel_x + 120 + slide_x
                    icon_surf = pygame.Surface((45, 45), pygame.SRCALPHA)
                    pygame.draw.circle(icon_surf, (*color, 200), (22, 22), 20)
                    pygame.draw.circle(icon_surf, (255, 255, 255), (22, 22), 20, 2)
                    screen.blit(icon_surf, (icon_x, stat_y - 5))
                    
                    icon_text = font_text.render(icon, True, (0, 100, 0))
                    icon_rect = icon_text.get_rect(center=(icon_x + 22, stat_y + 15))
                    screen.blit(icon_text, icon_rect)
                    
                    # Text
                    stat_text = font_text.render(text, True, color)
                    stat_rect = stat_text.get_rect(midleft=(icon_x + 55, stat_y + 15))
                    screen.blit(stat_text, stat_rect)
        
        else:
            # BUSTED with shake effect
            shake_x = random.randint(-4, 4) if (elapsed // 100) % 2 else 0
            shake_y = random.randint(-3, 3) if (elapsed // 100) % 2 else 0
            
            title_y = panel_y + 80
            
            # 3D shadow layers
            for depth in range(10, 0, -1):
                shadow_color = (60 + depth * 2, 10, 10)
                shadow = font_mega.render("BUSTED!", True, shadow_color)
                shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + depth + shake_x, 
                                                      title_y + depth + shake_y))
                screen.blit(shadow, shadow_rect)
            
            # Red pulsing glow
            glow_intensity = abs(math.sin(elapsed / 200)) * 100 + 150
            for offset in [(-4, -4), (4, -4), (-4, 4), (4, 4), (-6, 0), (6, 0), (0, -6), (0, 6)]:
                glow = font_mega.render("BUSTED!", True, (int(glow_intensity), 50, 50))
                glow_rect = glow.get_rect(center=(SCREEN_WIDTH // 2 + offset[0] + shake_x, 
                                                  title_y + offset[1] + shake_y))
                screen.blit(glow, glow_rect)
            
            # Main title
            title = font_mega.render("BUSTED!", True, (255, 80, 80))
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2 + shake_x, title_y + shake_y))
            screen.blit(title, title_rect)
            
            # Police car icons with flash
            flash = (elapsed // 150) % 2
            car_font = pygame.font.Font(None, 90)
            car_color = (255, 100, 100) if flash else (100, 150, 255)
            police_left = car_font.render("🚔", True, car_color)
            police_right = car_font.render("🚔", True, car_color)
            screen.blit(police_left, (panel_x + 60, title_y - 20))
            screen.blit(police_right, (panel_x + panel_width - 120, title_y - 20))
            
            # Subtitle
            subtitle_y = panel_y + 180
            subtitle = font_subtitle.render("The Police Caught You!", True, (255, 200, 200))
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, subtitle_y))
            screen.blit(subtitle, subtitle_rect)
            
            # Game over messages
            messages_y = panel_y + 250
            messages_data = [
                ("✗", "Mission Failed", (255, 100, 100)),
                ("✗", "Caught by Police", (255, 150, 100)),
                ("↻", "Try Again!", (255, 200, 100))
            ]
            
            for idx, (icon, text, color) in enumerate(messages_data):
                msg_y = messages_y + idx * 50
                
                # Icon
                icon_x = panel_x + 150
                icon_surf = pygame.Surface((45, 45), pygame.SRCALPHA)
                pygame.draw.circle(icon_surf, (*color, 180), (22, 22), 20)
                pygame.draw.circle(icon_surf, (200, 100, 100), (22, 22), 20, 2)
                screen.blit(icon_surf, (icon_x, msg_y - 5))
                
                icon_text = font_text.render(icon, True, (100, 0, 0))
                icon_rect = icon_text.get_rect(center=(icon_x + 22, msg_y + 15))
                screen.blit(icon_text, icon_rect)
                
                # Text
                msg_text = font_text.render(text, True, color)
                msg_rect = msg_text.get_rect(midleft=(icon_x + 55, msg_y + 15))
                screen.blit(msg_text, msg_rect)
        
        # Action buttons at bottom
        button_y = panel_y + panel_height + 40
        flash_cycle = (elapsed // 350) % 3
        
        # Restart button
        if flash_cycle < 2:
            button_scale = 1 + math.sin(elapsed / 180) * 0.04
            
            # Button surface
            restart_btn = pygame.Surface((280, 60), pygame.SRCALPHA)
            if winner == "thief":
                pygame.draw.rect(restart_btn, (100, 255, 100, 220), restart_btn.get_rect(), border_radius=30)
                pygame.draw.rect(restart_btn, (150, 255, 150), restart_btn.get_rect(), 3, border_radius=30)
            else:
                pygame.draw.rect(restart_btn, (255, 150, 100, 220), restart_btn.get_rect(), border_radius=30)
                pygame.draw.rect(restart_btn, (255, 200, 150), restart_btn.get_rect(), 3, border_radius=30)
            
            # Scale and position
            scaled_btn = pygame.transform.scale(restart_btn, 
                                               (int(280 * button_scale), int(60 * button_scale)))
            btn_rect = scaled_btn.get_rect(center=(SCREEN_WIDTH // 2 - 180, button_y))
            screen.blit(scaled_btn, btn_rect)
            
            # Text
            restart_text = font_text.render("SPACE - Restart", True, (0, 50, 0) if winner == "thief" else (100, 30, 0))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2 - 180, button_y))
            screen.blit(restart_text, restart_rect)
        
        # Exit button
        exit_btn = pygame.Surface((280, 60), pygame.SRCALPHA)
        pygame.draw.rect(exit_btn, (100, 100, 120, 180), exit_btn.get_rect(), border_radius=30)
        pygame.draw.rect(exit_btn, (150, 150, 170), exit_btn.get_rect(), 2, border_radius=30)
        screen.blit(exit_btn, (SCREEN_WIDTH // 2 - 140 + 180, button_y - 30))
        
        exit_text = font_text.render("ESC - Exit", True, (200, 200, 220))
        exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH // 2 + 180, button_y))
        screen.blit(exit_text, exit_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return waiting

def main():
    """Main game loop"""
    clock = pygame.time.Clock()
    
    # Initialize CSP solver for AI decision making
    csp_solver = CSPDecisionMaker()
    
    while True:
        if not show_start_screen(screen):
            break
        
        # Initialize game objects
        player = Vehicle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150, RED, is_player=True)
        police = Vehicle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 300, BLUE, is_police=True)
        
        # Set initial distances - police starts behind the player
        player.distance = 0
        police.distance = -300  # Police starts 300 units behind
        
        # Increased traffic cars for more challenge
        traffic_cars = []
        for i in range(50):  # Increased from 20 to 50
            lane = random.randint(0, 2)
            distance = random.randint(500, FINISH_LINE_DISTANCE - 500)
            traffic_cars.append(TrafficCar(lane, distance))
        
        # Spawn power-ups along the track
        powerups = []
        
        # Thief power-ups (blue/green theme)
        thief_power_types = ['freeze', 'boost', 'shield', 'ghost']
        for i in range(35):  # 35 thief power-ups
            lane = random.randint(0, 2)
            distance = random.randint(1000, FINISH_LINE_DISTANCE - 1000)
            power_type = random.choice(thief_power_types)
            powerups.append(PowerUp(lane, distance, power_type, for_police=False))
        
        # Police power-ups (red theme - police only)
        police_power_types = ['spike', 'emp', 'turbo', 'roadblock', 'magnet']
        for i in range(25):  # 25 police power-ups
            lane = random.randint(0, 2)
            distance = random.randint(1000, FINISH_LINE_DISTANCE - 1000)
            power_type = random.choice(police_power_types)
            powerups.append(PowerUp(lane, distance, power_type, for_police=True))
        
        camera_offset = 0
        game_over = False
        winner = None
        
        # Thief power-up timers
        freeze_timer = 0
        boost_timer = 0
        shield_timer = 0
        ghost_timer = 0
        
        # Police power-up timers
        spike_timer = 0
        emp_timer = 0
        turbo_timer = 0
        roadblock_timer = 0
        magnet_timer = 0
        
        # Police power-up effects
        spike_active = False  # Slows down thief when hit
        roadblock_lane = -1  # Which lane has roadblock (-1 = none)
        
        # Score and combo
        powerups_collected = 0
        combo_multiplier = 1
        
        # Game loop
        running = True
        while running and not game_over:
            clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    game_over = True
            
            # Update power-up timers
            # Thief timers
            if freeze_timer > 0:
                freeze_timer -= 1
            if boost_timer > 0:
                boost_timer -= 1
            if shield_timer > 0:
                shield_timer -= 1
                player.shield_active = True
            else:
                player.shield_active = False
            if ghost_timer > 0:
                ghost_timer -= 1
                player.ghost_mode = True
            else:
                player.ghost_mode = False
            
            # Police timers
            if spike_timer > 0:
                spike_timer -= 1
                spike_active = True
            else:
                spike_active = False
            
            if emp_timer > 0:
                emp_timer -= 1
            
            if turbo_timer > 0:
                turbo_timer -= 1
            
            if roadblock_timer > 0:
                roadblock_timer -= 1
            else:
                roadblock_lane = -1
            
            if magnet_timer > 0:
                magnet_timer -= 1
            
            # Thief AI controls using CSP algorithm
            # Apply boost effect
            speed_multiplier = 1.5 if boost_timer > 0 else 1.0
            
            # EMP effect slows down thief
            if emp_timer > 0:
                speed_multiplier *= 0.5
            
            player.max_speed = 8 * speed_multiplier
            
            # Advanced CSP-based AI decision making for thief
            player.ai_decision_csp(
                traffic_cars=traffic_cars,
                powerups=powerups,
                opponent=police,
                ghost_mode=(ghost_timer > 0),
                csp_solver=csp_solver
            )
            
            # Add exhaust particles for thief
            if player.speed > 5 and random.random() < 0.3:
                # Calculate screen position for particles
                player_screen_y = player.distance - camera_offset + SCREEN_HEIGHT // 2
                particles.append(Particle(
                    player.x + random.randint(-15, 15),
                    player_screen_y + 40,
                    (100, 100, 100)
                ))
            
            # Update player
            player.distance += player.speed
            player.wheel_rotation += player.speed
            player.update_crash()  # Update crash state
            
            # Check power-up collisions for THIEF
            player_screen_y = SCREEN_HEIGHT // 2
            for powerup in powerups:
                # Thief can only collect thief powerups
                if not powerup.for_police and powerup.check_collision(player.x, player_screen_y, player.width, player.height, camera_offset):
                    powerups_collected += 1
                    
                    # Apply thief power-up effect
                    if powerup.power_type == 'freeze':
                        freeze_timer = 180  # 3 seconds at 60 FPS
                        # Create freeze particle effect
                        for _ in range(30):
                            particles.append(Particle(
                                police.x + random.randint(-30, 30),
                                SCREEN_HEIGHT // 2 + random.randint(-30, 30),
                                (100, 200, 255)
                            ))
                    elif powerup.power_type == 'boost':
                        boost_timer = 240  # 4 seconds
                        for _ in range(20):
                            particles.append(Particle(
                                player.x + random.randint(-25, 25),
                                player_screen_y + random.randint(-25, 25),
                                (255, 200, 0)
                            ))
                    elif powerup.power_type == 'shield':
                        shield_timer = 360  # 6 seconds
                        for _ in range(25):
                            particles.append(Particle(
                                player.x + random.randint(-30, 30),
                                player_screen_y + random.randint(-30, 30),
                                (150, 255, 150)
                            ))
                    elif powerup.power_type == 'ghost':
                        ghost_timer = 300  # 5 seconds
                        for _ in range(25):
                            particles.append(Particle(
                                player.x + random.randint(-30, 30),
                                player_screen_y + random.randint(-30, 30),
                                (200, 150, 255)
                            ))
            
            # Check power-up collisions for POLICE
            police_screen_y = police.distance - camera_offset + SCREEN_HEIGHT // 2
            for powerup in powerups:
                # Police can only collect police powerups
                if powerup.for_police and powerup.check_collision(police.x, police_screen_y, police.width, police.height, camera_offset):
                    
                    # Apply police power-up effect
                    if powerup.power_type == 'spike':
                        spike_timer = 240  # 4 seconds - creates spikes that slow thief
                        for _ in range(25):
                            particles.append(Particle(
                                police.x + random.randint(-30, 30),
                                police_screen_y + random.randint(-30, 30),
                                (255, 50, 50)
                            ))
                    elif powerup.power_type == 'emp':
                        emp_timer = 180  # 3 seconds - EMP slows thief's speed
                        for _ in range(30):
                            particles.append(Particle(
                                player.x + random.randint(-40, 40),
                                SCREEN_HEIGHT // 2 + random.randint(-40, 40),
                                (255, 100, 255)
                            ))
                    elif powerup.power_type == 'turbo':
                        turbo_timer = 300  # 5 seconds - police speed boost
                        for _ in range(20):
                            particles.append(Particle(
                                police.x + random.randint(-25, 25),
                                police_screen_y + random.randint(-25, 25),
                                (255, 150, 0)
                            ))
                    elif powerup.power_type == 'roadblock':
                        roadblock_timer = 420  # 7 seconds - blocks a lane
                        roadblock_lane = powerup.lane
                        for _ in range(30):
                            particles.append(Particle(
                                ROAD_X + roadblock_lane * LANE_WIDTH + LANE_WIDTH // 2 + random.randint(-40, 40),
                                SCREEN_HEIGHT // 2 + 200 + random.randint(-30, 30),
                                (200, 50, 50)
                            ))
                    elif powerup.power_type == 'magnet':
                        magnet_timer = 240  # 4 seconds - pulls thief toward police
                        for _ in range(25):
                            particles.append(Particle(
                                (player.x + police.x) // 2 + random.randint(-30, 30),
                                SCREEN_HEIGHT // 2 + random.randint(-30, 30),
                                (150, 150, 255)
                            ))
            
            # Update power-ups
            for powerup in powerups:
                powerup.update(camera_offset)
            
            # Police AI using CSP algorithm - affected by freeze power-up
            if freeze_timer > 0:
                # Police is frozen
                police.speed = 0
            elif not police.crashed:
                # Apply turbo boost for police
                turbo_multiplier = 1.5 if turbo_timer > 0 else 1.0
                police.max_speed = 8 * turbo_multiplier
                
                # Advanced CSP-based AI decision making for police
                police.ai_decision_csp(
                    traffic_cars=traffic_cars,
                    powerups=powerups,  # Police now cares about their powerups
                    opponent=player,
                    ghost_mode=False,  # Police doesn't have ghost mode
                    csp_solver=csp_solver
                )
            
            # Apply magnet effect - pull thief toward police
            if magnet_timer > 0 and not player.crashed:
                # Gradually pull thief toward police's x position
                if abs(police.x - player.x) > 10:
                    pull_strength = 2
                    if police.x < player.x:
                        player.x = max(ROAD_X + 35, player.x - pull_strength)
                    else:
                        player.x = min(ROAD_X + ROAD_WIDTH - 35, player.x + pull_strength)
            
            # Apply spike effect - slow down thief
            if spike_timer > 0 and not player.crashed:
                player.speed = max(player.speed - 0.1, player.max_speed * 0.6)
            
            police.distance += police.speed
            police.update_crash()  # Update crash state
            
            # Add police exhaust (with freeze effect)
            if freeze_timer > 0:
                # Frozen police - show ice particles
                if random.random() < 0.3:
                    police_screen_y = police.distance - camera_offset + SCREEN_HEIGHT // 2
                    particles.append(Particle(
                        police.x + random.randint(-20, 20),
                        police_screen_y + random.randint(-20, 20),
                        (150, 220, 255)
                    ))
            elif random.random() < 0.2:
                # Calculate screen position for particles
                police_screen_y = police.distance - camera_offset + SCREEN_HEIGHT // 2
                particles.append(Particle(
                    police.x + random.randint(-15, 15),
                    police_screen_y + 40,
                    (80, 80, 100)
                ))
            
            # Update traffic
            for car in traffic_cars:
                car.update()
            
            # Check roadblock collision with thief
            if roadblock_timer > 0 and roadblock_lane >= 0:
                thief_lane = csp_solver._get_current_lane(player.x)
                # If thief is in blocked lane and near roadblock position
                if thief_lane == roadblock_lane and not player.crashed:
                    # Roadblock is placed ahead of thief
                    roadblock_distance = player.distance + 300
                    if abs(player.distance - roadblock_distance) < 100:
                        # Hit the roadblock!
                        player.crash()
                        for _ in range(20):
                            particles.append(Particle(
                                player.x + random.randint(-30, 30),
                                SCREEN_HEIGHT // 2 + random.randint(-30, 30),
                                random.choice([RED, ORANGE, YELLOW])
                            ))
            
            # Check collisions with traffic cars
            for car in traffic_cars:
                # Check player collision with traffic (ghost mode allows pass-through)
                if not player.crashed and ghost_timer <= 0:
                    player_dist = math.sqrt((player.x - car.x)**2 + (player.distance - car.distance)**2)
                    if player_dist < 55:  # Collision threshold
                        # Shield protects from crashes
                        if shield_timer <= 0:
                            player.crash()
                            # Create crash effect particles
                            for _ in range(15):
                                particles.append(Particle(
                                    player.x + random.randint(-25, 25),
                                    SCREEN_HEIGHT // 2 + random.randint(-25, 25),
                                    random.choice([ORANGE, YELLOW, RED])
                                ))
                        else:
                            # Shield absorbed the hit - create shield spark effect
                            for _ in range(10):
                                particles.append(Particle(
                                    player.x + random.randint(-25, 25),
                                    SCREEN_HEIGHT // 2 + random.randint(-25, 25),
                                    (150, 255, 150)
                                ))
                
                # Check police collision with traffic
                if not police.crashed:
                    police_dist = math.sqrt((police.x - car.x)**2 + (police.distance - car.distance)**2)
                    if police_dist < 55:  # Collision threshold
                        police.crash()
                        # Create crash effect particles
                        for _ in range(15):
                            police_screen_y = police.distance - camera_offset + SCREEN_HEIGHT // 2
                            particles.append(Particle(
                                police.x + random.randint(-25, 25),
                                police_screen_y + random.randint(-25, 25),
                                random.choice([ORANGE, YELLOW, RED])
                            ))
            
            # Update particles
            for particle in particles[:]:
                particle.update()
                if particle.life <= 0:
                    particles.remove(particle)
            
            # Remove off-screen traffic and add new ones (maintain 50 cars)
            traffic_cars = [car for car in traffic_cars if car.distance > -500]
            while len(traffic_cars) < 50:  # Increased from 20 to 50
                lane = random.randint(0, 2)
                distance = player.distance + random.randint(1000, 2000)
                if distance < FINISH_LINE_DISTANCE:
                    traffic_cars.append(TrafficCar(lane, distance))
                else:
                    break
            
            # Camera follows player
            camera_offset = player.distance
            
            # Check collision with police
            dist_to_police = math.sqrt((player.x - police.x)**2 + (player.distance - police.distance)**2)
            if dist_to_police < 60:
                game_over = True
                winner = "police"
            
            # Check if player reached finish
            if player.distance >= FINISH_LINE_DISTANCE:
                game_over = True
                winner = "thief"
            
            # === DRAWING ===
            # Background scenery
            draw_background_scenery(screen, camera_offset)
            
            # Road
            draw_road(screen, camera_offset)
            
            # Speed lines for motion effect
            draw_speed_lines(screen, player.speed)
            
            # Finish line
            draw_finish_line(screen, camera_offset, FINISH_LINE_DISTANCE)
            
            # Particles
            for particle in particles:
                particle.draw(screen)
            
            # Power-ups
            for powerup in powerups:
                powerup.draw(screen, camera_offset)
            
            # Traffic cars
            for car in traffic_cars:
                car.draw(screen, camera_offset)
            
            # Police and player
            police.draw(screen, camera_offset)
            player.draw(screen, camera_offset)
            
            # HUD (drawn last to be on top)
            draw_hud(screen, player, police, traffic_cars, freeze_timer, boost_timer, shield_timer, ghost_timer, powerups_collected)
            
            pygame.display.flip()
        
        if not running:
            break
        
        # Clear particles before end screen
        particles.clear()
        
        if not show_end_screen(screen, winner):
            break
    
    pygame.quit()

if __name__ == "__main__":
    main()