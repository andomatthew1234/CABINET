import os
import sys
import json
import importlib
import pygame
import random
import math
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog

# --- GUARANTEED ABSOLUTE PATH FIX ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Pygame, Mixer, and Joystick
pygame.init()
pygame.mixer.init()
pygame.joystick.init()

# Detect and initialize gamepads
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for joy in joysticks:
    joy.init()

# Window Setup (Now dynamic and resizable)
WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("🕹️ THE CABINET")
clock = pygame.time.Clock()

# Colors
BG_COLOR = (15, 15, 25)
CARD_BG = (25, 25, 40)
CARD_SELECTED = (40, 40, 70)
TEXT_MAIN = (255, 255, 255)
TEXT_MUTED = (150, 150, 180)
NEON_CYAN = (0, 240, 255)
NEON_PINK = (255, 0, 127)
NEON_GREEN = (0, 255, 100)

# Fonts
FONT_BEAST = pygame.font.SysFont("Courier New", 65, bold=True, italic=True)
FONT_SUB = pygame.font.SysFont("Arial", 20, bold=True)
FONT_BODY = pygame.font.SysFont("Arial", 18)
FONT_BTN = pygame.font.SysFont("Courier New", 16, bold=True)

# Audio Configuration
TRACK_ALIASES = {
    "launch.mp3": "Launch sound effect",
    "matrix.mp3": "TheMatrix",
    "menu.mp3": "Main theme - THE CABINET",
    "pong.mp3": "Main theme - PONG",
    "racing.mp3": "BassDrop",
    "snake.mp3": "ssss",
    "tetris.mp3": "BlockClassico",
    "water_sort.mp3": "BouncyWaterSort"
}

def play_sound(filename, loop=0, volume=1.0):
    try:
        path = os.path.join(ROOT_DIR, 'music', filename)
        if os.path.exists(path):
            if loop == -1:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
            else:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(volume)
                sound.play()
    except Exception as e:
        print(f"Audio error for {filename}: {e}")

class ArcadeLauncher:
    def __init__(self):
        self.animation_ticks = 0
        self.master_volume = 0.5
        
        self.games = []
        self.selected_index = 0
        self.view_state = "GAMES" 
        self.tracks = self.load_tracks()
        
        # Smooth Scrolling & Touch State
        self.scroll_y = 0
        self.target_scroll_y = 0
        self.scroll_velocity = 0
        self.is_dragging = False
        self.is_dragging_volume = False 
        self.drag_start_y = 0
        self.last_mouse_y = 0
        self.drag_accumulated = 0 
        self.input_mode = "INDEXED" 

        # --- INSTANT BOOT SPLASH SCREEN ---
        self.load_games(show_splash=True)

        # Start background loop music only AFTER the splash boot sequence is done
        self.active_track = "menu.mp3"
        self.is_playing = True
        play_sound("menu.mp3", loop=-1, volume=self.master_volume)

    def draw_splash(self, progress, task_text):
        """Renders the modernized, clean boot sequence."""
        screen.fill((20, 20, 25))

        # Title Rendering
        title_str = "THE CABINET"
        title_main = FONT_BEAST.render(title_str, True, (255, 255, 255))
        pulse = abs(math.sin(self.animation_ticks * 0.05)) * 100
        title_main.set_alpha(155 + int(pulse))
        screen.blit(title_main, (WIDTH//2 - title_main.get_width()//2, HEIGHT//2 - 80))

        os_txt = FONT_SUB.render("LAUNCHER INITIALIZING...", True, NEON_CYAN)
        screen.blit(os_txt, (WIDTH//2 - os_txt.get_width()//2, HEIGHT//2 - 10))

        # Task Text Console Output
        task_surf = FONT_BODY.render(task_text, True, TEXT_MUTED)
        screen.blit(task_surf, (WIDTH//2 - task_surf.get_width()//2, HEIGHT - 100))

        # Progress Bar (Clean & Sleek)
        bar_w = min(600, WIDTH - 100)
        bar_h = 6
        bar_x = WIDTH//2 - bar_w//2
        bar_y = HEIGHT - 70

        pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        filled_w = int(bar_w * progress)
        pygame.draw.rect(screen, NEON_CYAN, (bar_x, bar_y, filled_w, bar_h), border_radius=3)

    def _load_single_game(self, folder, games_dir):
        """Processes exactly one game directory. Used to unblock the main thread."""
        folder_path = os.path.join(games_dir, folder)
        config_path = os.path.join(folder_path, 'config.json')
        game_script = os.path.join(folder_path, 'game.py')
        
        if os.path.isdir(folder_path) and os.path.exists(config_path) and os.path.exists(game_script):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                effect_func = None
                effect_script = os.path.join(folder_path, 'effect.py')
                if os.path.exists(effect_script):
                    module_name = f"games.{folder}.effect"
                    if module_name in sys.modules:
                        effect_module = importlib.reload(sys.modules[module_name])
                    else:
                        effect_module = importlib.import_module(module_name)
                    if hasattr(effect_module, 'draw_effect'):
                        effect_func = effect_module.draw_effect
                        
                self.games.append({
                    "id": folder.lower(),
                    "title": config.get("title", folder.upper()),
                    "description": config.get("description", "No description provided."),
                    "high_score": config.get("high_score", 0),
                    "config_path": config_path,
                    "effect_func": effect_func
                })
            except Exception as e:
                print(f"Error loading game '{folder}': {e}")

    def load_games(self, show_splash=False):
        self.games = []
        games_dir = os.path.join(ROOT_DIR, 'games')
        
        folders = []
        if os.path.exists(games_dir):
            folders = [f for f in os.listdir(games_dir) if os.path.isdir(os.path.join(games_dir, f))]

        if show_splash:
            min_splash_frames = 180 # 3 seconds at 60 FPS
            total_frames = max(min_splash_frames, len(folders))
            play_sound("launch.mp3", volume=self.master_volume) 
            
            for i in range(total_frames):
                self.animation_ticks += 1
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    elif event.type == pygame.VIDEORESIZE:
                        global WIDTH, HEIGHT
                        WIDTH, HEIGHT = event.w, event.h
                        pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

                # Process loading queue with cleaner language
                current_task = "Loading framework components..."
                if i < len(folders):
                    current_task = f"Mounting game: {folders[i].title()}"
                    self._load_single_game(folders[i], games_dir)
                elif i >= len(folders):
                    current_task = "Verifying assets..."
                if i >= total_frames - 10:
                    current_task = "Ready."

                self.draw_splash(i / total_frames, current_task)
                pygame.display.flip()
                clock.tick(60)
        else:
            for folder in folders:
                self._load_single_game(folder, games_dir)

    def load_tracks(self):
        tracks = []
        music_dir = os.path.join(ROOT_DIR, 'music')
        if not os.path.exists(music_dir): return tracks
        
        for file in sorted(os.listdir(music_dir)):
            if file.endswith('.mp3') and file != "exit.mp3":
                display_name = TRACK_ALIASES.get(file, file)
                tracks.append({"file": file, "name": display_name})
        return tracks

    def download_track(self, filename):
        src = os.path.join(ROOT_DIR, 'music', filename)
        if not os.path.exists(src): return
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        dst = filedialog.asksaveasfilename(defaultextension=".mp3", initialfile=filename, title="Download Track")
        if dst:
            try:
                shutil.copy(src, dst)
            except Exception as e:
                print(f"Download failed: {e}")
        root.destroy()

    def transition_out_and_launch(self, game_id):
        pygame.mixer.music.fadeout(800)
        play_sound("launch.mp3", volume=self.master_volume)
        
        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill((0, 0, 0))
        
        frames = 45 
        for i in range(frames):
            self.draw()
            alpha = int((i / frames) * 255)
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            clock.tick(60)
            
        pygame.time.wait(200) 
        
        if game_id == "update":
            pygame.quit()
            update_script = os.path.join(ROOT_DIR, 'other', 'update.py')
            subprocess.Popen([sys.executable, update_script], cwd=ROOT_DIR)
            sys.exit()
        else:
            self.launch_game(game_id)

    def transition_out_and_quit(self):
        pygame.mixer.music.fadeout(800)
        play_sound("exit.mp3", volume=self.master_volume)
        
        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill((0, 0, 0))
        
        frames = 45 
        for i in range(frames):
            self.draw()
            alpha = int((i / frames) * 255)
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            clock.tick(60)
            
        pygame.time.wait(200)
        pygame.quit()
        sys.exit()

    def launch_game(self, game_id):
        global screen
        try:
            module_name = f"games.{game_id}.game"
            if module_name in sys.modules:
                game_module = importlib.reload(sys.modules[module_name])
            else:
                game_module = importlib.import_module(module_name)
            game_module.main(screen)
        except Exception as e:
            print(f"Failed to run game {game_id}: {e}")
        
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("🕹️ THE CABINET")
        
        pygame.joystick.quit()
        pygame.joystick.init()
        global joysticks
        joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joy in joysticks: joy.init()
        
        self.load_games(show_splash=False) 
        play_sound(self.active_track, loop=-1, volume=self.master_volume)
        if not self.is_playing:
            pygame.mixer.music.pause()

    def draw_special_effects(self, game_identifier, rect):
        self.animation_ticks += 1
        t = self.animation_ticks

        if "pong" in game_identifier:
            pass 
        elif "ast" in game_identifier or "asteroid" in game_identifier:
            screen.set_clip(rect)
            ship1_y = rect.centery + math.sin(t * 0.05) * 20
            ship2_y = rect.centery + math.cos(t * 0.07) * 20
            
            pygame.draw.polygon(screen, NEON_CYAN, [(rect.left + 15, ship1_y - 8), (rect.left + 35, ship1_y), (rect.left + 15, ship1_y + 8)])
            pygame.draw.polygon(screen, NEON_PINK, [(rect.right - 15, ship2_y - 8), (rect.right - 35, ship2_y), (rect.right - 15, ship2_y + 8)])
            
            bullet_speed = 8
            b1_x = rect.left + 35 + ((t * bullet_speed) % (rect.width - 50))
            pygame.draw.line(screen, NEON_GREEN, (b1_x, ship1_y), (b1_x + 10, ship1_y), 2)
            
            b2_x = rect.right - 35 - (((t + 20) * (bullet_speed + 1)) % (rect.width - 50))
            pygame.draw.line(screen, (255, 200, 0), (b2_x, ship2_y), (b2_x - 10, ship2_y), 2)
            screen.set_clip(None)

        elif "racer" in game_identifier or "neon" in game_identifier or "racing" in game_identifier:
            screen.set_clip(rect)
            road_w = 50
            road_x = rect.right - road_w - 20
            
            speed = 6
            dash_len = 15
            cycle = dash_len + 15
            offset = (t * speed) % cycle
            center_line_x = road_x + (road_w // 2)
            
            for y in range(rect.top - cycle, rect.bottom, cycle):
                pygame.draw.rect(screen, (255, 255, 255), (center_line_x - 1, y + offset, 2, dash_len))
                
            car_w, car_h = 16, 28
            car_x = center_line_x - (car_w // 2)
            car_y = rect.top + (rect.height // 2) + 5
            
            light_surf = pygame.Surface((car_w + 40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(light_surf, (255, 255, 150, 60), [(20 + 2, 40), (0, 0), (15, 0)])
            pygame.draw.polygon(light_surf, (255, 255, 150, 60), [(20 + car_w - 2, 40), (25 + car_w, 0), (40 + car_w, 0)])
            screen.blit(light_surf, (car_x - 20, car_y - 40))
            
            pygame.draw.rect(screen, (200, 30, 60), (car_x, car_y, car_w, car_h), border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), (car_x + 2, car_y - 2, 4, 3))
            pygame.draw.rect(screen, (255, 255, 255), (car_x + car_w - 6, car_y - 2, 4, 3))
            pygame.draw.rect(screen, (255, 0, 0), (car_x + 2, car_y + car_h - 2, 4, 3))
            pygame.draw.rect(screen, (255, 0, 0), (car_x + car_w - 6, car_y + car_h - 2, 4, 3))
            screen.set_clip(None)

        elif "fighter" in game_identifier or "street" in game_identifier:
            loop_t = t % 60
            progress = loop_t / 30.0 
            
            if progress <= 1.0:
                p1_x = rect.left + (rect.w * progress)
                pygame.draw.circle(screen, (0, 200, 255), (int(p1_x), rect.top), 6)
                pygame.draw.circle(screen, (255, 255, 255), (int(p1_x), rect.top), 3)
                
                p2_x = rect.right - (rect.w * progress)
                pygame.draw.circle(screen, (255, 100, 0), (int(p2_x), rect.bottom), 6)
                pygame.draw.circle(screen, (255, 255, 255), (int(p2_x), rect.bottom), 3)
            else:
                explosion_rad = int(max(0, (2.0 - progress) * 15))
                if explosion_rad > 0:
                    pygame.draw.circle(screen, (255, 255, 255), (rect.right, rect.top), explosion_rad)
                    pygame.draw.circle(screen, (255, 200, 0), (rect.right, rect.top), int(explosion_rad * 0.7))
                    pygame.draw.circle(screen, (255, 255, 255), (rect.left, rect.bottom), explosion_rad)
                    pygame.draw.circle(screen, (255, 200, 0), (rect.left, rect.bottom), int(explosion_rad * 0.7))

        elif "snake" in game_identifier:
            perimeter = (rect.w * 2) + (rect.h * 2)
            s_pos = (t * 4) % perimeter
            def get_perimeter_pt(p):
                if p < rect.w: return rect.x + p, rect.y
                p -= rect.w
                if p < rect.h: return rect.right, rect.y + p
                p -= rect.h
                if p < rect.w: return rect.right - p, rect.bottom
                p -= rect.w
                return rect.x, rect.bottom - p
            for seg in range(4):
                pt = get_perimeter_pt((s_pos - (seg * 12)) % perimeter)
                pygame.draw.rect(screen, (0, 255, 100), (pt[0] - 4, pt[1] - 4, 8, 8), border_radius=2)

        elif "water" in game_identifier or "sort" in game_identifier:
            for thick in range(3, 0, -1):
                hue = (t * 3 + thick * 20) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 100, 100, 100)
                pygame.draw.rect(screen, color, rect.inflate(thick * 2, thick * 2), width=1, border_radius=8 + thick)

    def draw_top_nav(self, mx, my):
        t = self.animation_ticks
        title_str = "THE CABINET"
        
        pulse = math.sin(t * 0.05) * 4
        float_y = math.sin(t * 0.08) * 5
        
        title_red = FONT_BEAST.render(title_str, True, (255, 0, 50))
        title_blue = FONT_BEAST.render(title_str, True, (0, 200, 255))
        title_main = FONT_BEAST.render(title_str, True, (255, 255, 255))
        
        base_x = WIDTH // 2 - title_main.get_width() // 2
        base_y = 20 + float_y
        
        screen.blit(title_red, (base_x - 3 + pulse, base_y))
        screen.blit(title_blue, (base_x + 3 - pulse, base_y))
        screen.blit(title_main, (base_x, base_y))
        
        subtitle_txt = "Select a game using D-PAD/ARROWS and hit A/ENTER to play" if self.view_state == "GAMES" else "Audio Operations Center (Spacebar to Play/Pause)"
        subtitle = FONT_BODY.render(subtitle_txt, True, NEON_PINK)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 105))
        
        pygame.draw.line(screen, NEON_PINK, (50, 140), (WIDTH - 50, 140), 2)
        pygame.draw.line(screen, NEON_CYAN, (50, HEIGHT - 70), (WIDTH - 50, HEIGHT - 70), 2)

    def draw_bottom_nav(self, mx, my):
        btn_w, btn_h = 220, 36
        
        update_rect = pygame.Rect(WIDTH // 2 - btn_w - 10, HEIGHT - 52, btn_w, btn_h)
        u_hover = update_rect.collidepoint(mx, my)
        if u_hover: update_rect.inflate_ip(14, 6)
        
        pygame.draw.rect(screen, (20, 20, 35) if not u_hover else (10, 40, 30), update_rect, border_radius=6)
        pygame.draw.rect(screen, NEON_CYAN if not u_hover else NEON_GREEN, update_rect, width=2, border_radius=6)
        
        u_txt = FONT_BTN.render("[ SYSTEM UPDATE ]", True, NEON_CYAN if not u_hover else TEXT_MAIN)
        screen.blit(u_txt, (update_rect.centerx - u_txt.get_width()//2, update_rect.centery - u_txt.get_height()//2))

        tracks_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT - 52, btn_w, btn_h)
        t_hover = tracks_rect.collidepoint(mx, my)
        if t_hover: tracks_rect.inflate_ip(14, 6)
        
        pygame.draw.rect(screen, (20, 20, 35) if not t_hover else (40, 10, 30), tracks_rect, border_radius=6)
        pygame.draw.rect(screen, NEON_PINK if not t_hover else TEXT_MAIN, tracks_rect, width=2, border_radius=6)
        
        t_label = "[ 🎧 TRACKS ]" if self.view_state == "GAMES" else "[ 🕹️ GAMES ]"
        t_txt = FONT_BTN.render(t_label, True, NEON_PINK if not t_hover else TEXT_MAIN)
        screen.blit(t_txt, (tracks_rect.centerx - t_txt.get_width()//2, tracks_rect.centery - t_txt.get_height()//2))
        
        return update_rect, tracks_rect

    def draw_games(self, mx, my):
        if not self.games:
            no_games = FONT_SUB.render("No games found in /games/ folder!", True, NEON_PINK)
            screen.blit(no_games, (WIDTH // 2 - no_games.get_width() // 2, 300))
            return

        base_start_y = 165
        card_height = 90
        gap = 15
        
        # Calculate dynamic bounds for scrolling based on current window height
        visible_h = max(0, (HEIGHT - 75) - base_start_y)
        content_h = len(self.games) * (card_height + gap)
        
        if self.input_mode == "INDEXED":
            self.target_scroll_y = -max(0, (self.selected_index * (card_height + gap)) - (visible_h // 2) + (card_height // 2))
            self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.15 
        else:
            self.scroll_y += self.scroll_velocity
            self.scroll_velocity *= 0.85 
            
        max_scroll = min(0, visible_h - content_h)
        if self.scroll_y > 0: self.scroll_y = 0
        if self.scroll_y < max_scroll: self.scroll_y = max_scroll

        for i, game in enumerate(self.games):
            y_pos = base_start_y + i * (card_height + gap) + self.scroll_y
            mouse_hover = pygame.Rect(50, y_pos, WIDTH - 100, card_height).collidepoint(mx, my)
            
            is_focused = (i == self.selected_index) if self.input_mode == "INDEXED" else mouse_hover
            
            game_identifier = (game["id"] + " " + game["title"]).lower()
            current_w, current_h = WIDTH - 100, card_height
            current_x, current_y = 50, y_pos

            if is_focused:
                current_w += 20; current_h += 10
                current_x -= 10; current_y -= 5

                if "tetris" in game_identifier: current_x += math.sin(self.animation_ticks * 0.1) * 12
                if "pong" in game_identifier: current_x += random.randint(-3, 3); current_y += random.randint(-3, 3)
                if "fighter" in game_identifier or "street" in game_identifier or "ast" in game_identifier:
                    current_x += random.randint(-2, 2); current_y += random.randint(-2, 2)

            card_rect = pygame.Rect(current_x, current_y, current_w, current_h)
            if card_rect.bottom < 145 or card_rect.top > HEIGHT - 75: continue

            if is_focused and ("racer" in game_identifier or "neon" in game_identifier or "racing" in game_identifier or "ast" in game_identifier):
                bg_color = (8, 8, 12) 
            else:
                bg_color = CARD_SELECTED if is_focused else CARD_BG

            pygame.draw.rect(screen, bg_color, card_rect, border_radius=8)
            
            if is_focused:
                pygame.draw.rect(screen, NEON_CYAN, card_rect, width=2, border_radius=8)
                
                if game.get("effect_func"):
                    try:
                        game["effect_func"](screen, card_rect, self.animation_ticks)
                    except Exception as e:
                        print(f"Effect crash suppressed in {game['id']}: {e}")
                        self.draw_special_effects(game_identifier, card_rect)
                    finally:
                        screen.set_clip(None)
                else:
                    self.draw_special_effects(game_identifier, card_rect)
            
            title_surf = FONT_SUB.render(game["title"], True, NEON_CYAN if is_focused else TEXT_MAIN)
            screen.blit(title_surf, (current_x + 20, current_y + (20 if is_focused else 15)))
            
            desc_surf = FONT_BODY.render(game["description"], True, TEXT_MUTED)
            screen.blit(desc_surf, (current_x + 20, current_y + (50 if is_focused else 45)))
            
            score_surf = FONT_SUB.render(f"HI-SCORE: {game['high_score']}", True, NEON_PINK if is_focused else TEXT_MUTED)
            screen.blit(score_surf, (current_x + current_w - score_surf.get_width() - 30, current_y + (current_h // 2) - (score_surf.get_height() // 2)))

    def draw_tracks(self, mx, my):
        base_start_y = 165
        row_height = 60
        gap = 10
        
        visible_h = max(0, (HEIGHT - 70) - base_start_y)
        content_h = len(self.tracks) * (row_height + gap)
        
        if self.input_mode == "INDEXED":
            self.target_scroll_y = -max(0, (self.selected_index * (row_height + gap)) - (visible_h // 2) + (row_height // 2))
            self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.15 
        else:
            self.scroll_y += self.scroll_velocity
            self.scroll_velocity *= 0.85
            
        max_scroll = min(0, visible_h - content_h)
        if self.scroll_y > 0: self.scroll_y = 0
        if self.scroll_y < max_scroll: self.scroll_y = max_scroll

        for i, track in enumerate(self.tracks):
            y_pos = base_start_y + i * (row_height + gap) + self.scroll_y
            if y_pos > HEIGHT - 70 or y_pos < 140: continue
            
            rect = pygame.Rect(50, y_pos, WIDTH - 100, row_height)
            is_active = (track["file"] == self.active_track)
            
            pygame.draw.rect(screen, CARD_SELECTED if is_active else CARD_BG, rect, border_radius=6)
            if is_active:
                pygame.draw.rect(screen, NEON_PINK, rect, width=2, border_radius=6)

            play_col = NEON_GREEN if is_active and self.is_playing else TEXT_MUTED
            status = "▶" if not (is_active and self.is_playing) else "⏸"
            status_surf = FONT_SUB.render(status, True, play_col)
            screen.blit(status_surf, (70, y_pos + 18))
            
            name_surf = FONT_SUB.render(track["name"], True, TEXT_MAIN if is_active else TEXT_MUTED)
            screen.blit(name_surf, (110, y_pos + 18))
            
            vol_x, vol_w = WIDTH - 350, 150
            vol_rect = pygame.Rect(vol_x, y_pos + 25, vol_w, 10)
            pygame.draw.rect(screen, (30, 30, 45), vol_rect, border_radius=5)
            
            if is_active:
                pygame.draw.rect(screen, NEON_CYAN, (vol_x, y_pos + 25, int(vol_w * self.master_volume), 10), border_radius=5)
                vol_label = FONT_BODY.render("VOL", True, NEON_CYAN)
            else:
                vol_label = FONT_BODY.render("VOL", True, TEXT_MUTED)
            screen.blit(vol_label, (vol_x - 45, y_pos + 18))
            
            dl_rect = pygame.Rect(WIDTH - 150, y_pos + 15, 80, 30)
            dl_hover = dl_rect.collidepoint(mx, my)
            pygame.draw.rect(screen, (50, 50, 70) if not dl_hover else NEON_CYAN, dl_rect, border_radius=4)
            dl_txt = FONT_BODY.render("⬇️ SAVE", True, TEXT_MAIN if not dl_hover else (0,0,0))
            screen.blit(dl_txt, (dl_rect.centerx - dl_txt.get_width()//2, dl_rect.centery - dl_txt.get_height()//2))

    def draw(self):
        screen.fill(BG_COLOR)
        mx, my = pygame.mouse.get_pos()
        
        self.draw_top_nav(mx, my)
        
        if self.view_state == "GAMES":
            self.draw_games(mx, my)
        elif self.view_state == "TRACKS":
            self.draw_tracks(mx, my)
            
        return self.draw_bottom_nav(mx, my)

    def run(self):
        global WIDTH, HEIGHT
        running = True
        while running:
            self.animation_ticks += 1
            update_btn, tracks_btn = self.draw()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.transition_out_and_quit()
                    
                # --- RESIZE SUPPORT ---
                elif event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = event.w, event.h
                    pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                
                # --- GAMEPAD & KEYBOARD INPUT ---
                elif event.type == pygame.KEYDOWN or event.type == pygame.JOYHATMOTION or event.type == pygame.JOYBUTTONDOWN:
                    self.input_mode = "INDEXED"
                    
                    is_up = (event.type == pygame.KEYDOWN and event.key == pygame.K_UP) or (event.type == pygame.JOYHATMOTION and event.value[1] == 1)
                    is_down = (event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN) or (event.type == pygame.JOYHATMOTION and event.value[1] == -1)
                    is_enter = (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN) or (event.type == pygame.JOYBUTTONDOWN and event.button == 0)
                    is_back = (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or (event.type == pygame.JOYBUTTONDOWN and event.button == 1)
                    is_space = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)

                    if is_back:
                        if self.view_state == "TRACKS": self.view_state = "GAMES"; self.selected_index = 0
                        else: self.transition_out_and_quit()

                    if self.view_state == "GAMES" and self.games:
                        if is_up:
                            self.selected_index = (self.selected_index - 1) % len(self.games); play_sound("move.mp3", volume=self.master_volume)
                        elif is_down:
                            self.selected_index = (self.selected_index + 1) % len(self.games); play_sound("move.mp3", volume=self.master_volume)
                        elif is_enter:
                            self.transition_out_and_launch(self.games[self.selected_index]["id"])
                            
                    elif self.view_state == "TRACKS" and self.tracks:
                        if is_up:
                            self.selected_index = (self.selected_index - 1) % len(self.tracks); play_sound("move.mp3", volume=self.master_volume)
                        elif is_down:
                            self.selected_index = (self.selected_index + 1) % len(self.tracks); play_sound("move.mp3", volume=self.master_volume)
                        elif is_enter or is_space:
                            track = self.tracks[self.selected_index]
                            if self.active_track == track["file"]:
                                self.is_playing = not self.is_playing
                                if self.is_playing: pygame.mixer.music.unpause()
                                else: pygame.mixer.music.pause()
                            else:
                                self.active_track = track["file"]
                                self.is_playing = True
                                play_sound(self.active_track, loop=-1, volume=self.master_volume)

                # --- TRACKPAD & MOUSE WHEEL ---
                elif event.type == pygame.MOUSEWHEEL:
                    self.input_mode = "KINETIC"
                    self.scroll_velocity += event.y * 15 # Glides smoothly

                # --- TOUCH / MOUSE CLICK DRAGGING ---
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.input_mode = "KINETIC"
                        
                        hit_volume = False
                        if self.view_state == "TRACKS":
                            for i, track in enumerate(self.tracks):
                                y_pos = 165 + i * 70 + self.scroll_y
                                if y_pos > HEIGHT - 70 or y_pos < 140: continue # Prevent clicking hidden sliders
                                
                                vol_rect = pygame.Rect(WIDTH - 360, y_pos + 5, 170, 50)
                                if vol_rect.collidepoint(event.pos):
                                    self.is_dragging_volume = True
                                    hit_volume = True
                                    self.master_volume = max(0.0, min(1.0, (event.pos[0] - (WIDTH - 350)) / 150.0))
                                    pygame.mixer.music.set_volume(self.master_volume)
                                    break
                                    
                        if not hit_volume:
                            self.is_dragging = True
                            self.drag_start_y = event.pos[1]
                            self.last_mouse_y = event.pos[1]
                            self.drag_accumulated = 0
                            self.scroll_velocity = 0 # Stop current momentum immediately on grab

                elif event.type == pygame.MOUSEMOTION:
                    if getattr(self, 'is_dragging_volume', False):
                        self.master_volume = max(0.0, min(1.0, (event.pos[0] - (WIDTH - 350)) / 150.0))
                        pygame.mixer.music.set_volume(self.master_volume)
                    elif getattr(self, 'is_dragging', False):
                        dy = event.pos[1] - self.last_mouse_y
                        self.scroll_y += dy # Instantly track the cursor for a tighter feel
                        self.scroll_velocity = dy * 0.5 # Leave some momentum upon release
                        self.last_mouse_y = event.pos[1]
                        self.drag_accumulated += abs(dy)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if getattr(self, 'is_dragging_volume', False):
                            self.is_dragging_volume = False
                            continue 
                            
                        self.is_dragging = False
                        mx, my = event.pos
                        
                        # Increased tolerance (15) to prevent accidental drags from blocking clicks
                        if self.drag_accumulated < 15: 
                            if update_btn.collidepoint(mx, my):
                                self.transition_out_and_launch("update")
                            elif tracks_btn.collidepoint(mx, my):
                                self.view_state = "TRACKS" if self.view_state == "GAMES" else "GAMES"
                                self.selected_index = 0
                                self.scroll_y = 0
                                self.scroll_velocity = 0
                            
                            elif self.view_state == "GAMES":
                                for i, game in enumerate(self.games):
                                    y_pos = 165 + i * 105 + self.scroll_y
                                    if y_pos > HEIGHT - 75 or y_pos < 145: continue # Ensure it's fully visible
                                    
                                    rect = pygame.Rect(50, y_pos, WIDTH - 100, 90)
                                    if rect.collidepoint(mx, my):
                                        self.selected_index = i
                                        self.transition_out_and_launch(game["id"])
                                        
                            elif self.view_state == "TRACKS":
                                for i, track in enumerate(self.tracks):
                                    y_pos = 165 + i * 70 + self.scroll_y
                                    if y_pos > HEIGHT - 70 or y_pos < 140: continue # Ensure it's fully visible
                                    
                                    rect = pygame.Rect(50, y_pos, WIDTH - 100, 60)
                                    dl_rect = pygame.Rect(WIDTH - 150, y_pos + 15, 80, 30)
                                    
                                    if dl_rect.collidepoint(mx, my):
                                        self.download_track(track["file"])
                                    elif rect.collidepoint(mx, my):
                                        self.selected_index = i
                                        if self.active_track == track["file"]:
                                            self.is_playing = not self.is_playing
                                            if self.is_playing: pygame.mixer.music.unpause()
                                            else: pygame.mixer.music.pause()
                                        else:
                                            self.active_track = track["file"]
                                            self.is_playing = True
                                            play_sound(self.active_track, loop=-1, volume=self.master_volume)
            
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    launcher = ArcadeLauncher()
    launcher.run()