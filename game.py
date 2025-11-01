import pygame
import random
import math
import os
import numpy as np

# Initialize Pygame
pygame.init()

# Initialize audio with more channels for layered sounds
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(16)  # Support multiple simultaneous sounds

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
FINISH_LINE_DISTANCE = 50000  # 50 KM track for balanced gameplay
LANE_WIDTH = ROAD_WIDTH // 3

# ============= PROFESSIONAL LAYERED AUDIO SYSTEM =============
class AudioManager:
    """
    Professional game audio system with layered sounds and dynamic mixing.
    Implements realistic racing game audio with:
    - Engine sounds (idle + rev loops)
    - Wind/road noise
    - Dynamic police siren (distance-based)
    - Collision/impact sounds
    - Power-up feedback
    - Menu and game music
    - Win/Lose themes
    """
    
    def __init__(self):
        self.sounds_dir = "sounds"
        self.sounds = {}
        self.channels = {}
        
        # Master volumes
        self.master_volume = 0.7
        self.music_volume = 0.4
        self.sfx_volume = 0.6
        
        # Audio channels (dedicated for each layer)
        self.channels['engine_idle'] = pygame.mixer.Channel(1)
        self.channels['engine_rev'] = pygame.mixer.Channel(2)
        self.channels['wind'] = pygame.mixer.Channel(3)
        self.channels['police_siren'] = pygame.mixer.Channel(4)
        self.channels['traffic_ambient'] = pygame.mixer.Channel(5)
        self.channels['crash'] = pygame.mixer.Channel(6)
        self.channels['powerup'] = pygame.mixer.Channel(7)
        self.channels['skid'] = pygame.mixer.Channel(8)
        
        # State tracking
        self.engine_running = False
        self.siren_playing = False
        self.current_speed_ratio = 0.0
        self.police_distance = 1000
        
        # Generate procedural sounds (fallback if no audio files)
        self._generate_procedural_sounds()
        
        # Try to load external sound files
        self._load_sound_files()
    
    def _generate_procedural_sounds(self):
        """Generate basic procedural sounds as fallback"""
        import numpy as np
        sample_rate = 44100
        
        # 1. ENGINE IDLE - Low rumble (40Hz base)
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        engine_idle = np.zeros_like(t)
        engine_idle += 0.3 * np.sin(2 * np.pi * 40 * t)
        engine_idle += 0.2 * np.sin(2 * np.pi * 80 * t)
        engine_idle += 0.15 * np.sin(2 * np.pi * 120 * t)
        engine_idle += 0.03 * np.random.uniform(-1, 1, len(t))
        
        # Smooth loop
        fade = int(0.1 * sample_rate)
        engine_idle[:fade] *= np.linspace(0, 1, fade)
        engine_idle[-fade:] *= np.linspace(1, 0, fade)
        
        engine_idle = np.clip(engine_idle, -1, 1)
        engine_idle = (engine_idle * 32767 * 0.4).astype(np.int16)
        engine_idle_stereo = np.column_stack((engine_idle, engine_idle))
        self.sounds['engine_idle'] = pygame.sndarray.make_sound(engine_idle_stereo)
        
        # 2. ENGINE REV - Higher pitched (80-200Hz sweep)
        duration = 1.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        engine_rev = np.zeros_like(t)
        
        # Variable frequency for rev sound
        freq_mod = 120 + 80 * np.sin(2 * np.pi * 2 * t)
        engine_rev = 0.35 * np.sin(2 * np.pi * freq_mod * t)
        engine_rev += 0.2 * np.sin(2 * np.pi * freq_mod * 2 * t)
        engine_rev += 0.05 * np.random.uniform(-1, 1, len(t))
        
        fade = int(0.05 * sample_rate)
        engine_rev[:fade] *= np.linspace(0, 1, fade)
        engine_rev[-fade:] *= np.linspace(1, 0, fade)
        
        engine_rev = np.clip(engine_rev, -1, 1)
        engine_rev = (engine_rev * 32767 * 0.3).astype(np.int16)
        engine_rev_stereo = np.column_stack((engine_rev, engine_rev))
        self.sounds['engine_rev'] = pygame.sndarray.make_sound(engine_rev_stereo)
        
        # 3. WIND/ROAD NOISE
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        wind = 0.15 * np.random.uniform(-1, 1, len(t))
        
        # Low-pass filter effect
        for i in range(1, len(wind)):
            wind[i] = 0.7 * wind[i] + 0.3 * wind[i-1]
        
        fade = int(0.2 * sample_rate)
        wind[:fade] *= np.linspace(0, 1, fade)
        wind[-fade:] *= np.linspace(1, 0, fade)
        
        wind = (wind * 32767).astype(np.int16)
        wind_stereo = np.column_stack((wind, wind))
        self.sounds['wind'] = pygame.sndarray.make_sound(wind_stereo)
        
        # 4. POLICE SIREN - Wail pattern
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        freq = 650 + 100 * np.sin(2 * np.pi * 1.5 * t)
        siren = 0.4 * np.sin(2 * np.pi * freq * t)
        siren += 0.15 * np.sin(2 * np.pi * freq * 2 * t)
        
        fade = int(0.15 * sample_rate)
        siren[:fade] *= np.linspace(0, 1, fade)
        siren[-fade:] *= np.linspace(1, 0, fade)
        
        siren = (siren * 32767 * 0.5).astype(np.int16)
        siren_stereo = np.column_stack((siren, siren))
        self.sounds['police_siren'] = pygame.sndarray.make_sound(siren_stereo)
        
        # 5. TRAFFIC AMBIENT
        duration = 4.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        traffic = np.zeros_like(t)
        traffic += 0.06 * np.sin(2 * np.pi * 55 * t * (1 + 0.2 * np.sin(2 * np.pi * 0.3 * t)))
        traffic += 0.04 * np.sin(2 * np.pi * 70 * t * (1 + 0.2 * np.sin(2 * np.pi * 0.5 * t)))
        traffic += 0.03 * np.random.uniform(-1, 1, len(t))
        
        fade = int(0.3 * sample_rate)
        traffic[:fade] *= np.linspace(0, 1, fade)
        traffic[-fade:] *= np.linspace(1, 0, fade)
        
        traffic = (traffic * 32767 * 0.3).astype(np.int16)
        traffic_stereo = np.column_stack((traffic, traffic))
        self.sounds['traffic_ambient'] = pygame.sndarray.make_sound(traffic_stereo)
        
        # 6. CRASH SOUND
        duration = 0.8
        t = np.linspace(0, duration, int(sample_rate * duration))
        crash = 0.7 * np.random.uniform(-1, 1, len(t)) * np.exp(-5 * t)
        crash += 0.3 * np.sin(2 * np.pi * 80 * t) * np.exp(-6 * t)
        crash = (crash * 32767 * 0.7).astype(np.int16)
        crash_stereo = np.column_stack((crash, crash))
        self.sounds['crash'] = pygame.sndarray.make_sound(crash_stereo)
        
        # 7. POWERUP PICKUP
        duration = 0.3
        t = np.linspace(0, duration, int(sample_rate * duration))
        freq_sweep = 400 + 600 * (t / duration)
        powerup = 0.4 * np.sin(2 * np.pi * freq_sweep * t) * np.exp(-4 * t)
        powerup = (powerup * 32767 * 0.5).astype(np.int16)
        powerup_stereo = np.column_stack((powerup, powerup))
        self.sounds['powerup'] = pygame.sndarray.make_sound(powerup_stereo)
        
        # 8. TIRE SKID
        duration = 0.6
        t = np.linspace(0, duration, int(sample_rate * duration))
        skid = 0.3 * np.random.uniform(-1, 1, len(t))
        skid += 0.2 * np.sin(2 * np.pi * 1400 * t * (1 + 0.1 * np.sin(2 * np.pi * 30 * t)))
        skid *= np.exp(-2 * t)
        skid = (skid * 32767 * 0.4).astype(np.int16)
        skid_stereo = np.column_stack((skid, skid))
        self.sounds['skid'] = pygame.sndarray.make_sound(skid_stereo)
        
        # 9. BOOST/TURBO
        duration = 0.7
        t = np.linspace(0, duration, int(sample_rate * duration))
        freq_sweep = 150 + 500 * (t / duration)**2
        boost = 0.5 * np.sin(2 * np.pi * freq_sweep * t)
        boost += 0.2 * np.random.uniform(-1, 1, len(t))
        boost *= np.exp(-1.2 * t)
        boost = (boost * 32767 * 0.5).astype(np.int16)
        boost_stereo = np.column_stack((boost, boost))
        self.sounds['boost'] = pygame.sndarray.make_sound(boost_stereo)
        
        print("✓ Procedural sounds generated")
    
    def _load_sound_files(self):
        """Try to load external sound files if available"""
        sound_files = {
            'engine_idle': 'engine_idle.wav',
            'engine_rev': 'engine_rev_loop.wav',
            'wind': 'wind_loop.wav',
            'police_siren': 'police_siren_loop.wav',
            'traffic_ambient': 'traffic_ambient.wav',
            'crash': 'crash.wav',
            'powerup': 'pickup.wav',
            'boost': 'boost.wav',
            'skid': 'skid.wav',
            'menu_music': 'menu_theme.mp3',
            'game_music': 'driving_music.mp3',
            'win_music': 'win_theme.mp3',
            'lose_music': 'lose_theme.mp3'
        }
        
        loaded_count = 0
        for key, filename in sound_files.items():
            filepath = os.path.join(self.sounds_dir, filename)
            if os.path.exists(filepath):
                try:
                    if filename.endswith('.mp3') or filename.endswith('.ogg'):
                        # Music files (don't load as Sound objects)
                        continue
                    else:
                        self.sounds[key] = pygame.mixer.Sound(filepath)
                        loaded_count += 1
                        print(f"✓ Loaded: {filename}")
                except Exception as e:
                    print(f"✗ Failed to load {filename}: {e}")
        
        if loaded_count > 0:
            print(f"✓ Loaded {loaded_count} external sound files")
        else:
            print("ℹ No external sound files found, using procedural sounds")
    
    def start_engine_layers(self):
        """Start all engine sound layers"""
        if not self.engine_running:
            if 'engine_idle' in self.sounds:
                self.channels['engine_idle'].play(self.sounds['engine_idle'], loops=-1)
                self.channels['engine_idle'].set_volume(0.5 * self.sfx_volume * self.master_volume)
            
            if 'engine_rev' in self.sounds:
                self.channels['engine_rev'].play(self.sounds['engine_rev'], loops=-1)
                self.channels['engine_rev'].set_volume(0.0)  # Start silent
            
            if 'wind' in self.sounds:
                self.channels['wind'].play(self.sounds['wind'], loops=-1)
                self.channels['wind'].set_volume(0.0)  # Start silent
            
            self.engine_running = True
            print("🏎️ Engine layers started")
    
    def stop_engine_layers(self):
        """Stop all engine sound layers"""
        if self.engine_running:
            self.channels['engine_idle'].stop()
            self.channels['engine_rev'].stop()
            self.channels['wind'].stop()
            self.engine_running = False
    
    def update_engine_sound(self, current_speed, max_speed):
        """
        Dynamically adjust engine layers based on speed.
        
        Low speed: High idle volume, low rev volume
        High speed: Low idle volume, high rev volume
        """
        if not self.engine_running:
            return
        
        speed_ratio = min(current_speed / max_speed, 1.0)
        self.current_speed_ratio = speed_ratio
        
        # Engine idle fades out as speed increases
        idle_volume = (1.0 - speed_ratio * 0.8) * 0.5 * self.sfx_volume * self.master_volume
        self.channels['engine_idle'].set_volume(idle_volume)
        
        # Engine rev fades in as speed increases
        rev_volume = speed_ratio * 0.6 * self.sfx_volume * self.master_volume
        self.channels['engine_rev'].set_volume(rev_volume)
        
        # Wind noise increases with speed
        wind_volume = speed_ratio * 0.4 * self.sfx_volume * self.master_volume
        self.channels['wind'].set_volume(wind_volume)
    
    def start_traffic_ambient(self):
        """Start ambient traffic sound"""
        if 'traffic_ambient' in self.sounds:
            self.channels['traffic_ambient'].play(self.sounds['traffic_ambient'], loops=-1)
            self.channels['traffic_ambient'].set_volume(0.25 * self.sfx_volume * self.master_volume)
    
    def stop_traffic_ambient(self):
        """Stop traffic ambient"""
        self.channels['traffic_ambient'].stop()
    
    def update_police_siren(self, police_distance):
        """
        Dynamic police siren based on distance.
        Only plays when police is close (<350 units)
        Volume increases as police gets closer
        """
        self.police_distance = police_distance
        
        if police_distance < 350:
            # Police is close - play siren
            if not self.siren_playing:
                if 'police_siren' in self.sounds:
                    self.channels['police_siren'].play(self.sounds['police_siren'], loops=-1)
                    self.siren_playing = True
            
            # Calculate volume based on distance
            # Full volume at <150, fade out to 350
            if police_distance < 150:
                volume = 1.0
            else:
                volume = 1.0 - ((police_distance - 150) / 200)
            
            self.channels['police_siren'].set_volume(volume * 0.5 * self.sfx_volume * self.master_volume)
        else:
            # Police is far - fade out siren
            if self.siren_playing:
                self.channels['police_siren'].fadeout(800)
                self.siren_playing = False
    
    def play_crash(self):
        """Play crash sound"""
        if 'crash' in self.sounds:
            self.channels['crash'].play(self.sounds['crash'])
            self.channels['crash'].set_volume(0.7 * self.sfx_volume * self.master_volume)
    
    def play_powerup(self):
        """Play powerup pickup sound"""
        if 'powerup' in self.sounds:
            self.channels['powerup'].play(self.sounds['powerup'])
            self.channels['powerup'].set_volume(0.5 * self.sfx_volume * self.master_volume)
    
    def play_boost(self):
        """Play boost/turbo sound"""
        if 'boost' in self.sounds:
            # Use a free channel for boost (not dedicated)
            boost_channel = pygame.mixer.find_channel()
            if boost_channel:
                boost_channel.play(self.sounds['boost'])
                boost_channel.set_volume(0.6 * self.sfx_volume * self.master_volume)
    
    def play_skid(self):
        """Play tire skid sound"""
        if 'skid' in self.sounds and not self.channels['skid'].get_busy():
            self.channels['skid'].play(self.sounds['skid'])
            self.channels['skid'].set_volume(0.4 * self.sfx_volume * self.master_volume)
    
    def play_menu_music(self):
        """Play menu theme music"""
        music_file = os.path.join(self.sounds_dir, 'menu_theme.mp3')
        if os.path.exists(music_file):
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            pygame.mixer.music.play(-1)
            print("🎵 Menu music playing")
    
    def play_game_music(self):
        """Play in-game racing music"""
        pygame.mixer.music.fadeout(1200)
        pygame.time.wait(1300)
        
        music_file = os.path.join(self.sounds_dir, 'driving_music.mp3')
        if os.path.exists(music_file):
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume * 0.7)
            pygame.mixer.music.play(-1)
            print("🎵 Game music playing")
    
    def play_win_music(self):
        """Play victory music"""
        pygame.mixer.music.fadeout(1000)
        pygame.time.wait(1100)
        
        music_file = os.path.join(self.sounds_dir, 'win_theme.mp3')
        if os.path.exists(music_file):
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            pygame.mixer.music.play()
            print("🎵 Win music playing")
    
    def play_lose_music(self):
        """Play defeat music"""
        pygame.mixer.music.fadeout(1000)
        pygame.time.wait(1100)
        
        music_file = os.path.join(self.sounds_dir, 'lose_theme.mp3')
        if os.path.exists(music_file):
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            pygame.mixer.music.play()
            print("🎵 Lose music playing")
    
    def stop_all_sounds(self):
        """Stop all sound effects and music"""
        self.stop_engine_layers()
        self.stop_traffic_ambient()
        if self.siren_playing:
            self.channels['police_siren'].stop()
            self.siren_playing = False
        pygame.mixer.music.stop()

# Create global audio manager
try:
    import numpy as np
    audio_manager = AudioManager()
    print("🔊 Audio Manager initialized successfully")
except Exception as e:
    print(f"⚠️ Audio Manager initialization failed: {e}")
    # Create dummy audio manager
    class DummyAudioManager:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    audio_manager = DummyAudioManager()

# Fuzzy Logic System for Realistic AI Decision Making
class FuzzyLogicController:
    """
    Advanced Fuzzy Logic system for human-like AI behavior.
    Handles uncertainty and gradual decision-making for realistic driving.
    """
    
    def __init__(self):
        self.lane_positions = [
            ROAD_X + LANE_WIDTH // 2,
            ROAD_X + LANE_WIDTH + LANE_WIDTH // 2,
            ROAD_X + 2 * LANE_WIDTH + LANE_WIDTH // 2
        ]
    
    # ============= MEMBERSHIP FUNCTIONS =============
    
    def triangular_membership(self, value, left, peak, right):
        """Triangular membership function"""
        if value <= left or value >= right:
            return 0.0
        elif value == peak:
            return 1.0
        elif value < peak:
            return (value - left) / (peak - left)
        else:
            return (right - value) / (right - peak)
    
    def trapezoidal_membership(self, value, left, left_top, right_top, right):
        """Trapezoidal membership function"""
        if value <= left or value >= right:
            return 0.0
        elif left_top <= value <= right_top:
            return 1.0
        elif value < left_top:
            return (value - left) / (left_top - left)
        else:
            return (right - value) / (right - right_top)
    
    # ============= FUZZIFICATION: Distance to Traffic =============
    
    def fuzzify_distance_to_traffic(self, distance):
        """
        CRITICAL: Fuzzify distance to nearest traffic car ahead.
        ENHANCED: React MUCH earlier to avoid crashes!
        Returns membership values for: VeryClose, Close, Medium, Far, VeryFar
        """
        return {
            'VeryClose': self.trapezoidal_membership(distance, 0, 0, 80, 160),  # Wider critical zone (was 50-100)
            'Close': self.triangular_membership(distance, 130, 220, 310),  # Earlier reaction (was 80-220)
            'Medium': self.triangular_membership(distance, 250, 380, 510),  # More warning (was 180-370)
            'Far': self.triangular_membership(distance, 450, 600, 750),  # Look further (was 300-600)
            'VeryFar': self.trapezoidal_membership(distance, 650, 800, 10000, 10000)  # Extended range (was 500-600)
        }
    
    # ============= FUZZIFICATION: Opponent Proximity =============
    
    def fuzzify_opponent_proximity(self, distance):
        """
        Fuzzify distance to opponent.
        Returns membership values for: ExtremelyClose, Close, Medium, Far, VeryFar
        """
        return {
            'ExtremelyClose': self.trapezoidal_membership(distance, 0, 0, 30, 60),
            'Close': self.triangular_membership(distance, 40, 100, 170),
            'Medium': self.triangular_membership(distance, 120, 225, 330),
            'Far': self.triangular_membership(distance, 250, 450, 650),
            'VeryFar': self.trapezoidal_membership(distance, 500, 700, 10000, 10000)
        }
    
    # ============= FUZZIFICATION: Current Speed =============
    
    def fuzzify_speed(self, speed, max_speed):
        """
        Fuzzify current speed relative to max speed.
        Returns membership values for: VerySlow, Slow, Medium, Fast, VeryFast
        """
        speed_ratio = speed / max_speed if max_speed > 0 else 0
        
        return {
            'VerySlow': self.trapezoidal_membership(speed_ratio, 0, 0, 0.3, 0.4),
            'Slow': self.triangular_membership(speed_ratio, 0.3, 0.5, 0.65),
            'Medium': self.triangular_membership(speed_ratio, 0.55, 0.7, 0.85),
            'Fast': self.triangular_membership(speed_ratio, 0.75, 0.9, 1.0),
            'VeryFast': self.trapezoidal_membership(speed_ratio, 0.9, 0.95, 1.2, 1.2)
        }
    
    # ============= FUZZIFICATION: Road Clearance =============
    
    def fuzzify_road_clearance(self, clear_lanes):
        """
        Fuzzify number of clear lanes ahead.
        Returns membership values for: Blocked, PartiallyBlocked, Clear
        """
        return {
            'Blocked': 1.0 if clear_lanes == 0 else 0.5 if clear_lanes == 1 else 0.0,
            'PartiallyBlocked': self.triangular_membership(clear_lanes, 0, 1, 2),
            'Clear': 1.0 if clear_lanes >= 2 else 0.5 if clear_lanes == 1 else 0.0
        }
    
    # ============= FUZZIFICATION: Lane Change Urgency =============
    
    def fuzzify_lane_urgency(self, distance_to_obstacle):
        """
        CRITICAL: Fuzzify urgency to change lanes.
        ENHANCED: Much more aggressive thresholds for crash prevention!
        Returns membership values for: Low, Medium, High, Critical
        """
        return {
            'Low': self.trapezoidal_membership(distance_to_obstacle, 600, 700, 10000, 10000),  # React earlier!
            'Medium': self.triangular_membership(distance_to_obstacle, 350, 450, 600),  # More warning
            'High': self.triangular_membership(distance_to_obstacle, 150, 250, 400),  # Urgent sooner
            'Critical': self.trapezoidal_membership(distance_to_obstacle, 0, 0, 140, 220)  # Wider critical zone
        }
    
    # ============= FUZZIFICATION: Lane Safety =============
    
    def fuzzify_lane_safety(self, min_clearance):
        """
        Fuzzify safety level of a lane.
        Returns membership values for: Dangerous, Risky, Safe, VerySafe
        """
        return {
            'Dangerous': self.trapezoidal_membership(min_clearance, 0, 0, 80, 130),
            'Risky': self.triangular_membership(min_clearance, 100, 200, 320),
            'Safe': self.triangular_membership(min_clearance, 280, 400, 520),
            'VerySafe': self.trapezoidal_membership(min_clearance, 450, 550, 10000, 10000)
        }
    
    # ============= FUZZIFICATION: Traffic Density =============
    
    def fuzzify_traffic_density(self, traffic_count):
        """
        Fuzzify traffic density in a lane.
        Returns membership values for: Empty, Light, Moderate, Heavy, Congested
        """
        return {
            'Empty': 1.0 if traffic_count == 0 else 0.0,
            'Light': self.triangular_membership(traffic_count, 0, 1, 2),
            'Moderate': self.triangular_membership(traffic_count, 1, 2, 4),
            'Heavy': self.triangular_membership(traffic_count, 3, 5, 7),
            'Congested': self.trapezoidal_membership(traffic_count, 6, 8, 20, 20)
        }
    
    # ============= FUZZY RULES: Speed Control =============
    
    def evaluate_speed_rules(self, distance_fuzzy, opponent_fuzzy, speed_fuzzy, 
                            clearance_fuzzy, is_police):
        """
        Evaluate fuzzy rules for speed control.
        Returns fuzzy output for acceleration command.
        """
        rules_output = {
            'StrongBrake': 0.0,
            'LightBrake': 0.0,
            'Maintain': 0.0,
            'LightAccelerate': 0.0,
            'StrongAccelerate': 0.0
        }
        
        # CRITICAL SAFETY RULES (highest priority)
        # Rule 1: If traffic is VeryClose AND speed is Fast -> StrongBrake
        strength = min(distance_fuzzy['VeryClose'], speed_fuzzy['Fast'])
        rules_output['StrongBrake'] = max(rules_output['StrongBrake'], strength)
        
        # Rule 2: If traffic is VeryClose AND speed is Medium -> StrongBrake
        strength = min(distance_fuzzy['VeryClose'], speed_fuzzy['Medium'])
        rules_output['StrongBrake'] = max(rules_output['StrongBrake'], strength)
        
        # Rule 3: If traffic is Close AND speed is VeryFast -> StrongBrake
        strength = min(distance_fuzzy['Close'], speed_fuzzy['VeryFast'])
        rules_output['StrongBrake'] = max(rules_output['StrongBrake'], strength)
        
        # Rule 4: If road is Blocked AND speed is Fast -> StrongBrake
        strength = min(clearance_fuzzy['Blocked'], speed_fuzzy['Fast'])
        rules_output['StrongBrake'] = max(rules_output['StrongBrake'], strength)
        
        # MODERATE BRAKING RULES
        # Rule 5: If traffic is Close AND speed is Medium -> LightBrake
        strength = min(distance_fuzzy['Close'], speed_fuzzy['Medium'])
        rules_output['LightBrake'] = max(rules_output['LightBrake'], strength)
        
        # Rule 6: If traffic is Medium AND speed is VeryFast -> LightBrake
        strength = min(distance_fuzzy['Medium'], speed_fuzzy['VeryFast'])
        rules_output['LightBrake'] = max(rules_output['LightBrake'], strength)
        
        # Rule 7: If road is PartiallyBlocked AND speed is Fast -> LightBrake
        strength = min(clearance_fuzzy['PartiallyBlocked'], speed_fuzzy['Fast'])
        rules_output['LightBrake'] = max(rules_output['LightBrake'], strength)
        
        # MAINTAIN SPEED RULES
        # Rule 8: If traffic is Medium AND speed is Medium -> Maintain
        strength = min(distance_fuzzy['Medium'], speed_fuzzy['Medium'])
        rules_output['Maintain'] = max(rules_output['Maintain'], strength)
        
        # Rule 9: If traffic is Far AND speed is Fast -> Maintain
        strength = min(distance_fuzzy['Far'], speed_fuzzy['Fast'])
        rules_output['Maintain'] = max(rules_output['Maintain'], strength)
        
        # ACCELERATION RULES
        # Rule 10: If traffic is Far AND speed is Slow -> LightAccelerate
        strength = min(distance_fuzzy['Far'], speed_fuzzy['Slow'])
        rules_output['LightAccelerate'] = max(rules_output['LightAccelerate'], strength)
        
        # Rule 11: If traffic is VeryFar AND road is Clear AND speed is Medium -> StrongAccelerate
        strength = min(distance_fuzzy['VeryFar'], clearance_fuzzy['Clear'], speed_fuzzy['Medium'])
        rules_output['StrongAccelerate'] = max(rules_output['StrongAccelerate'], strength)
        
        # Rule 12: If traffic is VeryFar AND road is Clear AND speed is Slow -> StrongAccelerate
        strength = min(distance_fuzzy['VeryFar'], clearance_fuzzy['Clear'], speed_fuzzy['Slow'])
        rules_output['StrongAccelerate'] = max(rules_output['StrongAccelerate'], strength)
        
        # Rule 13: If traffic is Far AND speed is VerySlow -> StrongAccelerate
        strength = min(distance_fuzzy['Far'], speed_fuzzy['VerySlow'])
        rules_output['StrongAccelerate'] = max(rules_output['StrongAccelerate'], strength)
        
        # OPPONENT-SPECIFIC RULES
        if is_police:
            # Police: Match opponent speed when close
            # Rule 14: If opponent is ExtremelyClose AND speed is VeryFast -> LightBrake
            strength = min(opponent_fuzzy['ExtremelyClose'], speed_fuzzy['VeryFast'])
            rules_output['LightBrake'] = max(rules_output['LightBrake'], strength)
            
            # Rule 15: If opponent is Close AND speed is Slow -> LightAccelerate
            strength = min(opponent_fuzzy['Close'], speed_fuzzy['Slow'])
            rules_output['LightAccelerate'] = max(rules_output['LightAccelerate'], strength)
        else:
            # Thief: Careful approach when police is close
            # Rule 16: If opponent is ExtremelyClose AND traffic is Close -> LightBrake
            strength = min(opponent_fuzzy['ExtremelyClose'], distance_fuzzy['Close'])
            rules_output['LightBrake'] = max(rules_output['LightBrake'], strength)
            
            # Rule 17: If opponent is VeryFar AND traffic is Far -> StrongAccelerate
            strength = min(opponent_fuzzy['VeryFar'], distance_fuzzy['Far'])
            rules_output['StrongAccelerate'] = max(rules_output['StrongAccelerate'], strength)
        
        return rules_output
    
    # ============= FUZZY RULES: Lane Change Decision =============
    
    def evaluate_lane_change_rules(self, current_safety_fuzzy, target_density_fuzzy,
                                   urgency_fuzzy, target_safety_fuzzy):
        """
        Evaluate fuzzy rules for lane change confidence.
        Returns fuzzy output for lane change decision.
        """
        rules_output = {
            'VeryLow': 0.0,
            'Low': 0.0,
            'Medium': 0.0,
            'High': 0.0,
            'VeryHigh': 0.0
        }
        
        # CRITICAL LANE CHANGE RULES
        # Rule 1: If current lane is Dangerous AND target traffic is NOT Congested -> VeryHigh
        strength = min(current_safety_fuzzy['Dangerous'], 
                      1.0 - target_density_fuzzy['Congested'])
        rules_output['VeryHigh'] = max(rules_output['VeryHigh'], strength)
        
        # Rule 2: If urgency is Critical AND target is NOT Heavy -> VeryHigh
        strength = min(urgency_fuzzy['Critical'], 
                      1.0 - target_density_fuzzy['Heavy'])
        rules_output['VeryHigh'] = max(rules_output['VeryHigh'], strength)
        
        # Rule 3: If current is Dangerous AND target is Safe -> High
        strength = min(current_safety_fuzzy['Dangerous'], target_safety_fuzzy['Safe'])
        rules_output['High'] = max(rules_output['High'], strength)
        
        # Rule 4: If urgency is High AND target traffic is Light -> High
        strength = min(urgency_fuzzy['High'], target_density_fuzzy['Light'])
        rules_output['High'] = max(rules_output['High'], strength)
        
        # MODERATE LANE CHANGE RULES
        # Rule 5: If current is Risky AND target is Safe -> Medium
        strength = min(current_safety_fuzzy['Risky'], target_safety_fuzzy['Safe'])
        rules_output['Medium'] = max(rules_output['Medium'], strength)
        
        # Rule 6: If urgency is Medium AND target is NOT Heavy -> Medium
        strength = min(urgency_fuzzy['Medium'], 
                      1.0 - target_density_fuzzy['Heavy'])
        rules_output['Medium'] = max(rules_output['Medium'], strength)
        
        # LOW LANE CHANGE RULES
        # Rule 7: If current is Safe AND urgency is Low -> VeryLow
        strength = min(current_safety_fuzzy['Safe'], urgency_fuzzy['Low'])
        rules_output['VeryLow'] = max(rules_output['VeryLow'], strength)
        
        # Rule 8: If target traffic is Heavy AND current is NOT Dangerous -> Low
        strength = min(target_density_fuzzy['Heavy'], 
                      1.0 - current_safety_fuzzy['Dangerous'])
        rules_output['Low'] = max(rules_output['Low'], strength)
        
        # Rule 9: If current is VerySafe AND target is Risky -> VeryLow
        strength = min(current_safety_fuzzy['VerySafe'], target_safety_fuzzy['Risky'])
        rules_output['VeryLow'] = max(rules_output['VeryLow'], strength)
        
        # Rule 10: If target is VerySafe AND urgency is High -> VeryHigh
        strength = min(target_safety_fuzzy['VerySafe'], urgency_fuzzy['High'])
        rules_output['VeryHigh'] = max(rules_output['VeryHigh'], strength)
        
        return rules_output
    
    # ============= DEFUZZIFICATION =============
    
    def defuzzify_acceleration(self, fuzzy_output):
        """
        Convert fuzzy acceleration output to crisp value.
        Uses center of gravity (centroid) method.
        """
        # Define crisp values for each fuzzy set
        crisp_values = {
            'StrongBrake': -0.7,
            'LightBrake': -0.3,
            'Maintain': 0.0,
            'LightAccelerate': 0.3,
            'StrongAccelerate': 0.6
        }
        
        # Calculate weighted average
        numerator = 0.0
        denominator = 0.0
        
        for fuzzy_set, membership in fuzzy_output.items():
            numerator += crisp_values[fuzzy_set] * membership
            denominator += membership
        
        if denominator == 0:
            return 0.0  # Default: maintain
        
        return numerator / denominator
    
    def defuzzify_lane_confidence(self, fuzzy_output):
        """
        Convert fuzzy lane change confidence to crisp percentage.
        Uses center of gravity (centroid) method.
        """
        # Define crisp values for each fuzzy set (0-100%)
        crisp_values = {
            'VeryLow': 10,
            'Low': 30,
            'Medium': 50,
            'High': 75,
            'VeryHigh': 95
        }
        
        # Calculate weighted average
        numerator = 0.0
        denominator = 0.0
        
        for fuzzy_set, membership in fuzzy_output.items():
            numerator += crisp_values[fuzzy_set] * membership
            denominator += membership
        
        if denominator == 0:
            return 0.0  # Default: don't change
        
        return numerator / denominator
    
    # ============= MAIN FUZZY CONTROL METHODS =============
    
    def get_fuzzy_speed_control(self, vehicle, traffic_cars, opponent, is_police):
        """
        PROPERLY IMPROVED: Fuzzy logic speed control with SMART crash avoidance.
        Key: Detect early, brake smoothly, avoid unnecessary speed changes.
        Returns acceleration value (-1.0 to +1.0)
        """
        current_lane = self.get_lane_from_x(vehicle.x)
        
        # Extended look-ahead for better prediction
        look_ahead = 600 + (vehicle.speed * 70)  # See far ahead
        
        # Analyze traffic in current lane with speed consideration
        min_traffic_distance = 10000
        obstacles_in_lane = 0
        closest_obstacle_speed = 2.0  # Assume slow traffic if unknown
        
        for car in traffic_cars:
            if car.lane == current_lane:
                dist = car.distance - vehicle.distance
                if 0 < dist < look_ahead:
                    obstacles_in_lane += 1
                    if dist < min_traffic_distance:
                        min_traffic_distance = dist
                        # Get obstacle speed if available
                        closest_obstacle_speed = car.speed if hasattr(car, 'speed') else 2.0
        
        # Calculate RELATIVE danger based on speed difference
        speed_difference = vehicle.speed - closest_obstacle_speed
        
        # SMART EMERGENCY DETECTION: Earlier braking when going much faster
        emergency_distance = 180 + (speed_difference * 30)  # More distance needed when faster
        emergency_brake = min_traffic_distance < emergency_distance
        
        # Traffic jam detection: multiple cars moderately close
        traffic_jam = False
        if obstacles_in_lane >= 2 and min_traffic_distance < 500:
            traffic_jam = True
        
        # Calculate opponent distance
        opponent_distance = abs(opponent.distance - vehicle.distance) if opponent else 10000
        
        # Count clear lanes for road clearance assessment
        clear_lanes = 0
        for lane_idx in range(3):
            has_traffic = False
            for car in traffic_cars:
                if car.lane == lane_idx:
                    dist = car.distance - vehicle.distance
                    if 0 < dist < look_ahead:
                        has_traffic = True
                        break
            if not has_traffic:
                clear_lanes += 1
        
        # FUZZIFICATION
        distance_fuzzy = self.fuzzify_distance_to_traffic(min_traffic_distance)
        opponent_fuzzy = self.fuzzify_opponent_proximity(opponent_distance)
        speed_fuzzy = self.fuzzify_speed(vehicle.speed, vehicle.max_speed)
        clearance_fuzzy = self.fuzzify_road_clearance(clear_lanes)
        
        # INFERENCE (apply fuzzy rules)
        fuzzy_output = self.evaluate_speed_rules(
            distance_fuzzy, opponent_fuzzy, speed_fuzzy, 
            clearance_fuzzy, is_police
        )
        
        # DEFUZZIFICATION
        acceleration = self.defuzzify_acceleration(fuzzy_output)
        
        # SMART MODIFIERS: Proper acceleration/braking control
        
        # 1. CRITICAL EMERGENCY: Obstacle very close - FULL BRAKE
        if min_traffic_distance < 120:
            acceleration = -1.0  # Maximum emergency brake
        
        # 2. EMERGENCY: Close obstacle and going fast - HARD BRAKE
        elif emergency_brake and speed_difference > 3.0:
            acceleration = min(acceleration, -0.85)  # Strong brake
        
        # 3. WARNING: Getting close - MODERATE BRAKE
        elif emergency_brake:
            acceleration = min(acceleration, -0.6)  # Moderate brake
        
        # 4. TRAFFIC JAM: Multiple cars ahead - GRADUAL SLOWDOWN
        elif traffic_jam:
            acceleration = min(acceleration, -0.35)  # Gentle brake
        
        # 5. MAINTAIN: Far obstacles - TRUST FUZZY OUTPUT
        # Don't override if obstacle is far enough away
        
        return acceleration
    
    def get_fuzzy_lane_decision(self, vehicle, traffic_cars, target_lane):
        """
        PROPERLY IMPROVED: Smart fuzzy lane change decision.
        Key: Only change lanes when NECESSARY and SAFE, avoid unnecessary moves.
        Returns confidence percentage (0-100)
        """
        current_lane = self.get_lane_from_x(vehicle.x)
        
        # Extended look-ahead for better prediction
        look_ahead_distance = 700 + (vehicle.speed * 80)
        
        # Speed-based safety margin (need more space when going faster)
        safety_margin = 220 + (vehicle.speed * 30)
        
        # === ANALYZE CURRENT LANE ===
        current_min_clearance = 10000
        current_immediate_danger = False
        obstacles_in_current = 0
        
        for car in traffic_cars:
            if car.lane == current_lane:
                dist = car.distance - vehicle.distance
                if 0 < dist < look_ahead_distance:
                    obstacles_in_current += 1
                    current_min_clearance = min(current_min_clearance, dist)
                    
                    # Real danger: obstacle within safety margin
                    if dist < safety_margin:
                        current_immediate_danger = True
        
        # === ANALYZE TARGET LANE ===
        target_min_clearance = 10000
        target_has_danger = False
        target_obstacles = 0
        side_collision_risk = False
        
        for car in traffic_cars:
            if car.lane == target_lane:
                dist = car.distance - vehicle.distance
                
                # Check ahead AND behind for safe lane change
                if -120 < dist < look_ahead_distance:
                    target_obstacles += 1
                    target_min_clearance = min(target_min_clearance, abs(dist))
                    
                    # Danger: obstacle too close in target lane
                    if abs(dist) < safety_margin:
                        target_has_danger = True
                    
                    # CRITICAL: Side-by-side collision risk
                    if -60 < dist < 60:
                        side_collision_risk = True
        
        # === FUZZIFICATION ===
        current_safety_fuzzy = self.fuzzify_lane_safety(current_min_clearance)
        target_safety_fuzzy = self.fuzzify_lane_safety(target_min_clearance)
        target_density_fuzzy = self.fuzzify_traffic_density(target_obstacles)
        urgency_fuzzy = self.fuzzify_lane_urgency(current_min_clearance)
        
        # === INFERENCE (apply rules) ===
        fuzzy_output = self.evaluate_lane_change_rules(
            current_safety_fuzzy, target_density_fuzzy,
            urgency_fuzzy, target_safety_fuzzy
        )
        
        # === DEFUZZIFICATION ===
        confidence = self.defuzzify_lane_confidence(fuzzy_output)
        
        # === SMART MODIFIERS ===
        
        # 1. NEVER change if side collision risk
        if side_collision_risk:
            return 0  # Absolutely NO lane change
        
        # 2. NEVER change if target has immediate danger
        if target_has_danger:
            confidence = max(0, confidence - 80)  # Heavy penalty
        
        # 3. ONLY change if current lane has real danger
        if not current_immediate_danger:
            confidence = max(0, confidence - 40)  # Prefer staying in lane
        
        # 4. BOOST if current lane blocked and target clear
        if current_immediate_danger and not target_has_danger and target_min_clearance > 400:
            confidence += 50  # Strong incentive to escape danger
        
        # 5. PENALTY if target lane more crowded than current
        if target_obstacles > obstacles_in_current and not current_immediate_danger:
            confidence -= 30  # Don't move to worse lane
        
        # Ensure confidence stays in valid range
        confidence = max(0, min(100, confidence))
        
        return confidence
    
    def get_lane_from_x(self, x_position):
        """Convert x position to lane index"""
        for i, lane_x in enumerate(self.lane_positions):
            if abs(x_position - lane_x) < LANE_WIDTH // 2:
                return i
        return 1  # Default to center lane

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

# A* Search Algorithm for Pathfinding
import heapq

class AStarNode:
    """
    Node representation for A* pathfinding algorithm.
    Each node represents a state: (lane, distance) position.
    """
    def __init__(self, lane, distance, g_cost, h_cost, parent=None):
        self.lane = lane  # Lane index (0, 1, 2)
        self.distance = distance  # Distance along the track
        self.g_cost = g_cost  # Cost from start to this node
        self.h_cost = h_cost  # Heuristic cost to goal
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent = parent  # Parent node for path reconstruction
    
    def __lt__(self, other):
        """Comparison for priority queue (lower f_cost = higher priority)"""
        return self.f_cost < other.f_cost
    
    def __eq__(self, other):
        """Equality check based on position"""
        return self.lane == other.lane and abs(self.distance - other.distance) < 50

class AStarPathfinder:
    """
    A* Pathfinding algorithm for vehicle navigation.
    Finds optimal path considering traffic, opponents, and power-ups.
    """
    
    def __init__(self, heuristic_type='manhattan'):
        """
        Initialize A* pathfinder.
        
        Args:
            heuristic_type: 'manhattan' or 'euclidean'
                - Manhattan: |Δlane| × LANE_WIDTH + |Δdistance| (better for structured movement)
                - Euclidean: √((Δx)² + (Δdistance)²) (better for direct pursuit)
        """
        self.heuristic_type = heuristic_type
        self.lane_positions = [
            ROAD_X + LANE_WIDTH // 2,
            ROAD_X + LANE_WIDTH + LANE_WIDTH // 2,
            ROAD_X + 2 * LANE_WIDTH + LANE_WIDTH // 2
        ]
    
    def manhattan_distance(self, current_lane, current_distance, goal_lane, goal_distance):
        """
        Manhattan distance heuristic (L1 norm).
        Calculates distance as sum of absolute differences.
        Better for grid-like movement (lane changes are discrete).
        
        Formula: |Δlane| × LANE_WIDTH + |Δdistance|
        """
        lane_diff = abs(current_lane - goal_lane) * LANE_WIDTH
        distance_diff = abs(goal_distance - current_distance)
        return lane_diff + distance_diff
    
    def euclidean_distance(self, current_lane, current_distance, goal_lane, goal_distance):
        """
        Euclidean distance heuristic (L2 norm).
        Calculates straight-line distance between positions.
        Better for direct pursuit and aggressive navigation.
        
        Formula: √((Δx)² + (Δdistance)²)
        """
        current_x = self.lane_positions[current_lane]
        goal_x = self.lane_positions[goal_lane]
        x_diff = goal_x - current_x
        distance_diff = goal_distance - current_distance
        return math.sqrt(x_diff**2 + distance_diff**2)
    
    def calculate_heuristic(self, current_lane, current_distance, goal_lane, goal_distance):
        """Calculate heuristic based on selected type"""
        if self.heuristic_type == 'manhattan':
            return self.manhattan_distance(current_lane, current_distance, goal_lane, goal_distance)
        else:  # euclidean
            return self.euclidean_distance(current_lane, current_distance, goal_lane, goal_distance)
    
    def get_lane_from_x(self, x_position):
        """Convert x position to lane index"""
        for i, lane_x in enumerate(self.lane_positions):
            if abs(x_position - lane_x) < LANE_WIDTH // 2:
                return i
        return 1  # Default to center lane
    
    def find_clearest_lane(self, current_distance, traffic_cars, look_ahead=600):
        """
        Find the lane with least traffic ahead.
        Returns (lane_index, traffic_count, min_distance_to_traffic)
        """
        lane_info = []
        
        for lane_idx in range(3):
            traffic_count = 0
            min_distance = float('inf')
            
            for car in traffic_cars:
                if car.lane == lane_idx:
                    distance_to_car = car.distance - current_distance
                    if 0 < distance_to_car < look_ahead:
                        traffic_count += 1
                        min_distance = min(min_distance, distance_to_car)
            
            lane_info.append((lane_idx, traffic_count, min_distance))
        
        # Sort by: fewer cars, then greater minimum distance
        lane_info.sort(key=lambda x: (x[1], -x[2]))
        return lane_info[0]  # Return clearest lane
    
    def is_position_safe(self, lane, distance, traffic_cars, opponent=None, ghost_mode=False, vehicle_speed=0):
        """
        IMPROVED: Check if a position is safe (no collisions).
        Enhanced with speed-based safety margins and side-collision detection.
        
        Args:
            lane: Lane index
            distance: Distance along track
            traffic_cars: List of traffic cars
            opponent: Opponent vehicle (to avoid)
            ghost_mode: If True, can pass through traffic
            vehicle_speed: Current vehicle speed (for dynamic safety margins)
        """
        # Ghost mode allows passing through traffic
        if ghost_mode:
            return True
        
        # Speed-based safety margin (faster = need more space) - MUCH MORE CONSERVATIVE!
        base_margin = 280  # INCREASED from 200
        speed_margin = base_margin + (vehicle_speed * 40)  # INCREASED from 30 - Larger margin!
        
        # Check traffic car collisions with DYNAMIC safety margin
        for car in traffic_cars:
            if car.lane == lane:
                distance_diff = abs(car.distance - distance)
                # Use speed-based margin for better avoidance
                if distance_diff < speed_margin:
                    return False
            
            # ENHANCED: Check adjacent lanes for side-by-side collision risk - WIDER ZONE!
            if abs(car.lane - lane) == 1:  # Adjacent lane
                distance_diff = abs(car.distance - distance)
                # Very close side-by-side is dangerous
                if distance_diff < 80:  # INCREASED from 60 - Side collision zone
                    return False
        
        # Check opponent collision (police should avoid being ahead of thief before catching)
        if opponent:
            opponent_lane = self.get_lane_from_x(opponent.x)
            if lane == opponent_lane:
                distance_diff = abs(opponent.distance - distance)
                if distance_diff < 180:  # Safety margin for opponent
                    return False
        
        return True
    
    def calculate_path_cost(self, current_node, next_lane, next_distance, traffic_cars, 
                           opponent=None, ghost_mode=False, is_police=False, vehicle_speed=0):
        """
        IMPROVED: Calculate cost of moving to next position.
        Enhanced with speed-aware penalties and multi-obstacle detection.
        
        Cost components:
        - Distance traveled
        - Lane change penalty (lane changes are risky)
        - Traffic proximity penalty (speed-aware and multi-obstacle)
        - Opponent interaction (police chases, thief evades)
        """
        # Base cost: distance traveled
        distance_cost = abs(next_distance - current_node.distance)
        
        # Lane change penalty (changing lanes is costly, especially at high speed)
        lane_change_cost = 0
        if next_lane != current_node.lane:
            # Higher penalty at high speed (more dangerous)
            lane_change_cost = 30 + (vehicle_speed * 5)
        
        # IMPROVED: Speed-aware traffic proximity penalty with multi-obstacle detection
        traffic_penalty = 0
        obstacles_nearby = 0
        
        if not ghost_mode:
            # Speed-based danger zones (faster = larger zones) - MUCH MORE CONSERVATIVE!
            critical_zone = 150 + (vehicle_speed * 25)  # INCREASED from 100 + speed*15
            close_zone = 280 + (vehicle_speed * 30)  # INCREASED from 200 + speed*20
            medium_zone = 420 + (vehicle_speed * 35)  # INCREASED from 300 + speed*25
            far_zone = 560 + (vehicle_speed * 40)  # INCREASED from 400 + speed*30
            
            for car in traffic_cars:
                if car.lane == next_lane:
                    distance_diff = abs(car.distance - next_distance)
                    
                    # CRITICAL ZONE: Very close to traffic - MASSIVE PENALTIES!
                    if distance_diff < critical_zone:
                        traffic_penalty += 900  # INCREASED from 600 - HUGE penalty!
                        obstacles_nearby += 1
                    elif distance_diff < close_zone:
                        traffic_penalty += 550  # INCREASED from 350 - Very strong penalty
                        obstacles_nearby += 1
                    elif distance_diff < medium_zone:
                        traffic_penalty += 280  # INCREASED from 180 - Strong penalty
                    elif distance_diff < far_zone:
                        traffic_penalty += 100  # INCREASED from 60 - Medium penalty
                
                # ENHANCED: Penalty for adjacent lane traffic (side-collision risk) - STRONGER!
                if abs(car.lane - next_lane) == 1:
                    distance_diff = abs(car.distance - next_distance)
                    # Side-by-side is very dangerous
                    if distance_diff < 70:  # INCREASED zone from 50
                        traffic_penalty += 600  # INCREASED from 400 - Huge penalty!
                    elif distance_diff < 130:  # INCREASED zone from 100
                        traffic_penalty += 180  # INCREASED from 100 - Strong penalty
            
            # ENHANCED: Multi-obstacle penalty (traffic jam detection) - STRONGER!
            if obstacles_nearby >= 2:
                traffic_penalty += 350  # INCREASED from 200 - Major penalty!
            
            # BONUS: Reward clear lanes (no traffic within extended range)
            clear_distance = 500 + (vehicle_speed * 40)  # Dynamic clear zone
            lane_clear = True
            for car in traffic_cars:
                if car.lane == next_lane:
                    distance_diff = abs(car.distance - next_distance)
                    if distance_diff < clear_distance:
                        lane_clear = False
                        break
            
            if lane_clear:
                traffic_penalty -= 30  # Increased reward for choosing clear lane
        
        # Opponent interaction
        opponent_cost = 0
        if opponent:
            opponent_lane = self.get_lane_from_x(opponent.x)
            distance_to_opponent = next_distance - opponent.distance
            
            if is_police:
                # Police: reward getting closer to thief, but never overtake before catching
                if distance_to_opponent > 0:  # Police ahead of thief
                    # STRONG penalty for being ahead - police should chase, not lead!
                    opponent_cost += 500 + distance_to_opponent * 2
                else:  # Police behind thief (good)
                    # Small reward for closing distance
                    opponent_cost -= abs(distance_to_opponent) * 0.1
            else:
                # Thief: reward staying ahead and away from police
                if distance_to_opponent > 0:  # Thief ahead (good)
                    opponent_cost -= 20
                else:  # Thief behind police (bad)
                    opponent_cost += abs(distance_to_opponent) * 0.2
        
        total_cost = distance_cost + lane_change_cost + traffic_penalty + opponent_cost
        return max(1, total_cost)  # Ensure positive cost
    
    def find_path(self, start_lane, start_distance, goal_lane, goal_distance, 
                  traffic_cars, opponent=None, ghost_mode=False, is_police=False, vehicle_speed=0):
        """
        IMPROVED: A* pathfinding algorithm to find optimal path.
        Enhanced with speed-aware pathfinding for better obstacle avoidance.
        
        Args:
            start_lane: Starting lane index
            start_distance: Starting distance
            goal_lane: Goal lane index
            goal_distance: Goal distance
            traffic_cars: List of traffic cars to avoid
            opponent: Opponent vehicle
            ghost_mode: If True, can pass through traffic
            is_police: If True, vehicle is police (different behavior)
            vehicle_speed: Current vehicle speed (for dynamic safety margins)
        
        Returns:
            List of (lane, distance) waypoints representing the path
        """
        # Initialize start node
        start_h = self.calculate_heuristic(start_lane, start_distance, goal_lane, goal_distance)
        start_node = AStarNode(start_lane, start_distance, 0, start_h)
        
        # Priority queue (open set) and closed set
        open_set = []
        heapq.heappush(open_set, start_node)
        closed_set = set()
        
        # Track best g_cost for each position
        best_g_cost = {(start_lane, start_distance): 0}
        
        # Performance limit: max iterations
        max_iterations = 200
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # Get node with lowest f_cost
            current_node = heapq.heappop(open_set)
            
            # Check if reached goal
            if abs(current_node.distance - goal_distance) < 100 and current_node.lane == goal_lane:
                # Reconstruct path
                path = []
                node = current_node
                while node:
                    path.append((node.lane, node.distance))
                    node = node.parent
                return list(reversed(path))
            
            # Add to closed set
            state = (current_node.lane, int(current_node.distance / 50))  # Discretize for closed set
            if state in closed_set:
                continue
            closed_set.add(state)
            
            # Generate neighbors (possible next positions)
            neighbors = self._generate_neighbors(current_node, goal_distance)
            
            for next_lane, next_distance in neighbors:
                # Skip if not safe (with speed-based margins)
                if not self.is_position_safe(next_lane, next_distance, traffic_cars, opponent, ghost_mode, vehicle_speed):
                    continue
                
                # Calculate costs (with speed-aware penalties)
                move_cost = self.calculate_path_cost(
                    current_node, next_lane, next_distance, traffic_cars, 
                    opponent, ghost_mode, is_police, vehicle_speed
                )
                new_g_cost = current_node.g_cost + move_cost
                
                # Check if this path is better
                state_key = (next_lane, int(next_distance / 50))
                if state_key in best_g_cost and new_g_cost >= best_g_cost[state_key]:
                    continue
                
                best_g_cost[state_key] = new_g_cost
                
                # Calculate heuristic
                h_cost = self.calculate_heuristic(next_lane, next_distance, goal_lane, goal_distance)
                
                # Create new node
                new_node = AStarNode(next_lane, next_distance, new_g_cost, h_cost, current_node)
                heapq.heappush(open_set, new_node)
        
        # No path found - return simple fallback path
        return [(start_lane, start_distance), (goal_lane, goal_distance)]
    
    def _generate_neighbors(self, current_node, goal_distance):
        """
        Generate valid neighbor positions for A* expansion.
        
        Neighbors include:
        - Moving forward in same lane
        - Changing to adjacent lanes
        - Adaptive step size based on distance to goal
        """
        neighbors = []
        current_lane = current_node.lane
        current_distance = current_node.distance
        
        # Adaptive step size: larger steps when far from goal, smaller when close
        distance_to_goal = abs(goal_distance - current_distance)
        if distance_to_goal > 1000:
            step_size = 100  # Large steps when far
        elif distance_to_goal > 300:
            step_size = 50   # Medium steps
        else:
            step_size = 20   # Small steps when close
        
        # Move forward in current lane
        next_distance = current_distance + step_size
        if next_distance <= goal_distance + 100:  # Don't overshoot too much
            neighbors.append((current_lane, next_distance))
        
        # Lane changes (to adjacent lanes only)
        for lane_offset in [-1, 1]:
            next_lane = current_lane + lane_offset
            if 0 <= next_lane <= 2:  # Valid lane
                # Lane change with forward movement
                neighbors.append((next_lane, next_distance))
        
        return neighbors

# Minimax Algorithm with Alpha-Beta Pruning for Adversarial Decision Making
class GameState:
    """
    Represents a snapshot of the game state for Minimax evaluation.
    Lightweight structure for efficient tree search.
    """
    def __init__(self, police_lane, police_distance, thief_lane, thief_distance,
                 police_speed, thief_speed, traffic_snapshot, powerups_snapshot):
        self.police_lane = police_lane
        self.police_distance = police_distance
        self.thief_lane = thief_lane
        self.thief_distance = thief_distance
        self.police_speed = police_speed
        self.thief_speed = thief_speed
        self.traffic = traffic_snapshot  # List of (lane, distance) for nearby traffic
        self.powerups = powerups_snapshot  # List of (lane, distance, type, for_police)
        
    def copy(self):
        """Create a deep copy for simulation"""
        return GameState(
            self.police_lane, self.police_distance,
            self.thief_lane, self.thief_distance,
            self.police_speed, self.thief_speed,
            self.traffic.copy(), self.powerups.copy()
        )

class MinimaxAction:
    """Represents a possible action in the game tree"""
    def __init__(self, lane, speed_change, collect_powerup=False):
        self.lane = lane  # Target lane (0, 1, 2)
        self.speed_change = speed_change  # 'accelerate', 'maintain', 'brake'
        self.collect_powerup = collect_powerup  # Whether to attempt powerup collection
    
    def __repr__(self):
        return f"MinimaxAction(lane={self.lane}, speed={self.speed_change}, powerup={self.collect_powerup})"

class MinimaxDecisionMaker:
    """
    Advanced adversarial AI using Minimax with Alpha-Beta pruning.
    Models opponent behavior to make optimal strategic decisions.
    """
    
    def __init__(self):
        self.lane_positions = [
            ROAD_X + LANE_WIDTH // 2,
            ROAD_X + LANE_WIDTH + LANE_WIDTH // 2,
            ROAD_X + 2 * LANE_WIDTH + LANE_WIDTH // 2
        ]
        self.max_depth = 3  # Search depth (3 ply = 3 moves ahead)
        self.nodes_evaluated = 0  # For performance tracking
    
    def get_best_move(self, current_state, is_police, max_time_ms=15):
        """
        Main entry point: Returns best action using Minimax with Alpha-Beta pruning.
        
        Args:
            current_state: Current GameState
            is_police: True if police's turn, False if thief's turn
            max_time_ms: Maximum computation time (for real-time constraint)
        
        Returns:
            MinimaxAction: Best move to make
        """
        self.nodes_evaluated = 0
        self.start_time = pygame.time.get_ticks()
        self.max_time = max_time_ms
        
        best_action = None
        best_value = float('-inf') if is_police else float('inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # Generate all possible actions
        possible_actions = self._generate_actions(current_state, is_police)
        
        # Evaluate each action
        for action in possible_actions:
            # Simulate action
            new_state = self._simulate_action(current_state, action, is_police)
            
            # Evaluate with Minimax
            if is_police:
                # Police maximizes (wants to catch thief)
                value = self._minimax_alpha_beta(new_state, self.max_depth - 1, 
                                                 alpha, beta, False)
                if value > best_value:
                    best_value = value
                    best_action = action
                alpha = max(alpha, value)
            else:
                # Thief minimizes (wants to escape)
                value = self._minimax_alpha_beta(new_state, self.max_depth - 1,
                                                 alpha, beta, True)
                if value < best_value:
                    best_value = value
                    best_action = action
                beta = min(beta, value)
        
        return best_action if best_action else possible_actions[0]
    
    def _minimax_alpha_beta(self, state, depth, alpha, beta, maximizing_player):
        """
        Minimax algorithm with Alpha-Beta pruning.
        
        Args:
            state: Current GameState
            depth: Remaining search depth
            alpha: Best value for maximizer
            beta: Best value for minimizer
            maximizing_player: True if police's turn (maximizer)
        
        Returns:
            int: Evaluated score for this state
        """
        self.nodes_evaluated += 1
        
        # Terminal conditions
        if depth == 0 or self._is_terminal(state):
            return self._evaluate_state(state)
        
        # Time limit check (for real-time performance)
        if pygame.time.get_ticks() - self.start_time > self.max_time:
            return self._evaluate_state(state)
        
        if maximizing_player:
            # Police's turn (maximize score)
            max_eval = float('-inf')
            possible_actions = self._generate_actions(state, is_police=True)
            
            for action in possible_actions:
                new_state = self._simulate_action(state, action, is_police=True)
                eval_score = self._minimax_alpha_beta(new_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Beta cutoff (prune remaining branches)
            
            return max_eval
        
        else:
            # Thief's turn (minimize score)
            min_eval = float('inf')
            possible_actions = self._generate_actions(state, is_police=False)
            
            for action in possible_actions:
                new_state = self._simulate_action(state, action, is_police=False)
                eval_score = self._minimax_alpha_beta(new_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha cutoff (prune remaining branches)
            
            return min_eval
    
    def _evaluate_state(self, state):
        """
        Evaluation function: Scores game state from police perspective.
        Higher score = better for police (closer to catching thief)
        Lower score = better for thief (more likely to escape)
        
        IMPROVED: Better traffic collision avoidance
        
        Returns:
            int: State evaluation score
        """
        score = 0
        
        # PRIMARY FACTOR: Distance between police and thief
        distance_diff = state.thief_distance - state.police_distance
        
        if distance_diff <= 0:
            # Police caught thief or ahead - HUGE bonus
            return 10000
        elif distance_diff < 50:
            # Very close - imminent catch
            score += 5000 - (distance_diff * 80)
        elif distance_diff < 150:
            # Close pursuit
            score += 3000 - (distance_diff * 15)
        elif distance_diff < 300:
            # Medium range
            score += 1500 - (distance_diff * 4)
        else:
            # Far away
            score += 500 - (distance_diff * 1)
        
        # SECONDARY FACTOR: Lateral positioning (same lane = easier catch)
        lane_diff = abs(state.police_lane - state.thief_lane)
        score -= lane_diff * 150  # Penalty for different lanes
        
        # TERTIARY FACTOR: Speed advantage
        speed_diff = state.police_speed - state.thief_speed
        score += speed_diff * 50  # Bonus if police faster
        
        # TRAFFIC FACTOR: IMPROVED collision avoidance
        # Check immediate traffic danger for police (critical!)
        police_immediate_traffic = 0
        police_near_traffic = 0
        for traffic_lane, traffic_dist in state.traffic:
            if traffic_lane == state.police_lane:
                dist_to_traffic = traffic_dist - state.police_distance
                if 0 < dist_to_traffic < 150:
                    police_immediate_traffic += 1  # CRITICAL: collision imminent
                elif 0 < dist_to_traffic < 300:
                    police_near_traffic += 1  # Close traffic
        
        # MASSIVE penalties for traffic collisions
        score -= police_immediate_traffic * 800  # Must avoid collision!
        score -= police_near_traffic * 200  # Avoid close traffic
        
        # Thief trapped by traffic is good for police
        thief_traffic_ahead = 0
        for traffic_lane, traffic_dist in state.traffic:
            if traffic_lane == state.thief_lane:
                dist_to_traffic = traffic_dist - state.thief_distance
                if 0 < dist_to_traffic < 300:
                    thief_traffic_ahead += 1
        
        score += thief_traffic_ahead * 80  # Bonus for blocking thief
        
        # POWER-UP FACTOR: Strategic power-up positioning
        for powerup in state.powerups:
            pw_lane, pw_dist, pw_type, for_police = powerup
            
            if for_police:
                # Police power-up evaluation
                dist_to_police = abs(pw_dist - state.police_distance)
                if dist_to_police < 200:
                    # Police can get useful power-up
                    if pw_type in ['turbo', 'emp']:
                        score += 200 - dist_to_police  # High value powers
                    else:
                        score += 100 - dist_to_police
            else:
                # Thief power-up evaluation (bad for police)
                dist_to_thief = abs(pw_dist - state.thief_distance)
                if dist_to_thief < 200:
                    if pw_type in ['freeze', 'boost', 'ghost']:
                        score -= 250 - dist_to_thief  # Dangerous for police
                    else:
                        score -= 120 - dist_to_thief
        
        # FINISH LINE FACTOR: Thief near finish is bad
        distance_to_finish = FINISH_LINE_DISTANCE - state.thief_distance
        if distance_to_finish < 5000:
            # Endgame urgency
            score -= (5000 - distance_to_finish) * 2
        
        # LANE CLEARANCE BONUS: Reward being in clear lanes
        police_lane_clear = True
        for traffic_lane, traffic_dist in state.traffic:
            if traffic_lane == state.police_lane:
                dist_to_traffic = abs(traffic_dist - state.police_distance)
                if dist_to_traffic < 400:
                    police_lane_clear = False
                    break
        
        if police_lane_clear:
            score += 150  # Bonus for clear lane
        
        return score
    
    def _generate_actions(self, state, is_police):
        """
        Generate all possible actions for current player.
        IMPROVED: Better traffic-aware action filtering.
        
        Returns:
            List[MinimaxAction]: All valid actions
        """
        actions = []
        current_lane = state.police_lane if is_police else state.thief_lane
        current_distance = state.police_distance if is_police else state.thief_distance
        
        # Lane options: stay, move left, move right (ALL lanes always considered)
        lane_options = [current_lane]
        if current_lane > 0:
            lane_options.append(current_lane - 1)
        if current_lane < 2:
            lane_options.append(current_lane + 1)
        
        # Speed options
        speed_options = ['accelerate', 'maintain', 'brake']
        
        # Check traffic in current lane
        traffic_in_current = self._count_traffic_ahead(state, current_lane, current_distance, 250)
        
        # Generate combinations
        for lane in lane_options:
            traffic_in_lane = self._count_traffic_ahead(state, lane, current_distance, 250)
            
            for speed in speed_options:
                # IMPROVED LOGIC: Allow more combinations
                # Only skip if staying in heavily blocked lane while accelerating
                if lane == current_lane and traffic_in_current > 2 and speed == 'accelerate':
                    continue  # Don't accelerate into heavy traffic
                
                # Encourage lane changes when traffic is ahead
                if lane != current_lane and traffic_in_lane < traffic_in_current:
                    # This lane is clearer - prioritize it
                    actions.insert(0, MinimaxAction(lane, speed, collect_powerup=False))
                else:
                    actions.append(MinimaxAction(lane, speed, collect_powerup=False))
                
                # Consider power-up collection if nearby
                if self._powerup_nearby(state, lane, is_police):
                    actions.append(MinimaxAction(lane, speed, collect_powerup=True))
        
        return actions
    
    def _simulate_action(self, state, action, is_police):
        """
        Simulate action and return resulting state.
        Fast simulation without full physics.
        """
        new_state = state.copy()
        
        if is_police:
            # Update police state
            new_state.police_lane = action.lane
            
            # Speed changes
            if action.speed_change == 'accelerate':
                new_state.police_speed = min(new_state.police_speed + 0.4, 8)
            elif action.speed_change == 'brake':
                new_state.police_speed = max(new_state.police_speed - 0.6, 3)
            # 'maintain' keeps speed
            
            # Move forward
            new_state.police_distance += new_state.police_speed * 20  # Approximate
            
        else:
            # Update thief state
            new_state.thief_lane = action.lane
            
            # Speed changes
            if action.speed_change == 'accelerate':
                new_state.thief_speed = min(new_state.thief_speed + 0.4, 8)
            elif action.speed_change == 'brake':
                new_state.thief_speed = max(new_state.thief_speed - 0.6, 3)
            
            # Move forward
            new_state.thief_distance += new_state.thief_speed * 20
        
        return new_state
    
    def _is_terminal(self, state):
        """Check if state is terminal (game over)"""
        # Police caught thief
        if state.police_distance >= state.thief_distance - 30:
            return True
        
        # Thief reached finish
        if state.thief_distance >= FINISH_LINE_DISTANCE:
            return True
        
        return False
    
    def _count_traffic_ahead(self, state, lane, distance, look_ahead):
        """Count traffic cars ahead in specific lane"""
        count = 0
        for traffic_lane, traffic_dist in state.traffic:
            if traffic_lane == lane:
                if 0 < traffic_dist - distance < look_ahead:
                    count += 1
        return count
    
    def _count_available_lanes(self, state, current_lane, distance):
        """Count how many lanes are clear for movement"""
        available = 0
        for lane in range(3):
            traffic_in_lane = self._count_traffic_ahead(state, lane, distance, 200)
            if traffic_in_lane == 0:
                available += 1
        return available
    
    def _powerup_nearby(self, state, lane, is_police):
        """Check if there's a relevant power-up nearby"""
        for pw_lane, pw_dist, pw_type, for_police in state.powerups:
            if for_police == is_police and pw_lane == lane:
                # Power-up is for this player and in target lane
                current_dist = state.police_distance if is_police else state.thief_distance
                if 0 < pw_dist - current_dist < 250:
                    return True
        return False
    
    def get_lane_from_x(self, x_position):
        """Convert x position to lane index"""
        for i, lane_x in enumerate(self.lane_positions):
            if abs(x_position - lane_x) < LANE_WIDTH // 2:
                return i
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
            'freeze': {'color': (100, 200, 255), 'icon': '🌀', 'name': 'Stagger Slow'},
            'boost': {'color': (255, 200, 0), 'icon': '⚡', 'name': 'Speed Boost'},
            'shield': {'color': (150, 255, 150), 'icon': '🛡️', 'name': 'Shield'},
            'ghost': {'color': (200, 150, 255), 'icon': '👻', 'name': 'Ghost (1 Forgive)'},
            # Police-exclusive power-ups (red theme)
            'spike': {'color': (255, 50, 50), 'icon': '🔺', 'name': 'Spike Strip'},
            'emp': {'color': (255, 100, 255), 'icon': '💫', 'name': 'Stagger Slow'},
            'turbo': {'color': (255, 150, 0), 'icon': '🔥', 'name': 'Turbo Boost'},
            'roadblock': {'color': (200, 50, 50), 'icon': '🚧', 'name': 'Roadblock'},
            'magnet': {'color': (150, 150, 255), 'icon': '🧲', 'name': 'Magnetic Pull'}
        }
        
        # Power-up priority values (higher = more valuable)
        # Balanced to favor defensive & positioning powers over game-breaking ones
        self.priority = {
            'boost': 1.2,      # Moderate priority - speed advantage
            'shield': 1.4,     # High priority - crash protection
            'ghost': 1.5,      # Highest priority - mistake forgiveness
            'freeze': 1.0,     # Base priority - temporary hindrance
            'turbo': 1.2,      # Moderate priority - speed advantage
            'spike': 1.1,      # Low-moderate priority - slow effect
            'emp': 1.3,        # High priority - speed + steering hindrance
            'magnet': 1.4,     # High priority - positioning control
            'roadblock': 1.0   # Base priority - situational use
        }
    
    def get_priority_value(self):
        """Get the priority value for this power-up type"""
        return self.priority.get(self.power_type, 1.0)
    
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
            
            # LARGER SIZE for better visibility
            size = 55 if self.for_police else 50
            
            # Pulsing glow effect (more intense for police powerups)
            pulse_speed = 300 if self.for_police else 400
            pulse = abs(math.sin(pygame.time.get_ticks() / pulse_speed)) * 25 + 20
            
            # Draw multiple glow layers with stronger colors
            # SWAPPED: Police (blue car) gets blue glow, Thief (red car) gets red glow
            for r in range(int(pulse), 0, -4):
                alpha = int(120 * (r / pulse))
                glow_surf = pygame.Surface((size + r*2, size + r*2), pygame.SRCALPHA)
                glow_color = (50, 150, 255) if self.for_police else (255, 50, 50)  # SWAPPED
                pygame.draw.circle(glow_surf, (*glow_color, alpha), 
                                 (size//2 + r, size//2 + r), size//2 + r)
                screen.blit(glow_surf, (int(lane_x - size//2 - r), int(final_y - size//2 - r)))
            
            # DISTINCT SHAPES: Hexagon for POLICE (blue theme), Circle for THIEF (red theme)
            if self.for_police:
                # Draw LARGER hexagon for police powers with BLUE border (matches police car)
                points = []
                sides = 6
                for i in range(sides):
                    angle = (self.rotation + i * (360 / sides)) * math.pi / 180
                    x = lane_x + math.cos(angle) * (size//2)
                    y = final_y + math.sin(angle) * (size//2)
                    points.append((int(x), int(y)))
                
                # Dark blue fill (was dark red)
                pygame.draw.polygon(screen, (0, 80, 180), points)
                # Bright blue border (THICK) (was bright red)
                pygame.draw.polygon(screen, (50, 150, 255), points, 5)
                # Inner bright fill
                inner_points = []
                for i in range(sides):
                    angle = (self.rotation + i * (360 / sides)) * math.pi / 180
                    x = lane_x + math.cos(angle) * (size//2 - 8)
                    y = final_y + math.sin(angle) * (size//2 - 8)
                    inner_points.append((int(x), int(y)))
                pygame.draw.polygon(screen, props['color'], inner_points)
                
                # Add "POLICE" label below
                font_label = pygame.font.Font(None, 22)
                label_text = font_label.render("POLICE", True, (255, 255, 255))
                label_bg = pygame.Surface((label_text.get_width() + 8, label_text.get_height() + 4), pygame.SRCALPHA)
                pygame.draw.rect(label_bg, (0, 100, 200, 220), label_bg.get_rect(), border_radius=3)  # Blue label
                screen.blit(label_bg, (int(lane_x - label_text.get_width()//2 - 4), int(final_y + size//2 + 8)))
                screen.blit(label_text, (int(lane_x - label_text.get_width()//2), int(final_y + size//2 + 10)))
            else:
                # Draw CIRCLE for thief powers with RED border (matches thief car)
                # Dark red fill (was dark blue)
                pygame.draw.circle(screen, (180, 0, 0), (int(lane_x), int(final_y)), size//2)
                # Bright red border (THICK) (was bright blue)
                pygame.draw.circle(screen, (255, 0, 0), (int(lane_x), int(final_y)), size//2, 5)
                # Inner bright fill
                pygame.draw.circle(screen, props['color'], (int(lane_x), int(final_y)), size//2 - 8)
                
                # Add "THIEF" label below
                font_label = pygame.font.Font(None, 22)
                label_text = font_label.render("THIEF", True, (255, 255, 255))
                label_bg = pygame.Surface((label_text.get_width() + 8, label_text.get_height() + 4), pygame.SRCALPHA)
                pygame.draw.rect(label_bg, (200, 0, 0, 220), label_bg.get_rect(), border_radius=3)  # Red label
                screen.blit(label_bg, (int(lane_x - label_text.get_width()//2 - 4), int(final_y + size//2 + 8)))
                screen.blit(label_text, (int(lane_x - label_text.get_width()//2), int(final_y + size//2 + 10)))
            
            # Draw icon (LARGER)
            font_icon = pygame.font.Font(None, 42)
            icon_text = font_icon.render(props['icon'], True, WHITE)
            icon_rect = icon_text.get_rect(center=(int(lane_x), int(final_y)))
            screen.blit(icon_text, icon_rect)
            
            # Rotating sparkles for extra visibility
            # SWAPPED: Police (blue car) gets blue sparkles, Thief (red car) gets red sparkles
            sparkle_count = 4
            rotation_speed = 3 if self.for_police else 2
            for i in range(sparkle_count):
                angle = (self.rotation * rotation_speed + i * (360 / sparkle_count)) * math.pi / 180
                sparkle_dist = size//2 + 15
                x = lane_x + math.cos(angle) * sparkle_dist
                y = final_y + math.sin(angle) * sparkle_dist
                sparkle_color = (100, 200, 255) if self.for_police else (255, 100, 100)  # SWAPPED
                pygame.draw.circle(screen, sparkle_color, (int(x), int(y)), 4)
                pygame.draw.circle(screen, WHITE, (int(x), int(y)), 2)
    
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
        
        # SPEED LIMIT: 200 km/h maximum for both characters
        # Conversion: 1 speed unit = 25 km/h
        # Max speed units = 200 / 25 = 8.0 units
        self.ABSOLUTE_MAX_SPEED = 8.0  # 200 km/h hard limit
        
        # INDEPENDENT SPEED SETTINGS based on role
        # BALANCED: Both have same top speed for fair competition
        if is_police:
            # Police: Pursuit characteristics
            self.max_speed = 8.0  # 200 km/h - SAME as thief
            self.base_max_speed = 8.0
            self.acceleration_rate = 0.21  # Slightly faster recovery (5% advantage)
            self.brake_rate = 0.35  # Better braking control
        else:
            # Thief: Evasion characteristics  
            self.max_speed = 8.0  # 200 km/h - SAME as police
            self.base_max_speed = 8.0
            self.acceleration_rate = 0.20  # Standard acceleration
            self.brake_rate = 0.32  # Better evasion braking (better than before)
        
        self.is_player = is_player
        self.is_police = is_police
        self.distance = 0
        self.wheel_rotation = 0
        
        # Track previous position for skid detection
        self.prev_x = x
        self.skid_cooldown = 0
        
        # Power-up effects
        self.active_powerups = {}
        self.shield_active = False
        self.ghost_mode = False
        self.crashed = False
        self.crash_timer = 0
        self.crash_spin = 0
    
    def check_sharp_steering(self):
        """Detect sharp steering and play skid sound"""
        if self.skid_cooldown > 0:
            self.skid_cooldown -= 1
            return
        
        # Calculate steering change
        steering_change = abs(self.x - self.prev_x)
        
        # If steering sharply at high speed, play skid sound
        if steering_change > 8 and self.speed > 5.0:
            audio_manager.play_skid()
            self.skid_cooldown = 40  # Prevent rapid repeats
        
        self.prev_x = self.x
    
    def get_speed_kmh(self):
        """Convert speed units to km/h for display"""
        return int(self.speed * 25)  # 1 unit = 25 km/h
    
    def enforce_speed_limit(self):
        """Enforce the absolute 200 km/h speed limit"""
        if self.speed > self.ABSOLUTE_MAX_SPEED:
            self.speed = self.ABSOLUTE_MAX_SPEED
        # Also enforce max_speed (which can be modified by power-ups)
        if self.speed > self.max_speed:
            self.speed = self.max_speed
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
    
    def is_lane_safe_for_powerup(self, target_lane, traffic_cars, lookahead=250):
        """
        Check if it's safe to switch to target lane for power-up collection.
        
        Args:
            target_lane: The lane index (0, 1, or 2) to check
            traffic_cars: List of traffic car objects
            lookahead: Distance ahead to check for obstacles (default 250)
            
        Returns:
            bool: True if lane is safe, False if traffic detected
        """
        for car in traffic_cars:
            if car.lane == target_lane:
                # Calculate relative distance to traffic car
                relative_distance = car.distance - self.distance
                
                # Check if traffic is in our lookahead range
                if 0 < relative_distance < lookahead:
                    return False  # Traffic detected - unsafe
        
        return True  # No traffic detected - safe to switch
    
    def choose_best_power(self, powers, traffic_cars, lane_positions):
        """
        Intelligently choose the best power-up to collect based on:
        - Power priority value
        - Distance to power-up
        - Lane safety
        
        Args:
            powers: List of available power-ups
            traffic_cars: List of traffic cars for safety check
            lane_positions: Dictionary mapping lane index to X position
            
        Returns:
            PowerUp object or None if no good option exists
        """
        best_power = None
        best_score = 0
        
        for p in powers:
            # Skip if already collected
            if p.collected:
                continue
            
            # Skip if wrong type (thief can't collect police powers and vice versa)
            if self.is_police and not p.for_police:
                continue
            if not self.is_police and p.for_police:
                continue
            
            # Calculate distance to power-up
            dist = abs(p.distance - self.distance)
            
            # Ignore powers that are too far away
            if dist > 400:
                continue
            
            # Get power-up priority value (1.0 to 1.5)
            value = p.get_priority_value()
            
            # Closeness factor (closer = better)
            closeness = 1.0 / (dist + 1)
            
            # Lane safety check
            lane_risk = 0 if self.is_lane_safe_for_powerup(p.lane, traffic_cars, lookahead=250) else 1.2
            
            # Calculate final score
            score = (value * closeness) - lane_risk
            
            # Track best power-up
            if score > best_score:
                best_score = score
                best_power = p
        
        return best_power
    
    def priority_decision_hierarchy(self, traffic_cars, powerups, opponent, ghost_mode,
                                   fuzzy_controller, minimax_solver, astar_pathfinder):
        """
        ======================================================================
        PRIORITY DECISION HIERARCHY - ENHANCED WITH POWER COLLECTION
        ======================================================================
        Intelligent blending of multiple AI algorithms with clear priority order.
        
        PRIORITY LEVELS (CRITICAL ORDER):
        1. SAFETY (Always Active) - Predictive collision avoidance - HIGHEST PRIORITY
        2. POWER COLLECTION (When Safe) - Micro-steering toward valuable powers
        3. FUZZY (Tactical) - Close-range smooth reactions
        4. MINIMAX (Strategic) - Medium-range adversarial planning
        5. A* (Pathfinding) - Long-range optimal routing
        
        PRIORITY ORDER FLOW:
        - IF collision danger: → Avoid collision (safety override)
        - ELIF safe power exists: → Micro-steer toward power (smooth collection)
        - ELSE: → Continue chase/escape behavior (algorithm blending)
        
        Collision avoidance remains #1 priority forever.
        Power collection only happens when safe.
        ======================================================================
        """
        if self.crashed:
            return
        
        # ===== PRIORITY 1: SAFETY LAYER (ALWAYS RUNS FIRST) =====
        safety_check = self.predictive_safety_check(traffic_cars, fuzzy_controller)
        
        # If CRITICAL danger, safety takes FULL CONTROL (no blending)
        if safety_check['recommended_action']['urgency'] == 'critical':
            # Emergency override - 100% safety control
            self._execute_safety_override(safety_check, fuzzy_controller)
            return
        
        # ===== PRIORITY 2: SAFE POWER COLLECTION (MICRO-STEERING) =====
        # Only attempt power collection if NOT in high danger
        urgency = safety_check['recommended_action']['urgency']
        target_power = None
        
        if urgency not in ['high', 'critical']:
            # Safe enough to consider power collection
            lane_positions = fuzzy_controller.lane_positions
            target_power = self.choose_best_power(powerups, traffic_cars, lane_positions)
            
            if target_power is not None:
                # Apply MICRO-STEERING toward power-up (smooth movement)
                target_x = lane_positions[target_power.lane]
                steering_strength = 0.07  # Gentle steering (7% per frame)
                
                # Calculate steering amount
                steering_delta = (target_x - self.x) * steering_strength
                
                # Apply smooth steering with road boundaries
                self.x += steering_delta
                self.x = max(ROAD_X + 35, min(ROAD_X + ROAD_WIDTH - 35, self.x))
        
        # ===== PRIORITY 3: GATHER RECOMMENDATIONS FROM ALL SYSTEMS =====
        current_lane = fuzzy_controller.get_lane_from_x(self.x)
        distance_to_opponent = abs(opponent.distance - self.distance) if opponent else float('inf')
        
        # Get recommendations (but don't execute yet)
        recommendations = {
            'safety': safety_check['recommended_action'],
            'fuzzy': None,
            'minimax': None,
            'astar': None
        }
        
        # ===== PRIORITY 4: DETERMINE WEIGHTS BASED ON SITUATION =====
        # Weights determine how much each algorithm influences the final decision
        weights = {
            'safety': 0.0,
            'fuzzy': 0.0,
            'minimax': 0.0,
            'astar': 0.0
        }
        
        # Calculate situation urgency
        urgency = safety_check['recommended_action']['urgency']
        
        # WEIGHT CALCULATION: Adaptive based on danger level and opponent distance
        if urgency in ['high', 'moderate']:
            # HIGH DANGER: Safety + Fuzzy dominate (smooth evasion)
            weights['safety'] = 0.60  # Safety has strong influence
            weights['fuzzy'] = 0.30   # Fuzzy for smooth execution
            weights['minimax'] = 0.05 # Minimax still aware of opponent
            weights['astar'] = 0.05   # A* for path context
        
        elif distance_to_opponent < 300:
            # CLOSE OPPONENT: Safety + Fuzzy + Minimax blend
            weights['safety'] = 0.25  # Safety monitors
            weights['fuzzy'] = 0.45   # Fuzzy for reactions
            weights['minimax'] = 0.25 # Minimax for tactics
            weights['astar'] = 0.05   # A* minimal
        
        elif distance_to_opponent < 800:
            # MEDIUM DISTANCE: Balanced blend with Minimax priority
            weights['safety'] = 0.15  # Safety awareness
            weights['fuzzy'] = 0.25   # Fuzzy for smoothness
            weights['minimax'] = 0.45 # Minimax for strategy
            weights['astar'] = 0.15   # A* for planning
        
        else:
            # FAR/SAFE: A* dominates with support from others
            weights['safety'] = 0.10  # Safety background check
            weights['fuzzy'] = 0.15   # Fuzzy for smoothness
            weights['minimax'] = 0.20 # Minimax for opponent awareness
            weights['astar'] = 0.55   # A* for optimal routing
        
        # ===== EXECUTE BLENDED DECISION =====
        # Use the algorithm with highest weight as primary, others as modifiers
        primary_system = max(weights, key=weights.get)
        
        # Execute primary system with awareness of others
        # Note: We removed the "urgency == 'high'" override because the individual
        # AI algorithms already have safety checks built in (from STEP 1)
        # This prevents unnecessary slowdown
        
        if primary_system == 'safety':
            # Only use safety-first mode if safety is actually the primary system
            # This should be rare since safety weight is usually not the highest
            self._execute_safety_influenced_decision(
                safety_check, fuzzy_controller, weights
            )
        
        elif primary_system == 'fuzzy':
            # Fuzzy-primary mode with safety awareness (already built-in)
            self.ai_decision_fuzzy(
                traffic_cars, powerups, opponent, ghost_mode, fuzzy_controller
            )
        
        elif primary_system == 'minimax':
            # Minimax-primary mode with safety awareness
            self.ai_decision_minimax(
                traffic_cars, powerups, opponent, ghost_mode, minimax_solver
            )
        
        elif primary_system == 'astar':
            # A*-primary mode with safety awareness
            self.ai_decision_astar(
                traffic_cars, powerups, opponent, ghost_mode, astar_pathfinder
            )
        
        # ===== POST-DECISION SAFETY CHECK (LIGHT MONITORING ONLY) =====
        # The algorithms already handle safety, this is just a final check
        # Only apply if CRITICAL danger is detected AND algorithm didn't handle it
        if urgency == 'critical' and safety_check['recommended_action']['brake_intensity'] > 0.9:
            # Only in extreme cases, apply minimal corrective braking
            # Check if speed is still too high for the danger level
            if self.speed > self.max_speed * 0.70:
                brake_amount = safety_check['recommended_action']['brake_intensity'] * 0.2
                self.speed = max(self.speed - self.brake_rate * brake_amount, 
                               self.max_speed * 0.60)
    
    def _execute_safety_override(self, safety_check, fuzzy_controller):
        """Execute emergency safety override with maximum priority"""
        current_lane = fuzzy_controller.get_lane_from_x(self.x)
        
        # Apply emergency braking
        brake_intensity = safety_check['recommended_action']['brake_intensity']
        self.speed = max(self.speed - self.brake_rate * 2.0, self.max_speed * 0.25)
        
        # Execute emergency lane change if recommended
        if safety_check['recommended_action']['should_change_lane']:
            safe_lanes = safety_check['safe_lanes']
            target_lane = min(safe_lanes, key=lambda lane: abs(lane - current_lane))
            target_x = fuzzy_controller.lane_positions[target_lane]
            
            if abs(target_x - self.x) > 5:
                steering_speed = 14  # Maximum emergency
                if target_x < self.x:
                    self.x = max(ROAD_X + 35, self.x - steering_speed)
                else:
                    self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
        
        self.enforce_speed_limit()
    
    def _execute_safety_influenced_decision(self, safety_check, fuzzy_controller, weights):
        """Execute decision with strong safety influence"""
        current_lane = fuzzy_controller.get_lane_from_x(self.x)
        
        # Apply proportional braking based on safety recommendation
        brake_intensity = safety_check['recommended_action']['brake_intensity']
        
        if brake_intensity > 0.6:
            # Strong brake
            self.speed = max(self.speed - self.brake_rate * 1.3, self.max_speed * 0.40)
        elif brake_intensity > 0.3:
            # Moderate brake
            self.speed = max(self.speed - self.brake_rate * 0.8, self.max_speed * 0.60)
        elif brake_intensity > 0:
            # Light brake
            self.speed = max(self.speed - self.brake_rate * 0.4, self.max_speed * 0.75)
        
        # Execute lane change if strongly recommended
        if safety_check['recommended_action']['should_change_lane']:
            safe_lanes = safety_check['safe_lanes']
            
            if safe_lanes:
                target_lane = min(safe_lanes, key=lambda lane: abs(lane - current_lane))
                target_x = fuzzy_controller.lane_positions[target_lane]
                
                if abs(target_x - self.x) > 5:
                    # Steering speed proportional to urgency
                    urgency = safety_check['recommended_action']['urgency']
                    if urgency == 'high':
                        steering_speed = 12
                    elif urgency == 'moderate':
                        steering_speed = 9
                    else:
                        steering_speed = 7
                    
                    if target_x < self.x:
                        self.x = max(ROAD_X + 35, self.x - steering_speed)
                    else:
                        self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
        
        self.enforce_speed_limit()
    
    def predictive_safety_check(self, traffic_cars, fuzzy_controller):
        """
        ======================================================================
        PREDICTIVE SAFETY LAYER - STEP 1 IMPLEMENTATION
        ======================================================================
        This layer runs BEFORE any AI algorithm (A*, Minimax, Fuzzy, CSP)
        to prevent collisions by predicting future positions.
        
        Returns a safety analysis dict with:
        - danger_detected: bool (is collision imminent?)
        - time_to_collision: float (frames until collision)
        - current_lane_safe: bool (can stay in current lane?)
        - safe_lanes: list (which lanes are safe to move to?)
        - recommended_action: dict (what to do immediately)
        ======================================================================
        """
        # Get current lane
        current_lane = fuzzy_controller.get_lane_from_x(self.x)
        
        # Dynamic prediction window based on speed
        # Faster speed = look further ahead
        base_prediction_frames = 40  # ~0.67 seconds at 60 FPS
        speed_multiplier = max(1.0, self.speed / 4.0)  # Scale with speed
        prediction_frames = int(base_prediction_frames * speed_multiplier)
        
        # Calculate predicted position
        predicted_distance = self.distance + (self.speed * prediction_frames)
        
        # Safety margins (speed-aware)
        critical_distance = 150 + (self.speed * 20)  # Very dangerous
        warning_distance = 300 + (self.speed * 35)   # Should act soon
        safe_distance = 500 + (self.speed * 50)      # Monitor but OK
        
        # Lane change execution time calculation
        lane_width = 166  # ROAD_WIDTH / 3
        max_steering_speed = 14  # units per frame
        frames_to_change_lane = lane_width / max_steering_speed  # ~12 frames
        distance_traveled_during_change = self.speed * frames_to_change_lane
        
        # Analyze each lane comprehensively
        lane_analysis = {
            0: {'obstacles': [], 'min_distance': float('inf'), 'is_safe': True, 'risk_score': 0},
            1: {'obstacles': [], 'min_distance': float('inf'), 'is_safe': True, 'risk_score': 0},
            2: {'obstacles': [], 'min_distance': float('inf'), 'is_safe': True, 'risk_score': 0}
        }
        
        # Scan all traffic for threats
        for car in traffic_cars:
            # Calculate relative position
            relative_distance = car.distance - self.distance
            
            # Only check obstacles ahead within prediction window
            if 0 < relative_distance < predicted_distance - self.distance + 200:
                
                # Get traffic car speed (if available)
                traffic_speed = car.speed if hasattr(car, 'speed') else 3.0
                
                # Calculate RELATIVE SPEED (key for accurate prediction!)
                relative_speed = self.speed - traffic_speed
                
                # Time to collision calculation
                if relative_speed > 0.1:  # We're catching up
                    time_to_collision = relative_distance / relative_speed
                else:
                    time_to_collision = float('inf')  # Moving apart or same speed
                
                # Predict where obstacle will be when we reach it
                frames_to_reach = time_to_collision
                obstacle_future_distance = car.distance + (traffic_speed * frames_to_reach)
                vehicle_future_distance = self.distance + (self.speed * frames_to_reach)
                predicted_gap = obstacle_future_distance - vehicle_future_distance
                
                # Add to lane analysis
                lane_data = lane_analysis[car.lane]
                lane_data['obstacles'].append({
                    'current_distance': relative_distance,
                    'predicted_gap': predicted_gap,
                    'time_to_collision': time_to_collision,
                    'relative_speed': relative_speed
                })
                
                # Update minimum distance for this lane
                if relative_distance < lane_data['min_distance']:
                    lane_data['min_distance'] = relative_distance
                
                # Risk scoring based on predicted collision
                if time_to_collision < prediction_frames:
                    # CRITICAL: Collision will happen within prediction window
                    if predicted_gap < 100:
                        lane_data['risk_score'] += 1000  # Extreme danger
                        lane_data['is_safe'] = False
                    elif predicted_gap < 200:
                        lane_data['risk_score'] += 500  # High danger
                        lane_data['is_safe'] = False
                    elif predicted_gap < 300:
                        lane_data['risk_score'] += 200  # Moderate danger
                
                # Additional risk for close obstacles
                if relative_distance < critical_distance:
                    lane_data['risk_score'] += 800
                    lane_data['is_safe'] = False
                elif relative_distance < warning_distance:
                    lane_data['risk_score'] += 300
        
        # Check for side collision risk when changing lanes
        for target_lane in range(3):
            if target_lane != current_lane:
                for car in traffic_cars:
                    if car.lane == target_lane:
                        relative_distance = car.distance - self.distance
                        # Side-by-side or very close = cannot change to this lane
                        if -100 < relative_distance < distance_traveled_during_change + 100:
                            lane_analysis[target_lane]['risk_score'] += 2000
                            lane_analysis[target_lane]['is_safe'] = False
        
        # Determine current lane safety
        current_lane_info = lane_analysis[current_lane]
        danger_detected = not current_lane_info['is_safe']
        
        # Find safest lanes
        safe_lanes = [lane for lane, info in lane_analysis.items() if info['is_safe']]
        
        # If no lanes are perfectly safe, find LEAST dangerous
        if not safe_lanes:
            safest_lane = min(lane_analysis.keys(), key=lambda x: lane_analysis[x]['risk_score'])
            safe_lanes = [safest_lane]
        
        # Calculate time to collision in current lane
        min_ttc = float('inf')
        for obstacle in current_lane_info['obstacles']:
            if obstacle['time_to_collision'] < min_ttc:
                min_ttc = obstacle['time_to_collision']
        
        # Determine recommended action
        recommended_action = {
            'brake_intensity': 0.0,  # 0.0 to 1.0
            'should_change_lane': False,
            'target_lanes': safe_lanes,
            'urgency': 'none'  # 'critical', 'high', 'moderate', 'low', 'none'
        }
        
        if danger_detected:
            if current_lane_info['min_distance'] < critical_distance:
                # CRITICAL: Immediate action required
                recommended_action['urgency'] = 'critical'
                recommended_action['brake_intensity'] = 1.0  # Maximum braking
                if current_lane not in safe_lanes:
                    recommended_action['should_change_lane'] = True
            
            elif current_lane_info['min_distance'] < warning_distance:
                # HIGH: Act now to prevent collision
                recommended_action['urgency'] = 'high'
                recommended_action['brake_intensity'] = 0.7
                if len(safe_lanes) > 0 and current_lane not in safe_lanes:
                    recommended_action['should_change_lane'] = True
            
            else:
                # MODERATE: Prepare for evasion
                recommended_action['urgency'] = 'moderate'
                recommended_action['brake_intensity'] = 0.4
                if current_lane not in safe_lanes:
                    recommended_action['should_change_lane'] = True
        
        elif current_lane_info['min_distance'] < safe_distance:
            # LOW: Monitor situation, slight caution
            recommended_action['urgency'] = 'low'
            recommended_action['brake_intensity'] = 0.2
        
        # Return comprehensive safety analysis
        return {
            'danger_detected': danger_detected,
            'time_to_collision': min_ttc,
            'current_lane': current_lane,
            'current_lane_safe': current_lane_info['is_safe'],
            'current_lane_risk': current_lane_info['risk_score'],
            'safe_lanes': safe_lanes,
            'lane_analysis': lane_analysis,
            'recommended_action': recommended_action,
            'prediction_frames': prediction_frames,
            'predicted_distance': predicted_distance
        }
    
    def ai_decision_csp(self, traffic_cars, powerups, opponent, ghost_mode, csp_solver):
        """
        Advanced AI decision making using CSP algorithm.
        Considers multiple constraints simultaneously for optimal decision.
        """
        if self.crashed:
            return
        
        # ======================================================================
        # PRIORITY 1: RUN PREDICTIVE SAFETY LAYER FIRST
        # ======================================================================
        from game import FuzzyLogicController
        fuzzy_temp = FuzzyLogicController() if not hasattr(self, '_fuzzy_temp') else self._fuzzy_temp
        if not hasattr(self, '_fuzzy_temp'):
            self._fuzzy_temp = fuzzy_temp
        
        safety_check = self.predictive_safety_check(traffic_cars, fuzzy_temp)
        current_lane = csp_solver.get_lane_from_x(self.x)
        
        # If CRITICAL or HIGH danger detected, OVERRIDE CSP with safety actions
        if safety_check['recommended_action']['urgency'] in ['critical', 'high']:
            # EMERGENCY MODE: Safety takes absolute priority
            
            # Apply emergency braking
            brake_intensity = safety_check['recommended_action']['brake_intensity']
            if brake_intensity > 0.8:
                self.speed = max(self.speed - self.brake_rate * 2.0, self.max_speed * 0.25)
            elif brake_intensity > 0.5:
                self.speed = max(self.speed - self.brake_rate * 1.5, self.max_speed * 0.40)
            else:
                self.speed = max(self.speed - self.brake_rate * 1.0, self.max_speed * 0.55)
            
            # Execute emergency lane change if recommended
            if safety_check['recommended_action']['should_change_lane']:
                safe_lanes = safety_check['safe_lanes']
                target_lane = min(safe_lanes, key=lambda lane: abs(lane - current_lane))
                target_x = csp_solver.lane_positions[target_lane]
                
                if abs(target_x - self.x) > 5:
                    steering_speed = 14
                    if target_x < self.x:
                        self.x = max(ROAD_X + 35, self.x - steering_speed)
                    else:
                        self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
            
            self.enforce_speed_limit()
            return
        
        # ======================================================================
        # PRIORITY 2: CONTINUE WITH NORMAL CSP LOGIC
        # ======================================================================
        
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
                # Maintain at FULL max speed - no reduction
                if self.speed < self.max_speed - 0.1:
                    self.speed = min(self.speed + 0.08, self.max_speed)
            elif speed_action == 'brake':
                self.speed = max(self.speed - 0.3, self.max_speed * 0.5)
    
    def ai_decision_minimax(self, traffic_cars, powerups, opponent, ghost_mode, minimax_solver):
        """
        Advanced AI decision making using Minimax with Alpha-Beta pruning.
        Anticipates opponent's moves and plans counter-strategies.
        
        Args:
            traffic_cars: List of traffic cars
            powerups: List of power-ups
            opponent: Opponent vehicle
            ghost_mode: If True, can pass through traffic
            minimax_solver: MinimaxDecisionMaker instance
        """
        if self.crashed:
            return
        
        # ======================================================================
        # PRIORITY 1: RUN PREDICTIVE SAFETY LAYER FIRST
        # ======================================================================
        # Need fuzzy_controller for lane detection
        from game import FuzzyLogicController  # Import if needed
        fuzzy_temp = FuzzyLogicController() if not hasattr(self, '_fuzzy_temp') else self._fuzzy_temp
        if not hasattr(self, '_fuzzy_temp'):
            self._fuzzy_temp = fuzzy_temp
        
        safety_check = self.predictive_safety_check(traffic_cars, fuzzy_temp)
        current_lane = minimax_solver.get_lane_from_x(self.x)
        
        # If CRITICAL danger detected, OVERRIDE minimax with safety actions
        if safety_check['recommended_action']['urgency'] == 'critical':
            # EMERGENCY MODE: Safety takes absolute priority
            
            # Apply emergency braking
            brake_intensity = safety_check['recommended_action']['brake_intensity']
            self.speed = max(self.speed - self.brake_rate * 2.0, self.max_speed * 0.25)
            
            # Execute emergency lane change if recommended
            if safety_check['recommended_action']['should_change_lane']:
                safe_lanes = safety_check['safe_lanes']
                target_lane = min(safe_lanes, key=lambda lane: abs(lane - current_lane))
                target_x = minimax_solver.lane_positions[target_lane]
                
                if abs(target_x - self.x) > 5:
                    steering_speed = 14
                    if target_x < self.x:
                        self.x = max(ROAD_X + 35, self.x - steering_speed)
                    else:
                        self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
            
            self.enforce_speed_limit()
            return
        
        # Apply caution if HIGH danger (but let minimax continue with awareness)
        if safety_check['recommended_action']['urgency'] == 'high':
            # Reduce speed proactively
            self.speed = max(self.speed - self.brake_rate * 0.8, self.max_speed * 0.50)
        
        # ======================================================================
        # PRIORITY 2: CONTINUE WITH NORMAL MINIMAX LOGIC
        # ======================================================================
        
        # Create current game state snapshot
        opponent_lane = minimax_solver.get_lane_from_x(opponent.x) if opponent else 1
        
        # Take snapshot of nearby traffic (within 1000 units)
        traffic_snapshot = []
        for car in traffic_cars:
            dist_to_car = abs(car.distance - self.distance)
            if dist_to_car < 1000:
                traffic_snapshot.append((car.lane, car.distance))
        
        # Take snapshot of nearby power-ups (within 1000 units)
        powerup_snapshot = []
        for powerup in powerups:
            if not powerup.collected:
                dist_to_powerup = abs(powerup.distance - self.distance)
                if dist_to_powerup < 1000:
                    powerup_snapshot.append((
                        powerup.lane,
                        powerup.distance,
                        powerup.power_type,
                        powerup.for_police
                    ))
        
        # Create game state - FIXED: Correct police/thief assignment
        if self.is_police:
            # Current vehicle is police
            game_state = GameState(
                police_lane=current_lane,
                police_distance=self.distance,
                police_speed=self.speed,
                thief_lane=opponent_lane,
                thief_distance=opponent.distance,
                thief_speed=opponent.speed,
                traffic_snapshot=traffic_snapshot,
                powerups_snapshot=powerup_snapshot
            )
        else:
            # Current vehicle is thief
            game_state = GameState(
                police_lane=opponent_lane,
                police_distance=opponent.distance,
                police_speed=opponent.speed,
                thief_lane=current_lane,
                thief_distance=self.distance,
                thief_speed=self.speed,
                traffic_snapshot=traffic_snapshot,
                powerups_snapshot=powerup_snapshot
            )
        
        # Get best move from Minimax
        best_action = minimax_solver.get_best_move(game_state, self.is_police, max_time_ms=15)
        
        # Execute the action
        if best_action:
            # Convert lane to x position
            target_x = minimax_solver.lane_positions[best_action.lane]
            
            # IMPROVED: More aggressive steering for faster lane changes
            distance_to_target = abs(target_x - self.x)
            
            if distance_to_target > 5:
                # Check if there's traffic ahead - steer faster to avoid
                traffic_ahead_close = False
                for car in traffic_cars:
                    car_lane = minimax_solver.get_lane_from_x(car.x)
                    if car_lane == current_lane:
                        if 0 < car.distance - self.distance < 200:
                            traffic_ahead_close = True
                            break
                
                # Faster steering when avoiding traffic or at high speed - BOTH EQUALLY FAST!
                if not self.is_police:
                    # THIEF: Extra aggressive steering
                    if traffic_ahead_close:
                        steering_speed = 10  # THIEF emergency: faster!
                    elif self.speed > 6:
                        steering_speed = 8  # Fast lane change
                    else:
                        steering_speed = 7  # Normal lane change
                else:
                    # POLICE: MATCH THIEF - Must avoid crashes to catch!
                    if traffic_ahead_close:
                        steering_speed = 10  # INCREASED from 8 - Match thief!
                    elif self.speed > 6:
                        steering_speed = 8  # INCREASED from 6 - Fast!
                    else:
                        steering_speed = 7  # INCREASED from 5 - Normal
                
                if target_x < self.x:
                    self.x = max(ROAD_X + 35, self.x - steering_speed)
                else:
                    self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
            
            # Execute speed action with INDEPENDENT acceleration rates
            if not self.crashed:
                # ===== SPECIAL ESCAPE MODE: When opponent is very close =====
                if opponent and not self.is_police:
                    distance_to_police = abs(opponent.distance - self.distance)
                    if distance_to_police < 200:
                        # THIEF PANIC MODE: Police very close - maximum aggression!
                        if best_action.speed_change != 'brake':
                            # Override to FULL SPEED acceleration
                            self.speed = min(self.speed + self.acceleration_rate * 1.5, self.max_speed)
                        else:
                            # Even when braking, do it minimally to maintain speed
                            self.speed = max(self.speed - self.brake_rate * 0.6, self.max_speed * 0.70)
                    elif distance_to_police < 400:
                        # THIEF ALERT MODE: Police approaching - high aggression
                        if best_action.speed_change == 'accelerate':
                            self.speed = min(self.speed + self.acceleration_rate * 1.4, self.max_speed)
                        elif best_action.speed_change == 'maintain':
                            # Push hard to max speed
                            self.speed = min(self.speed + self.acceleration_rate * 1.2, self.max_speed)
                        elif best_action.speed_change == 'brake':
                            # Light braking only
                            self.speed = max(self.speed - self.brake_rate * 0.7, self.max_speed * 0.65)
                    else:
                        # Normal execution when police is far
                        if best_action.speed_change == 'accelerate':
                            accel_mult = 1.3
                            self.speed = min(self.speed + self.acceleration_rate * accel_mult, self.max_speed)
                        elif best_action.speed_change == 'maintain':
                            if self.speed < self.max_speed - 0.1:
                                self.speed = min(self.speed + self.acceleration_rate * 1.0, self.max_speed)
                        elif best_action.speed_change == 'brake':
                            self.speed = max(self.speed - self.brake_rate, self.max_speed * 0.5)
                else:
                    # POLICE execution (unchanged) or no opponent
                    if best_action.speed_change == 'accelerate':
                        accel_mult = 1.3
                        self.speed = min(self.speed + self.acceleration_rate * accel_mult, self.max_speed)
                    elif best_action.speed_change == 'maintain':
                        if self.speed < self.max_speed - 0.1:
                            self.speed = min(self.speed + self.acceleration_rate * 1.0, self.max_speed)
                    elif best_action.speed_change == 'brake':
                        self.speed = max(self.speed - self.brake_rate, self.max_speed * 0.5)
        
        # ENFORCE 200 km/h SPEED LIMIT
        self.enforce_speed_limit()
    
    def ai_decision_fuzzy(self, traffic_cars, powerups, opponent, ghost_mode, fuzzy_controller):
        """
        Advanced AI decision making using Fuzzy Logic.
        Provides human-like gradual decision making with smooth transitions.
        
        Args:
            traffic_cars: List of traffic cars
            powerups: List of power-ups
            opponent: Opponent vehicle
            ghost_mode: If True, can pass through traffic
            fuzzy_controller: FuzzyLogicController instance
        """
        if self.crashed:
            return
        
        # ======================================================================
        # PRIORITY 1: RUN PREDICTIVE SAFETY LAYER FIRST
        # ======================================================================
        safety_check = self.predictive_safety_check(traffic_cars, fuzzy_controller)
        
        # Get current lane
        current_lane = fuzzy_controller.get_lane_from_x(self.x)
        
        # If CRITICAL or HIGH danger detected, OVERRIDE fuzzy logic with safety actions
        if safety_check['recommended_action']['urgency'] in ['critical', 'high']:
            # EMERGENCY MODE: Safety takes absolute priority
            
            # Apply emergency braking
            brake_intensity = safety_check['recommended_action']['brake_intensity']
            if brake_intensity > 0.8:
                # Critical braking
                self.speed = max(self.speed - self.brake_rate * 2.0, self.max_speed * 0.25)
            elif brake_intensity > 0.5:
                # Strong braking
                self.speed = max(self.speed - self.brake_rate * 1.5, self.max_speed * 0.40)
            else:
                # Moderate braking
                self.speed = max(self.speed - self.brake_rate * 1.0, self.max_speed * 0.55)
            
            # Execute emergency lane change if recommended
            if safety_check['recommended_action']['should_change_lane']:
                safe_lanes = safety_check['safe_lanes']
                
                # Choose the closest safe lane
                target_lane = min(safe_lanes, key=lambda lane: abs(lane - current_lane))
                target_x = fuzzy_controller.lane_positions[target_lane]
                
                # AGGRESSIVE emergency steering
                if abs(target_x - self.x) > 5:
                    steering_speed = 14  # Maximum emergency speed
                    if target_x < self.x:
                        self.x = max(ROAD_X + 35, self.x - steering_speed)
                    else:
                        self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
            
            # Skip normal fuzzy logic - safety handled the situation
            self.enforce_speed_limit()
            return
        
        # ======================================================================
        # PRIORITY 2: CONTINUE WITH NORMAL FUZZY LOGIC (if no emergency)
        # ======================================================================
        
        # ===== SMART OBSTACLE ANALYSIS =====
        # Check what obstacles are ahead and if lane change is possible
        nearest_obstacle_dist = 10000
        can_safely_change_lane = False
        best_escape_lane = current_lane
        
        for car in traffic_cars:
            if car.lane == current_lane:
                dist = car.distance - self.distance
                if 0 < dist:
                    nearest_obstacle_dist = min(nearest_obstacle_dist, dist)
        
        # Intelligently check if lane change is a GOOD option
        for check_lane in range(3):
            if check_lane != current_lane:
                lane_is_safe = True
                min_clearance_in_lane = 10000
                
                for car in traffic_cars:
                    if car.lane == check_lane:
                        dist = car.distance - self.distance
                        min_clearance_in_lane = min(min_clearance_in_lane, abs(dist))
                        
                        # Need clear space (speed-aware safety margin)
                        safety_margin = 220 + (self.speed * 30)
                        if abs(dist) < safety_margin:
                            lane_is_safe = False
                            break
                
                # Found a safe escape route
                if lane_is_safe and min_clearance_in_lane > nearest_obstacle_dist:
                    can_safely_change_lane = True
                    best_escape_lane = check_lane
                    break
        
        # ===== PROPER FUZZY SPEED CONTROL =====
        # Get fuzzy acceleration decision
        acceleration = fuzzy_controller.get_fuzzy_speed_control(
            vehicle=self,
            traffic_cars=traffic_cars,
            opponent=opponent,
            is_police=self.is_police
        )
        
        # SMART ADJUSTMENTS: Use context to refine fuzzy output
        
        # Case 1: Obstacle ahead but safe lane change available - PREPARE TO STEER
        if 200 < nearest_obstacle_dist < 400 and can_safely_change_lane:
            # Moderate braking, prepare to change lanes
            if acceleration < -0.5:
                acceleration = -0.3  # Reduce braking, prioritize lane change
        
        # Case 2: Obstacle close and NO safe escape - HARD BRAKE
        elif nearest_obstacle_dist < 180 and not can_safely_change_lane:
            acceleration = min(acceleration, -0.85)  # Strong emergency brake
        
        # Case 3: Path clear ahead - ACCELERATE CONFIDENTLY
        elif nearest_obstacle_dist > 600:
            if acceleration > 0:
                acceleration = max(acceleration, 0.4)  # Boost acceleration when clear
        
        # ===== APPLY SMOOTH SPEED CHANGES =====
        if not self.crashed:
            # ===== SPECIAL ESCAPE MODE for THIEF when police is close =====
            if opponent and not self.is_police:
                distance_to_police = abs(opponent.distance - self.distance)
                
                if distance_to_police < 200:
                    # PANIC ESCAPE: Police very close - override all logic!
                    if acceleration >= 0:
                        # Accelerate AGGRESSIVELY
                        self.speed = min(self.speed + self.acceleration_rate * 1.8, self.max_speed)
                    else:
                        # Minimal braking only
                        self.speed = max(self.speed - self.brake_rate * 0.5, self.max_speed * 0.75)
                    
                elif distance_to_police < 400:
                    # HIGH ALERT: Boost all acceleration, reduce braking
                    if acceleration > 0.3:
                        accel_multiplier = 1.6  # Extra boost when escaping
                        self.speed = min(self.speed + self.acceleration_rate * accel_multiplier, self.max_speed)
                    elif acceleration > 0.05:
                        accel_multiplier = 1.2  # Increased from 0.8
                        self.speed = min(self.speed + self.acceleration_rate * accel_multiplier, self.max_speed)
                    elif acceleration < -0.5:
                        # Reduce braking intensity when escaping
                        self.speed = max(self.speed - self.brake_rate * 1.0, self.max_speed * 0.50)
                    elif acceleration < -0.15:
                        self.speed = max(self.speed - self.brake_rate * 0.5, self.max_speed * 0.65)
                    else:
                        # Push to max speed when escaping
                        target_speed = self.max_speed
                        if self.speed < target_speed - 0.1:
                            self.speed = min(self.speed + self.acceleration_rate * 1.3, self.max_speed)
                else:
                    # Normal execution when police is far - standard Minimax logic
                    if acceleration > 0.3:
                        accel_multiplier = 1.4
                        self.speed = min(self.speed + self.acceleration_rate * accel_multiplier, self.max_speed)
                    elif acceleration > 0.05:
                        accel_multiplier = 0.8
                        self.speed = min(self.speed + self.acceleration_rate * accel_multiplier, self.max_speed)
                    elif acceleration < -0.5:
                        self.speed = max(self.speed - self.brake_rate * 1.5, self.max_speed * 0.35)
                    elif acceleration < -0.15:
                        self.speed = max(self.speed - self.brake_rate * 0.8, self.max_speed * 0.55)
                    else:
                        if nearest_obstacle_dist > 600:
                            target_speed = self.max_speed
                        elif nearest_obstacle_dist > 400:
                            target_speed = self.max_speed * 0.95
                        elif nearest_obstacle_dist > 250:
                            target_speed = self.max_speed * 0.85
                        else:
                            target_speed = self.max_speed * 0.70
                        
                        if self.speed < target_speed - 0.3:
                            self.speed = min(self.speed + self.acceleration_rate * 1.0, self.max_speed)
                        elif self.speed > target_speed + 0.3:
                            self.speed = max(self.speed - self.brake_rate * 0.4, target_speed)
            else:
                # POLICE or no opponent - normal execution
                if acceleration > 0.3:
                    accel_multiplier = 1.4
                    self.speed = min(self.speed + self.acceleration_rate * accel_multiplier, self.max_speed)
                elif acceleration > 0.05:
                    accel_multiplier = 0.8
                    self.speed = min(self.speed + self.acceleration_rate * accel_multiplier, self.max_speed)
                elif acceleration < -0.5:
                    self.speed = max(self.speed - self.brake_rate * 1.5, self.max_speed * 0.35)
                elif acceleration < -0.15:
                    self.speed = max(self.speed - self.brake_rate * 0.8, self.max_speed * 0.55)
                else:
                    if nearest_obstacle_dist > 600:
                        target_speed = self.max_speed
                    elif nearest_obstacle_dist > 400:
                        target_speed = self.max_speed * 0.95
                    elif nearest_obstacle_dist > 250:
                        target_speed = self.max_speed * 0.85
                    else:
                        target_speed = self.max_speed * 0.70
                    
                    if self.speed < target_speed - 0.3:
                        self.speed = min(self.speed + self.acceleration_rate * 1.0, self.max_speed)
                    elif self.speed > target_speed + 0.3:
                        self.speed = max(self.speed - self.brake_rate * 0.4, target_speed)
        
        # ===== PRIORITY #1: INTELLIGENT LANE SAFETY ANALYSIS =====
        # Analyze ALL lanes comprehensively to find the SAFEST one
        
        lane_safety_scores = {}
        current_lane = fuzzy_controller.get_lane_from_x(self.x)        # Speed-based safety margin (faster = need more space)
        safety_margin = 250 + (self.speed * 35)
        emergency_distance = 200 + (self.speed * 25)
        
        for lane_idx in range(3):
            lane_score = 1000  # Start with high safety score
            obstacles_in_lane = []
            min_obstacle_dist = 10000
            has_immediate_danger = False
            has_side_collision_risk = False
            
            # Analyze ALL obstacles in this lane
            for car in traffic_cars:
                if car.lane == lane_idx:
                    dist = car.distance - self.distance
                    
                    # Check obstacles ahead (0 to 1000 units)
                    if 0 < dist < 1000:
                        obstacles_in_lane.append(dist)
                        min_obstacle_dist = min(min_obstacle_dist, dist)
                        
                        # CRITICAL: Immediate danger (very close obstacle)
                        if dist < emergency_distance:
                            has_immediate_danger = True
                            lane_score -= 500  # Massive penalty
                        
                        # Dangerous (close obstacle)
                        elif dist < safety_margin:
                            lane_score -= 300  # Heavy penalty
                        
                        # Caution (moderate distance)
                        elif dist < 500:
                            lane_score -= 100  # Moderate penalty
                        
                        # Visible (far but should consider)
                        elif dist < 800:
                            lane_score -= 30  # Light penalty
                    
                    # CRITICAL: Check for side-by-side collision when changing lanes
                    if lane_idx != current_lane:
                        # Car is beside us or very close - CANNOT CHANGE TO THIS LANE
                        if -80 < dist < 80:
                            has_side_collision_risk = True
                            lane_score = -10000  # Absolutely forbidden!
            
            # Additional scoring factors
            
            # Bonus for fewer obstacles
            lane_score -= len(obstacles_in_lane) * 50
            
            # Huge bonus for clear lane
            if len(obstacles_in_lane) == 0:
                lane_score += 500
            elif len(obstacles_in_lane) == 1 and min_obstacle_dist > 400:
                lane_score += 200
            
            # Prefer staying in current lane (stability bonus) - but not if dangerous
            if lane_idx == current_lane and not has_immediate_danger:
                lane_score += 150
            
            # Penalty for changing multiple lanes (risky)
            lane_difference = abs(lane_idx - current_lane)
            if lane_difference == 2:
                lane_score -= 100  # Avoid 2-lane changes unless necessary
            
            lane_safety_scores[lane_idx] = {
                'score': lane_score,
                'min_obstacle_dist': min_obstacle_dist,
                'obstacles_count': len(obstacles_in_lane),
                'immediate_danger': has_immediate_danger,
                'side_collision_risk': has_side_collision_risk
            }
        
        # ===== CHOOSE THE ABSOLUTELY SAFEST LANE =====
        safest_lane = max(lane_safety_scores, key=lambda x: lane_safety_scores[x]['score'])
        safest_lane_info = lane_safety_scores[safest_lane]
        current_lane_info = lane_safety_scores[current_lane]
        
        # Determine if lane change is NECESSARY and SAFE
        should_change_lane = False
        
        # EMERGENCY: Current lane has immediate danger - MUST move if possible
        if current_lane_info['immediate_danger'] and not safest_lane_info['side_collision_risk']:
            if safest_lane != current_lane and safest_lane_info['score'] > -1000:
                should_change_lane = True
        
        # PROACTIVE: Current lane worse than other lane - change if significantly better
        elif safest_lane != current_lane:
            score_difference = safest_lane_info['score'] - current_lane_info['score']
            # Only change if new lane is SIGNIFICANTLY better (at least 200 points)
            if score_difference > 200 and not safest_lane_info['side_collision_risk']:
                should_change_lane = True
        
        # ===== EXECUTE SMART LANE CHANGE =====
        if should_change_lane and safest_lane != current_lane:
            target_x = fuzzy_controller.lane_positions[safest_lane]
            distance_to_target = abs(target_x - self.x)
            
            if distance_to_target > 5:
                # Determine steering speed based on urgency
                if current_lane_info['immediate_danger']:
                    steering_speed = 14  # EMERGENCY: Move NOW!
                elif current_lane_info['min_obstacle_dist'] < 300:
                    steering_speed = 11  # URGENT: Move quickly
                elif safest_lane_info['score'] > current_lane_info['score'] + 400:
                    steering_speed = 9  # BENEFICIAL: Move steadily
                else:
                    steering_speed = 7  # CAUTIOUS: Move gently
                
                # Apply smooth steering with boundary checks
                if target_x < self.x:
                    self.x = max(ROAD_X + 35, self.x - steering_speed)
                else:
                    self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
        
        # ===== AGGRESSIVE POWER-UP COLLECTION - KEY TO WINNING! =====
        if not self.crashed:
            best_powerup = None
            best_powerup_score = 0
            
            for powerup in powerups:
                if powerup.collected:
                    continue
                
                # Check if power-up is for this vehicle
                if self.is_police and not powerup.for_police:
                    continue
                if not self.is_police and powerup.for_police:
                    continue
                
                # Check if power-up is nearby and reachable - EXTENDED RANGE!
                powerup_lane = powerup.lane
                distance_to_powerup = powerup.distance - self.distance
                
                # INCREASED from 400 to 600 - look further ahead for power-ups!
                if 0 < distance_to_powerup < 600:
                    # Strategic risk assessment for power-up collection
                    lane_diff = abs(powerup_lane - current_lane)
                    
                    # Calculate collection risk
                    traffic_in_powerup_lane = 0
                    min_traffic_dist = 10000
                    immediate_danger = False
                    
                    for car in traffic_cars:
                        if car.lane == powerup_lane:
                            car_dist = car.distance - self.distance
                            if 0 < car_dist < 400:  # Check ahead
                                traffic_in_powerup_lane += 1
                                min_traffic_dist = min(min_traffic_dist, car_dist)
                                # Check if obstacle is right at power-up location
                                if abs(car.distance - powerup.distance) < 80:
                                    immediate_danger = True
                    
                    # ENHANCED: Fuzzy decision with power priority and lane safety
                    collection_score = 0
                    
                    # NEW: Base score from power priority system (balanced values)
                    power_priority = powerup.get_priority_value()
                    collection_score += power_priority * 30  # Scale priority to meaningful score
                    
                    # Factor 1: Distance to power-up (closer = better) - INCREASED VALUES!
                    if distance_to_powerup < 150:
                        collection_score += 60  # INCREASED from 40
                    elif distance_to_powerup < 300:
                        collection_score += 40  # INCREASED from 25
                    elif distance_to_powerup < 450:
                        collection_score += 25  # NEW tier
                    else:
                        collection_score += 15  # INCREASED from 10
                    
                    # Factor 2: Lane difference with SAFETY CHECK
                    if lane_diff == 0:
                        collection_score += 70  # INCREASED from 50 - already in lane
                    elif lane_diff == 1:
                        # Check if target lane is safe before adding score
                        if self.is_lane_safe_for_powerup(powerup_lane, traffic_cars, lookahead=250):
                            collection_score += 35  # Safe to switch
                        else:
                            collection_score -= 20  # Unsafe lane - heavy penalty
                    else:  # lane_diff == 2
                        # Two lanes away - must check intermediate safety
                        if self.is_lane_safe_for_powerup(powerup_lane, traffic_cars, lookahead=250):
                            collection_score += 15  # Safe but far
                        else:
                            collection_score -= 30  # Very unsafe - heavy penalty
                    
                    # Factor 3: Traffic risk (clear = better) - MORE LENIENT!
                    if immediate_danger:
                        collection_score -= 50  # Dangerous obstacle at power-up
                    elif traffic_in_powerup_lane == 0:
                        collection_score += 40  # INCREASED from 30
                    elif traffic_in_powerup_lane == 1 and min_traffic_dist > 150:
                        collection_score += 25  # INCREASED from 15
                    elif traffic_in_powerup_lane <= 2 and min_traffic_dist > 100:
                        collection_score += 10  # NEW: Still worth it!
                    else:
                        collection_score -= 10  # REDUCED penalty from -20
                    
                    # Factor 4: Power-up value using PRIORITY SYSTEM (no longer hardcoded)
                    # Priority already added above, but add situational bonuses
                    # High-value defensive powers get extra boost
                    if powerup.power_type in ['ghost', 'shield', 'emp', 'magnet']:
                        collection_score += 20  # Bonus for high-priority powers
                    
                    # Factor 5: Opponent proximity - STRATEGIC NEED!
                    if opponent:
                        opponent_dist = opponent.distance - self.distance
                        if not self.is_police:
                            # THIEF: Defensive powers when police close - MASSIVELY INCREASED!
                            if opponent_dist < 200:  # Police VERY close - CRITICAL!
                                if powerup.power_type in ['freeze', 'shield', 'ghost']:
                                    collection_score += 100  # CRITICAL SURVIVAL!
                                elif powerup.power_type == 'boost':
                                    collection_score += 80  # Escape boost!
                            elif opponent_dist < 400:  # Police approaching
                                if powerup.power_type in ['freeze', 'shield', 'ghost']:
                                    collection_score += 60  # INCREASED from 50
                                elif powerup.power_type in ['boost', 'turbo']:
                                    collection_score += 50  # Speed escape!
                        else:
                            # POLICE: Offensive powers to catch thief
                            if opponent_dist < 300:  # Thief very close
                                if powerup.power_type in ['emp', 'spike', 'magnet']:
                                    collection_score += 70  # Catch opportunity!
                            elif opponent_dist < 500:  # Thief in range
                                if powerup.power_type in ['emp', 'turbo', 'magnet']:
                                    collection_score += 45  # INCREASED from 30 - ESSENTIAL!
                                elif powerup.power_type == 'roadblock':
                                    collection_score += 40  # Block thief's path!
                    
                    # Track best power-up
                    if collection_score > best_powerup_score:
                        best_powerup_score = collection_score
                        best_powerup = (powerup, powerup_lane)
            
            # EXECUTE: Go for best power-up if worth it
            # Dynamic threshold based on opponent proximity
            collection_threshold = 60  # Default threshold
            if opponent and not self.is_police:
                opponent_dist = opponent.distance - self.distance
                if opponent_dist < 200:
                    collection_threshold = 40  # Very aggressive when police close!
                elif opponent_dist < 400:
                    collection_threshold = 50  # Aggressive when police approaching
            
            if best_powerup and best_powerup_score > collection_threshold:
                powerup_lane = best_powerup[1]
                if powerup_lane != current_lane:
                    # AGGRESSIVE steering toward power-up
                    target_x = fuzzy_controller.lane_positions[powerup_lane]
                    if abs(target_x - self.x) > 5:
                        # FASTER steering for power-ups - they're important!
                        steering_speed = 9  # INCREASED from 6
                        if target_x < self.x:
                            self.x = max(ROAD_X + 35, self.x - steering_speed)
                        else:
                            self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
        
        # ENFORCE 200 km/h SPEED LIMIT
        self.enforce_speed_limit()
    
    def ai_decision_astar(self, traffic_cars, powerups, opponent, ghost_mode, astar_pathfinder):
        """
        Advanced AI decision making using A* pathfinding algorithm.
        Finds optimal path considering obstacles, opponent, and objectives.
        
        Args:
            traffic_cars: List of traffic cars to avoid
            powerups: List of power-ups to collect
            opponent: Opponent vehicle
            ghost_mode: If True, can pass through traffic
            astar_pathfinder: AStarPathfinder instance with appropriate heuristic
        """
        if self.crashed:
            return
        
        # ======================================================================
        # PRIORITY 1: RUN PREDICTIVE SAFETY LAYER FIRST
        # ======================================================================
        from game import FuzzyLogicController
        fuzzy_temp = FuzzyLogicController() if not hasattr(self, '_fuzzy_temp') else self._fuzzy_temp
        if not hasattr(self, '_fuzzy_temp'):
            self._fuzzy_temp = fuzzy_temp
        
        safety_check = self.predictive_safety_check(traffic_cars, fuzzy_temp)
        current_lane = astar_pathfinder.get_lane_from_x(self.x)
        
        # If CRITICAL or HIGH danger detected, OVERRIDE A* with safety actions
        if safety_check['recommended_action']['urgency'] in ['critical', 'high']:
            # EMERGENCY MODE: Safety takes absolute priority
            
            # Apply emergency braking
            brake_intensity = safety_check['recommended_action']['brake_intensity']
            if brake_intensity > 0.8:
                self.speed = max(self.speed - self.brake_rate * 2.0, self.max_speed * 0.25)
            elif brake_intensity > 0.5:
                self.speed = max(self.speed - self.brake_rate * 1.5, self.max_speed * 0.40)
            else:
                self.speed = max(self.speed - self.brake_rate * 1.0, self.max_speed * 0.55)
            
            # Execute emergency lane change if recommended
            if safety_check['recommended_action']['should_change_lane']:
                safe_lanes = safety_check['safe_lanes']
                target_lane = min(safe_lanes, key=lambda lane: abs(lane - current_lane))
                target_x = astar_pathfinder.lane_positions[target_lane]
                
                if abs(target_x - self.x) > 5:
                    steering_speed = 14
                    if target_x < self.x:
                        self.x = max(ROAD_X + 35, self.x - steering_speed)
                    else:
                        self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
            
            self.enforce_speed_limit()
            return
        
        # ======================================================================
        # PRIORITY 2: CONTINUE WITH NORMAL A* LOGIC
        # ======================================================================
        
        # Determine current position
        current_distance = self.distance
        
        # Determine goal based on vehicle type and situation
        goal_lane = current_lane
        goal_distance = current_distance + 500  # Default: look ahead 500 units
        
        if self.is_police:
            # Police goal: INDEPENDENT pursuit strategy
            if opponent:
                distance_to_thief = opponent.distance - self.distance
                
                # Police makes INDEPENDENT decisions based on distance to thief
                if distance_to_thief > 400:
                    # FAR BEHIND: Move forward aggressively, find clearest path
                    clearest_lane_info = astar_pathfinder.find_clearest_lane(
                        current_distance, traffic_cars, look_ahead=800
                    )
                    goal_lane = clearest_lane_info[0]  # Use clearest lane
                    goal_distance = current_distance + 900  # Move forward fast
                    
                elif distance_to_thief > 200:
                    # MEDIUM DISTANCE: STRATEGIC power-up collection with priority system
                    # Look for police power-ups - CRITICAL FOR CATCHING THIEF!
                    closest_police_powerup = None
                    min_powerup_dist = float('inf')
                    
                    for powerup in powerups:
                        if not powerup.collected and powerup.for_police:
                            dist_to_powerup = powerup.distance - current_distance
                            if 0 < dist_to_powerup < 900:  # INCREASED from 600 - Look further!
                                # Use PRIORITY SYSTEM instead of hardcoded values
                                power_priority = powerup.get_priority_value()
                                
                                # Convert priority to distance reduction (higher priority = "closer" in decision)
                                priority_bonus = -(power_priority * 200)  # Scale: 1.0-1.5 → -200 to -300
                                
                                effective_dist = dist_to_powerup + priority_bonus
                                
                                if effective_dist < min_powerup_dist:
                                    min_powerup_dist = effective_dist
                                    closest_police_powerup = powerup
                    
                    if closest_police_powerup:
                        # Go for police power-up with SAFETY CHECK
                        goal_distance = closest_police_powerup.distance
                        goal_lane = closest_police_powerup.lane
                        
                        # Use new lane safety method
                        is_lane_safe = self.is_lane_safe_for_powerup(goal_lane, traffic_cars, lookahead=300)
                        
                        # Additional immediate danger check
                        immediate_danger = False
                        for car in traffic_cars:
                            if car.lane == goal_lane:
                                if abs(car.distance - closest_police_powerup.distance) < 80:
                                    immediate_danger = True
                                    break
                        
                        # Only pursue if safe OR power-up is extremely valuable
                        if immediate_danger or not is_lane_safe:
                            # Too dangerous unless it's a critical power-up
                            if closest_police_powerup.get_priority_value() < 1.3:  # Not high priority
                                # Use clear lane instead
                                clearest_lane_info = astar_pathfinder.find_clearest_lane(
                                    current_distance, traffic_cars, look_ahead=700
                                )
                                goal_lane = clearest_lane_info[0]
                                goal_distance = current_distance + 700
                        # Else: GO FOR IT! Powers are essential!
                        # Go for police power-up
                        goal_distance = closest_police_powerup.distance
                        goal_lane = closest_police_powerup.lane
                    else:
                        # Move toward thief's general direction but use clear lanes
                        thief_lane = astar_pathfinder.get_lane_from_x(opponent.x)
                        
                        # Check if thief's lane is clear
                        lane_traffic_count = 0
                        for car in traffic_cars:
                            if car.lane == thief_lane:
                                dist_to_car = car.distance - current_distance
                                if 0 < dist_to_car < 500:
                                    lane_traffic_count += 1
                        
                        if lane_traffic_count > 2:
                            # Thief's lane is crowded, find better route
                            clearest_lane_info = astar_pathfinder.find_clearest_lane(
                                current_distance, traffic_cars, look_ahead=700
                            )
                            goal_lane = clearest_lane_info[0]
                        else:
                            # Thief's lane is relatively clear, approach that direction
                            goal_lane = thief_lane
                        
                        goal_distance = current_distance + 700
                
                elif distance_to_thief > 50:
                    # CLOSE RANGE: Careful approach, avoid overtaking
                    goal_distance = opponent.distance - 50  # Stay behind
                    # Don't just copy thief's lane - evaluate best interception
                    thief_lane = astar_pathfinder.get_lane_from_x(opponent.x)
                    
                    # Check adjacent lanes for better positioning
                    best_intercept_lane = thief_lane
                    min_obstacles = float('inf')
                    
                    for check_lane in [max(0, thief_lane - 1), thief_lane, min(2, thief_lane + 1)]:
                        obstacle_count = 0
                        for car in traffic_cars:
                            if car.lane == check_lane:
                                dist_to_car = abs(car.distance - goal_distance)
                                if dist_to_car < 300:
                                    obstacle_count += 1
                        if obstacle_count < min_obstacles:
                            min_obstacles = obstacle_count
                            best_intercept_lane = check_lane
                    
                    goal_lane = best_intercept_lane
                
                else:
                    # VERY CLOSE or EQUAL: CATCH POSITION - stay at or slightly behind thief
                    goal_distance = max(opponent.distance - 20, current_distance)  # Never plan ahead!
                    goal_lane = astar_pathfinder.get_lane_from_x(opponent.x)
            else:
                # No opponent visible, move forward using clearest lane
                clearest_lane_info = astar_pathfinder.find_clearest_lane(
                    current_distance, traffic_cars, look_ahead=800
                )
                goal_lane = clearest_lane_info[0]
                goal_distance = current_distance + 800
        else:
            # Thief goal: AGGRESSIVE power-up collection for survival!
            # Priority 1: Look for valuable power-ups - CRITICAL FOR WINNING!
            closest_powerup = None
            min_powerup_dist = float('inf')
            
            for powerup in powerups:
                if not powerup.collected and not powerup.for_police:
                    # Check if powerup is ahead and reachable - EXTENDED RANGE!
                    dist_to_powerup = powerup.distance - current_distance
                    if 0 < dist_to_powerup < 1500:  # INCREASED from 1200 - Look further!
                        # STRATEGIC: Prioritize based on power-up type and situation
                        priority_bonus = 0
                        
                        # Check police proximity for context
                        police_close = False
                        if opponent:
                            police_dist = opponent.distance - current_distance
                            if police_dist > -400:  # Police within 400m
                                police_close = True
                        
                        # GAME-CHANGING POWERS - TOP PRIORITY!
                        if powerup.power_type == 'freeze':
                            priority_bonus = -300  # INCREASED - Can freeze police!
                        elif powerup.power_type == 'ghost':
                            priority_bonus = -250  # INCREASED - Pass through obstacles!
                        elif powerup.power_type == 'shield':
                            priority_bonus = -250  # INCREASED - Prevents crashes!
                        elif powerup.power_type == 'turbo' or powerup.power_type == 'boost':
                            priority_bonus = -200  # INCREASED - Speed advantage!
                        else:
                            priority_bonus = -100  # All powers are valuable!
                        
                        # EXTRA BONUS if police is close - DESPERATE NEED!
                        if police_close:
                            if powerup.power_type in ['freeze', 'shield', 'ghost']:
                                priority_bonus -= 150  # CRITICAL when police near!
                        
                        effective_distance = dist_to_powerup + priority_bonus
                        
                        if effective_distance < min_powerup_dist:
                            min_powerup_dist = effective_distance
                            closest_powerup = powerup
            
            if closest_powerup:
                # Target the power-up with MORE LENIENT traffic check
                goal_distance = closest_powerup.distance
                goal_lane = closest_powerup.lane
                
                # Verify lane safety - MORE TOLERANT!
                traffic_in_lane = 0
                immediate_danger = False
                for car in traffic_cars:
                    if car.lane == goal_lane:
                        dist_to_car = car.distance - current_distance
                        if 0 < dist_to_car < 500:
                            traffic_in_lane += 1
                            # Check if obstacle right at power-up
                            if abs(car.distance - closest_powerup.distance) < 80:
                                immediate_danger = True
                
                # Only abandon power-up if VERY dangerous
                if immediate_danger or traffic_in_lane > 5:  # INCREASED from 3 - More willing to take risks!
                    clearest_lane_info = astar_pathfinder.find_clearest_lane(
                        current_distance, traffic_cars, look_ahead=800
                    )
                    goal_lane = clearest_lane_info[0]
                    goal_distance = current_distance + 800
                # Else: GO FOR IT! Power-ups are worth the risk!
            else:
                # Priority 2: No power-ups nearby - focus on maintaining lead
                # Always use clearest lane for fastest progress
                clearest_lane_info = astar_pathfinder.find_clearest_lane(
                    current_distance, traffic_cars, look_ahead=1000
                )
                goal_lane = clearest_lane_info[0]  # Use clearest lane
                
                # Adjust distance based on police proximity
                if opponent:
                    distance_to_police = opponent.distance - current_distance
                    
                    if distance_to_police > -100:  # Police very close (danger!)
                        # URGENT: Maximum speed escape
                        goal_distance = current_distance + 1000
                    elif distance_to_police > -300:  # Police approaching
                        # Move ahead aggressively
                        goal_distance = current_distance + 850
                    else:
                        # Safe distance, maintain steady progress
                        goal_distance = current_distance + 700
                else:
                    # No police visible, steady progress
                    goal_distance = current_distance + 750
        
        # Find path using A* (with speed-aware pathfinding)
        path = astar_pathfinder.find_path(
            start_lane=current_lane,
            start_distance=current_distance,
            goal_lane=goal_lane,
            goal_distance=goal_distance,
            traffic_cars=traffic_cars,
            opponent=opponent,
            ghost_mode=ghost_mode,
            is_police=self.is_police,
            vehicle_speed=self.speed  # Pass current speed for dynamic safety margins
        )
        
        # Execute path: follow the first few waypoints
        if len(path) > 1:
            # Get next waypoint
            next_waypoint = path[1] if len(path) > 1 else path[0]
            target_lane = next_waypoint[0]
            target_distance = next_waypoint[1]
            
            # Convert lane to x position
            target_x = astar_pathfinder.lane_positions[target_lane]
            
            # IMPROVED: Faster steering for better obstacle avoidance
            if abs(target_x - self.x) > 5:
                # Check for obstacles to determine urgency
                obstacle_very_close = False
                for car in traffic_cars:
                    if car.lane == current_lane:
                        dist = car.distance - self.distance
                        if 0 < dist < 200:  # Very close obstacle
                            obstacle_very_close = True
                            break
                
                # BOTH police and thief need fast steering to avoid crashes!
                if obstacle_very_close:
                    steering_speed = 10  # Emergency steering
                elif self.speed > 6:
                    steering_speed = 8  # Fast steering at high speed
                else:
                    steering_speed = 7  # Normal steering
                
                if target_x < self.x:
                    self.x = max(ROAD_X + 35, self.x - steering_speed)
                else:
                    self.x = min(ROAD_X + ROAD_WIDTH - 35, self.x + steering_speed)
            
            # Speed control based on path and situation with INDEPENDENT rates
            if not self.crashed:
                # IMPROVED: Check obstacles ahead with better detection - MORE AGGRESSIVE!
                obstacle_ahead = False
                closest_obstacle_distance = float('inf')
                
                for car in traffic_cars:
                    if car.lane == current_lane:
                        distance_to_car = car.distance - self.distance
                        # Look MUCH further ahead for better reaction time
                        look_ahead = 500 + (self.speed * 60)  # Speed-based look-ahead
                        if 0 < distance_to_car < look_ahead and not ghost_mode:
                            obstacle_ahead = True
                            closest_obstacle_distance = min(closest_obstacle_distance, distance_to_car)
                
                # CRITICAL: Police speed control to prevent overtaking
                if self.is_police and opponent:
                    distance_to_thief = opponent.distance - self.distance
                    
                    # ZONE 1: Very close - extremely careful (CATCH zone)
                    if distance_to_thief < 50:
                        # At catch distance - move slowly to avoid overtaking
                        target_speed = min(opponent.speed * 0.7, self.max_speed * 0.5)
                        self.speed = max(self.speed - self.brake_rate * 1.5, target_speed)
                        return  # Stop here, don't process further
                    
                    # ZONE 2: Close - match speed carefully
                    elif distance_to_thief < 100:
                        # Getting close - match thief's speed exactly
                        target_speed = min(opponent.speed, self.max_speed * 0.85)
                        if self.speed > target_speed:
                            self.speed = max(self.speed - self.brake_rate, target_speed)
                        else:
                            self.speed = min(self.speed + self.acceleration_rate * 0.5, target_speed)
                        return  # Don't accelerate further
                    
                    # ZONE 3: Medium close - start slowing approach
                    elif distance_to_thief < 150:
                        # Approaching - slow down gradually
                        target_speed = min(opponent.speed * 1.1, self.max_speed * 0.9)
                        if self.speed > target_speed:
                            self.speed = max(self.speed - self.brake_rate * 0.7, target_speed)
                        else:
                            self.speed = min(self.speed + self.acceleration_rate * 0.8, target_speed)
                        return
                    
                    # ZONE 4: If somehow ahead (shouldn't happen) - STOP IMMEDIATELY
                    elif distance_to_thief <= 0:
                        # Police is ahead or equal - STOP to catch
                        self.speed = max(self.speed - self.brake_rate * 2, 2)  # Minimum speed to maintain
                        return
                
                # IMPROVED: Adaptive speed control based on obstacle distance - MORE AGGRESSIVE!
                if obstacle_ahead:
                    # CRITICAL: Much more aggressive braking for crash prevention
                    if closest_obstacle_distance < 120:
                        # EMERGENCY: Very close - MAXIMUM BRAKE!
                        self.speed = max(self.speed - self.brake_rate * 2.5, self.max_speed * 0.3)
                    elif closest_obstacle_distance < 200:
                        # CRITICAL: Close obstacle - very strong brake
                        self.speed = max(self.speed - self.brake_rate * 1.8, self.max_speed * 0.5)
                    elif closest_obstacle_distance < 300:
                        # Close - significant brake
                        self.speed = max(self.speed - self.brake_rate * 1.2, self.max_speed * 0.65)
                    elif closest_obstacle_distance < 450:
                        # Approaching - moderate brake
                        self.speed = max(self.speed - self.brake_rate * 0.7, self.max_speed * 0.80)
                    else:
                        # Far obstacle - slight reduction
                        self.speed = max(self.speed - self.brake_rate * 0.3, self.max_speed * 0.90)
                else:
                    # No obstacles - BOTH accelerate aggressively when clear!
                    self.speed = min(self.speed + self.acceleration_rate * 1.2, self.max_speed)
        
        # ENFORCE 200 km/h SPEED LIMIT
        self.enforce_speed_limit()
    
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

def draw_hud(screen, player, police, traffic_cars, freeze_timer=0, boost_timer=0, shield_timer=0, ghost_timer=0, emp_timer=0, powerups_collected=0):
    """Enhanced HUD with TWO separate speed meters for Police and Thief"""
    # Top bar with gradient
    top_bar = pygame.Surface((SCREEN_WIDTH, 140), pygame.SRCALPHA)
    for i in range(140):
        alpha = int(200 - (i * 1.2))
        pygame.draw.line(top_bar, (0, 0, 0, alpha), (0, i), (SCREEN_WIDTH, i))
    screen.blit(top_bar, (0, 0))
    
    # Title with glow effect
    font_title = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 32)
    font_small = pygame.font.Font(None, 26)
    font_tiny = pygame.font.Font(None, 22)
    
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
    
    # ========== THIEF SPEED METER (LEFT SIDE) ==========
    thief_x = 30
    thief_y = 85
    
    # Thief label with icon
    thief_label = font_small.render("🏃 THIEF", True, RED)
    screen.blit(thief_label, (thief_x, thief_y))
    
    # Thief speed value
    thief_speed_value = player.get_speed_kmh()
    thief_speed_text = font_medium.render(f"{thief_speed_value} km/h", True, RED)
    screen.blit(thief_speed_text, (thief_x + 85, thief_y - 3))
    
    # Thief speed bar (horizontal)
    bar_width = 200
    bar_height = 24
    bar_y = thief_y + 30
    
    # Background bar
    pygame.draw.rect(screen, (40, 40, 40), (thief_x, bar_y, bar_width, bar_height), border_radius=12)
    
    # Filled portion for thief
    thief_filled = int((thief_speed_value / 200) * bar_width)
    if thief_speed_value >= 200:
        thief_bar_color = (255, 50, 50)  # Bright red at max
    elif thief_speed_value > 160:
        thief_bar_color = (255, 100, 50)  # Orange-red
    elif thief_speed_value > 120:
        thief_bar_color = (255, 150, 0)  # Orange
    elif thief_speed_value > 80:
        thief_bar_color = (255, 200, 0)  # Yellow
    else:
        thief_bar_color = (100, 255, 100)  # Green
    
    if thief_filled > 0:
        # Gradient effect
        for i in range(thief_filled):
            fade = 0.7 + (i / bar_width) * 0.3
            color = tuple(int(c * fade) for c in thief_bar_color)
            pygame.draw.rect(screen, color, (thief_x + i, bar_y, 1, bar_height))
        
        # Border around filled portion
        pygame.draw.rect(screen, thief_bar_color, (thief_x, bar_y, thief_filled, bar_height), 2, border_radius=12)
    
    # Speed limit marker at 200 km/h
    pygame.draw.line(screen, WHITE, (thief_x + bar_width, bar_y), (thief_x + bar_width, bar_y + bar_height), 3)
    limit_text = font_tiny.render("200", True, WHITE)
    screen.blit(limit_text, (thief_x + bar_width - 15, bar_y + bar_height + 2))
    
    # ========== POLICE SPEED METER (LEFT SIDE, BELOW THIEF) ==========
    police_x = thief_x  # Same X position as thief
    police_y = thief_y + 80  # Below thief speed meter
    
    # Police label with icon
    police_label = font_small.render("🚓 POLICE", True, BLUE)
    screen.blit(police_label, (police_x, police_y))
    
    # Police speed value
    police_speed_value = police.get_speed_kmh()
    police_speed_text = font_medium.render(f"{police_speed_value} km/h", True, BLUE)
    screen.blit(police_speed_text, (police_x + 100, police_y - 3))
    
    # Police speed bar (horizontal)
    bar_y_police = police_y + 30
    
    # Background bar
    pygame.draw.rect(screen, (40, 40, 40), (police_x, bar_y_police, bar_width, bar_height), border_radius=12)
    
    # Filled portion for police
    police_filled = int((police_speed_value / 200) * bar_width)
    if police_speed_value >= 200:
        police_bar_color = (50, 100, 255)  # Bright blue at max
    elif police_speed_value > 160:
        police_bar_color = (70, 130, 255)  # Light blue
    elif police_speed_value > 120:
        police_bar_color = (100, 150, 255)  # Sky blue
    elif police_speed_value > 80:
        police_bar_color = (130, 180, 255)  # Pale blue
    else:
        police_bar_color = (150, 200, 255)  # Very pale blue
    
    if police_filled > 0:
        # Gradient effect
        for i in range(police_filled):
            fade = 0.7 + (i / bar_width) * 0.3
            color = tuple(int(c * fade) for c in police_bar_color)
            pygame.draw.rect(screen, color, (police_x + i, bar_y_police, 1, bar_height))
        
        # Border around filled portion
        pygame.draw.rect(screen, police_bar_color, (police_x, bar_y_police, police_filled, bar_height), 2, border_radius=12)
    
    # Speed limit marker at 200 km/h
    pygame.draw.line(screen, WHITE, (police_x + bar_width, bar_y_police), (police_x + bar_width, bar_y_police + bar_height), 3)
    limit_text = font_tiny.render("200", True, WHITE)
    screen.blit(limit_text, (police_x + bar_width - 15, bar_y_police + bar_height + 2))
    
    # ========== DISTANCE TO FINISH (TOP RIGHT) ==========
    player_distance_left = max(0, FINISH_LINE_DISTANCE - player.distance)
    distance_text = font_small.render(f"FINISH: {int(player_distance_left)}m", True, WHITE)
    screen.blit(distance_text, (SCREEN_WIDTH - 220, 85))
    
    # Progress bar
    progress = player.distance / FINISH_LINE_DISTANCE
    progress_width = 180
    progress_height = 20
    pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH - 220, 110, progress_width, progress_height), border_radius=10)
    
    # Mark the 1000m preparation zone on progress bar
    prep_zone_marker = int((1000 / FINISH_LINE_DISTANCE) * progress_width)
    if prep_zone_marker < progress_width:
        pygame.draw.line(screen, YELLOW, 
                        (SCREEN_WIDTH - 220 + prep_zone_marker, 110), 
                        (SCREEN_WIDTH - 220 + prep_zone_marker, 110 + progress_height), 3)
    
    filled_progress = int(progress * progress_width)
    if filled_progress > 0:
        # Color code: Yellow in prep zone, green after
        progress_color = YELLOW if player.distance < 1000 else GREEN
        pygame.draw.rect(screen, progress_color, (SCREEN_WIDTH - 220, 110, filled_progress, progress_height), border_radius=10)
    
    # Active power-up indicators (right side, below police speed meter)
    powerup_icon_size = 50
    powerup_y_start = 220  # Moved down to avoid overlap with police speed meter
    powerup_x = SCREEN_WIDTH - 80
    active_powerup_y = powerup_y_start
    
    if freeze_timer > 0:
        # Stagger Slow power-up indicator
        powerup_bg = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(powerup_bg, (100, 200, 255, 200), powerup_bg.get_rect(), border_radius=10)
        screen.blit(powerup_bg, (powerup_x - 10, active_powerup_y - 10))
        
        freeze_font = pygame.font.Font(None, 48)
        freeze_icon = freeze_font.render("🌀", True, WHITE)
        screen.blit(freeze_icon, (powerup_x, active_powerup_y))
        
        # Timer bar
        timer_width = 60
        timer_progress = (freeze_timer / 150) * timer_width  # Updated to 2.5 seconds
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
        timer_progress = (boost_timer / 120) * timer_width  # Updated to 2 seconds
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
        # Ghost power-up indicator (now a counter, not a timer)
        powerup_bg = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(powerup_bg, (200, 150, 255, 200), powerup_bg.get_rect(), border_radius=10)
        screen.blit(powerup_bg, (powerup_x - 10, active_powerup_y - 10))
        
        ghost_font = pygame.font.Font(None, 48)
        ghost_icon = ghost_font.render("👻", True, WHITE)
        screen.blit(ghost_icon, (powerup_x, active_powerup_y))
        
        # Show "1 USE" text instead of timer bar
        use_font = pygame.font.Font(None, 20)
        use_text = use_font.render("1 USE", True, WHITE)
        screen.blit(use_text, (powerup_x - 5, active_powerup_y + 55))
        
        active_powerup_y += 80
    
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
    
    # Stagger Slow effect notification
    if freeze_timer > 0:
        freeze_notif_font = pygame.font.Font(None, 32)
        freeze_notif = freeze_notif_font.render("🌀 POLICE STAGGERED!", True, (100, 200, 255))
        screen.blit(freeze_notif, (SCREEN_WIDTH // 2 - 120, 220))
    
    # EMP Stagger Slow effect notification
    if emp_timer > 0:
        emp_notif_font = pygame.font.Font(None, 32)
        emp_notif = emp_notif_font.render("💫 THIEF STAGGERED!", True, (255, 100, 255))
        screen.blit(emp_notif, (SCREEN_WIDTH // 2 - 120, 250))

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
    
    # Start menu music
    audio_manager.play_menu_music()
    
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
        
        # Press Space to Start button inside panel
        start_button_y = info_y + 5
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
    
    # Initialize A* pathfinders with different heuristics
    # Thief uses Manhattan distance (L1 norm) - better for structured lane-based movement
    thief_astar = AStarPathfinder(heuristic_type='manhattan')
    
    # Police uses Euclidean distance (L2 norm) - better for direct pursuit
    police_astar = AStarPathfinder(heuristic_type='euclidean')
    
    # Initialize Minimax solver for adversarial decision making
    minimax_solver = MinimaxDecisionMaker()
    
    # Initialize Fuzzy Logic controller for human-like behavior
    fuzzy_controller = FuzzyLogicController()
    
    while True:
        if not show_start_screen(screen):
            break
        
        # Initialize game objects
        player = Vehicle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150, RED, is_player=True)
        police = Vehicle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 300, BLUE, is_police=True)
        
        # Set initial distances - Balanced starting positions
        player.distance = 0
        police.distance = -450  # Police starts 450m behind (9% of track - balanced for 50km race)
        
        # COMPETITIVE MODE: Traffic starts AFTER 1000m for preparation time!
        traffic_cars = []
        for i in range(50):  # 50 obstacle cars
            lane = random.randint(0, 2)
            # Obstacles start appearing AFTER 1000m (preparation zone)
            distance = random.randint(1000, FINISH_LINE_DISTANCE - 500)
            traffic_cars.append(TrafficCar(lane, distance))
        
        # Spawn power-ups along the track - Balanced for strategic gameplay
        powerups = []
        
        # Thief power-ups (defensive theme) - Strategic placement
        thief_power_types = ['freeze', 'boost', 'shield', 'ghost']
        for i in range(12):  # 12 thief power-ups across 50km (every ~4km)
            lane = random.randint(0, 2)
            # Spread them evenly across the track
            distance = random.randint(2000 + i * 4000, 2000 + (i + 1) * 4000)
            power_type = random.choice(thief_power_types)
            powerups.append(PowerUp(lane, distance, power_type, for_police=False))
        
        # Police power-ups (offensive theme) - Strategic placement
        police_power_types = ['spike', 'emp', 'turbo', 'roadblock', 'magnet']
        for i in range(12):  # 12 police power-ups across 50km (every ~4km)
            lane = random.randint(0, 2)
            # Spread them evenly across the track (offset from thief powerups)
            distance = random.randint(3000 + i * 4000, 3000 + (i + 1) * 4000)
            power_type = random.choice(police_power_types)
            powerups.append(PowerUp(lane, distance, power_type, for_police=True))
        
        camera_offset = 0
        game_over = False
        winner = None
        
        # Start game audio layers
        audio_manager.play_game_music()
        audio_manager.start_engine_layers()
        audio_manager.start_traffic_ambient()
        
        # Thief power-up timers
        freeze_timer = 0  # Stagger Slow on police (40% speed reduction)
        boost_timer = 0
        shield_timer = 0
        ghost_timer = 0
        
        # Police power-up timers
        spike_timer = 0
        emp_timer = 0  # Stagger Slow on thief (30% speed reduction + steering difficulty)
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
            # Ghost mode is now a counter (1 = has forgiveness, 0 = none)
            # Don't count down automatically - only consumed on collision
            if ghost_timer > 0:
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
            
            # Thief AI controls with INDEPENDENT speed management
            # Apply boost effect to thief's base speed
            speed_multiplier = 1.5 if boost_timer > 0 else 1.0
            
            # EMP effect slows down thief (30% speed reduction)
            if emp_timer > 0:
                speed_multiplier *= 0.7  # 30% speed reduction instead of 50%
            
            # Apply multiplier to thief's BASE speed (8.0)
            player.max_speed = player.base_max_speed * speed_multiplier
            
            # ===== STEP 2: PRIORITY DECISION HIERARCHY =====
            # INTELLIGENT BLENDING of Fuzzy Logic, Minimax, and A* algorithms
            # NO MORE HARD SWITCHING - smooth transitions based on situation priority
            # Safety layer (STEP 1) runs first, then hierarchy blends algorithms
            player.priority_decision_hierarchy(
                traffic_cars=traffic_cars,
                powerups=powerups,
                opponent=police,
                ghost_mode=(ghost_timer > 0),
                fuzzy_controller=fuzzy_controller,
                minimax_solver=minimax_solver,
                astar_pathfinder=thief_astar
            )
            
            # Apply EMP steering difficulty (Stagger Slow effect)
            if emp_timer > 0 and not player.crashed:
                # Add random steering jitter to make control harder
                if random.random() < 0.3:  # 30% chance each frame
                    jitter_amount = random.randint(-3, 3)
                    player.x = max(ROAD_X + 35, min(ROAD_X + ROAD_WIDTH - 35, player.x + jitter_amount))
            
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
            
            # Check for sharp steering (skid sound)
            player.check_sharp_steering()
            
            # Update dynamic audio based on gameplay
            audio_manager.update_engine_sound(player.speed, player.ABSOLUTE_MAX_SPEED)
            police_distance = abs(police.distance - player.distance)
            audio_manager.update_police_siren(police_distance)
            
            # Check power-up collisions for THIEF
            player_screen_y = SCREEN_HEIGHT // 2
            for powerup in powerups:
                # Thief can only collect thief powerups
                if not powerup.for_police and powerup.check_collision(player.x, player_screen_y, player.width, player.height, camera_offset):
                    powerups_collected += 1
                    
                    # Play powerup sound
                    audio_manager.play_powerup()
                    
                    # Apply thief power-up effect
                    if powerup.power_type == 'freeze':
                        freeze_timer = 150  # 2.5 seconds at 60 FPS (Stagger Slow - 40% speed reduction)
                        # Create stagger particle effect
                        for _ in range(30):
                            particles.append(Particle(
                                police.x + random.randint(-30, 30),
                                SCREEN_HEIGHT // 2 + random.randint(-30, 30),
                                (100, 200, 255)
                            ))
                    elif powerup.power_type == 'boost':
                        boost_timer = 120  # 2 seconds (reduced from 4 for tactical use)
                        audio_manager.play_boost()  # Play boost sound
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
                        ghost_timer = 1  # Ghost now provides 1 collision forgiveness (not a duration)
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
                        emp_timer = 150  # 2.5 seconds - Stagger Slow (30% speed reduction + steering difficulty)
                        for _ in range(30):
                            particles.append(Particle(
                                player.x + random.randint(-40, 40),
                                SCREEN_HEIGHT // 2 + random.randint(-40, 40),
                                (255, 100, 255)
                            ))
                    elif powerup.power_type == 'turbo':
                        turbo_timer = 120  # 2 seconds - police speed boost (reduced from 5 for tactical use)
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
            
            # Police AI using intelligent hybrid system with INDEPENDENT speed - affected by Stagger Slow power-up
            if not police.crashed:
                # Apply turbo boost to police's BASE speed (8.5)
                turbo_multiplier = 1.5 if turbo_timer > 0 else 1.0
                
                # Apply Stagger Slow effect (40% speed reduction)
                stagger_multiplier = 0.6 if freeze_timer > 0 else 1.0  # 40% reduction
                
                # Combine both multipliers
                police.max_speed = police.base_max_speed * turbo_multiplier * stagger_multiplier
                
                # ===== STEP 2: PRIORITY DECISION HIERARCHY =====
                # INTELLIGENT BLENDING of Fuzzy Logic, Minimax, and A* algorithms
                # NO MORE HARD SWITCHING - smooth transitions based on situation priority
                # Safety layer (STEP 1) runs first, then hierarchy blends algorithms
                police.priority_decision_hierarchy(
                    traffic_cars=traffic_cars,
                    powerups=powerups,
                    opponent=player,
                    ghost_mode=False,  # Police doesn't have ghost mode
                    fuzzy_controller=fuzzy_controller,
                    minimax_solver=minimax_solver,
                    astar_pathfinder=police_astar
                )
            
            # Apply magnet effect - pull thief toward police with distance-based scaling
            if magnet_timer > 0 and not player.crashed:
                # Calculate distance between police and thief
                distance_apart = abs(police.distance - player.distance)
                
                # Magnet strength scales with distance: strong when close, weak when far
                # Formula: pull_force = clamp((350 - distance) / 350, 0, 1)
                max_magnet_range = 350
                if distance_apart < max_magnet_range:
                    # Calculate normalized pull force (0.0 to 1.0)
                    pull_force = max(0.0, min(1.0, (max_magnet_range - distance_apart) / max_magnet_range))
                    
                    # Base pull strength varies from 0.5 to 4.0 based on distance
                    pull_strength = 0.5 + (pull_force * 3.5)
                    
                    # Gradually pull thief toward police's x position
                    if abs(police.x - player.x) > 10:
                        if police.x < player.x:
                            player.x = max(ROAD_X + 35, player.x - pull_strength)
                        else:
                            player.x = min(ROAD_X + ROAD_WIDTH - 35, player.x + pull_strength)
                # If distance > 350, no magnet effect (too far)
            
            # Apply spike effect - slow down thief
            if spike_timer > 0 and not player.crashed:
                player.speed = max(player.speed - 0.1, player.max_speed * 0.6)
            
            police.distance += police.speed
            police.update_crash()  # Update crash state
            
            # Add police exhaust (with stagger slow effect)
            if freeze_timer > 0:
                # Staggered police - show disorientation particles
                if random.random() < 0.3:
                    police_screen_y = police.distance - camera_offset + SCREEN_HEIGHT // 2
                    particles.append(Particle(
                        police.x + random.randint(-20, 20),
                        police_screen_y + random.randint(-20, 20),
                        (100, 200, 255)
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
                        audio_manager.play_crash()  # Crash sound
                        for _ in range(20):
                            particles.append(Particle(
                                player.x + random.randint(-30, 30),
                                SCREEN_HEIGHT // 2 + random.randint(-30, 30),
                                random.choice([RED, ORANGE, YELLOW])
                            ))
            
            # Check collisions with traffic cars
            for car in traffic_cars:
                # Check player collision with traffic
                if not player.crashed:
                    player_dist = math.sqrt((player.x - car.x)**2 + (player.distance - car.distance)**2)
                    if player_dist < 55:  # Collision threshold
                        # Ghost mode forgives 1 collision
                        if ghost_timer > 0:
                            ghost_timer = 0  # Consume ghost forgiveness
                            # Create ghost effect particles
                            for _ in range(20):
                                particles.append(Particle(
                                    player.x + random.randint(-30, 30),
                                    SCREEN_HEIGHT // 2 + random.randint(-30, 30),
                                    (200, 150, 255)
                                ))
                        # Shield protects from crashes
                        elif shield_timer > 0:
                            # Shield absorbed the hit - create shield spark effect
                            for _ in range(10):
                                particles.append(Particle(
                                    player.x + random.randint(-25, 25),
                                    SCREEN_HEIGHT // 2 + random.randint(-25, 25),
                                    (150, 255, 150)
                                ))
                        else:
                            # No protection - crash!
                            player.crash()
                            audio_manager.play_crash()  # Crash sound
                            # Create crash effect particles
                            for _ in range(15):
                                particles.append(Particle(
                                    player.x + random.randint(-25, 25),
                                    SCREEN_HEIGHT // 2 + random.randint(-25, 25),
                                    random.choice([ORANGE, YELLOW, RED])
                                ))
                
                # Check police collision with traffic
                if not police.crashed:
                    police_dist = math.sqrt((police.x - car.x)**2 + (police.distance - car.distance)**2)
                    if police_dist < 55:  # Collision threshold
                        police.crash()
                        audio_manager.play_crash()  # Crash sound
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
            
            # COMPETITIVE MODE: Dynamically spawn traffic ONLY after 1000m
            # Remove off-screen traffic and add new ones (maintain 50 cars)
            traffic_cars = [car for car in traffic_cars if car.distance > -500]
            while len(traffic_cars) < 50:  # Maintain 50 cars
                lane = random.randint(0, 2)
                distance = player.distance + random.randint(1000, 2000)
                # Only spawn if beyond 1000m mark AND before finish line
                if distance >= 1000 and distance < FINISH_LINE_DISTANCE:
                    traffic_cars.append(TrafficCar(lane, distance))
                else:
                    break
            
            # Camera follows player
            camera_offset = player.distance
            
            # IMPROVED: Check collision with police - catch when at same position
            distance_diff = abs(player.distance - police.distance)
            lateral_diff = abs(player.x - police.x)
            
            # Catch conditions: Police reached thief's position
            if distance_diff < 80 and lateral_diff < 100:
                # Police caught the thief!
                game_over = True
                winner = "police"
                audio_manager.stop_all_sounds()
                audio_manager.play_lose_music()
            
            # CRITICAL: Prevent police from overtaking without catching
            # If police is ahead or equal to thief, game should end
            if police.distance >= player.distance - 20:
                # Police has reached/overtaken thief - this counts as caught
                game_over = True
                winner = "police"
                audio_manager.stop_all_sounds()
                audio_manager.play_lose_music()
            
            # Check if player reached finish
            if player.distance >= FINISH_LINE_DISTANCE:
                game_over = True
                winner = "thief"
                audio_manager.stop_all_sounds()
                audio_manager.play_win_music()
            
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
            
            # Draw roadblock with warning indicator
            if roadblock_timer > 0 and roadblock_lane >= 0:
                roadblock_x = ROAD_X + roadblock_lane * LANE_WIDTH + LANE_WIDTH // 2
                roadblock_distance = player.distance + 300
                roadblock_screen_y = SCREEN_HEIGHT // 2 - (roadblock_distance - camera_offset)
                
                # Warning phase: 0.7 seconds = 42 frames (show warning if timer > 378)
                WARNING_THRESHOLD = 420 - 42  # Show warning for first 42 frames
                
                if roadblock_timer > WARNING_THRESHOLD:
                    # Draw warning indicator (flashing)
                    if (roadblock_timer // 5) % 2 == 0:  # Flash effect
                        # Warning triangle above roadblock position
                        warning_size = 40
                        warning_y = roadblock_screen_y - 100
                        
                        # Yellow warning triangle
                        pygame.draw.polygon(screen, YELLOW, [
                            (roadblock_x, warning_y - warning_size // 2),
                            (roadblock_x - warning_size // 2, warning_y + warning_size // 2),
                            (roadblock_x + warning_size // 2, warning_y + warning_size // 2)
                        ])
                        pygame.draw.polygon(screen, ORANGE, [
                            (roadblock_x, warning_y - warning_size // 2),
                            (roadblock_x - warning_size // 2, warning_y + warning_size // 2),
                            (roadblock_x + warning_size // 2, warning_y + warning_size // 2)
                        ], 3)
                        
                        # Exclamation mark
                        warning_font = pygame.font.Font(None, 32)
                        warning_text = warning_font.render("!", True, BLACK)
                        screen.blit(warning_text, (roadblock_x - 6, warning_y - 10))
                else:
                    # Draw actual roadblock
                    if -100 < roadblock_screen_y < SCREEN_HEIGHT + 100:
                        # Red barrier
                        barrier_width = LANE_WIDTH - 40
                        barrier_height = 80
                        pygame.draw.rect(screen, RED, 
                                       (roadblock_x - barrier_width // 2, roadblock_screen_y - barrier_height // 2,
                                        barrier_width, barrier_height), border_radius=10)
                        pygame.draw.rect(screen, (255, 150, 150), 
                                       (roadblock_x - barrier_width // 2, roadblock_screen_y - barrier_height // 2,
                                        barrier_width, barrier_height), 3, border_radius=10)
                        
                        # Roadblock icon
                        roadblock_font = pygame.font.Font(None, 48)
                        roadblock_icon = roadblock_font.render("🚧", True, WHITE)
                        screen.blit(roadblock_icon, (roadblock_x - 20, roadblock_screen_y - 20))
            
            # Police and player
            police.draw(screen, camera_offset)
            player.draw(screen, camera_offset)
            
            # HUD (drawn last to be on top)
            draw_hud(screen, player, police, traffic_cars, freeze_timer, boost_timer, shield_timer, ghost_timer, emp_timer, powerups_collected)
            
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