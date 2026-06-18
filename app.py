import os
import sys
import json
import importlib
import pygame
import random
import math

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init()

# Window Setup
WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🕹️ THE CABINET")
clock = pygame.time.Clock()

# Colors (Cyberpunk / Retro Theme)
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

# Audio Path Helper
def play_sound(filename, loop=0, volume=1.0):
    try:
        path = os.path.join(os.path.dirname(__file__), 'music', filename)
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
        self.games = []
        self.selected_index = 0
        self.load_games()
        
        # Scrolling and Animation Properties
        self.scroll_y = 0
        self.target_scroll_y = 0
        self.animation_ticks = 0
        
        # Neon Racer effect specific elements
        self.racer_cars = [{"lane": i, "y": random.randint(0, 90), "speed": random.uniform(1.5, 3.5), "color": random.choice([(255,0,0), (0,255,0), (255,255,0)])} for i in range(4)]
        
        # Update Button Hover Binary Drops
        self.update_drops = [{"x": random.randint(5, 195), "y": random.randint(-20, 0), "speed": random.uniform(1, 3), "char": random.choice(["0", "1"])} for _ in range(12)]
        
        # Start background menu track
        play_sound("menu.mp3", loop=-1, volume=0.5)

    def load_games(self):
        """Scans the /games/ directory and loads configurations."""
        self.games = []
        games_dir = os.path.join(os.path.dirname(__file__), 'games')
        
        if not os.path.exists(games_dir):
            os.makedirs(games_dir)
            return

        for folder in os.listdir(games_dir):
            folder_path = os.path.join(games_dir, folder)
            config_path = os.path.join(folder_path, 'config.json')
            game_script = os.path.join(folder_path, 'game.py')
            
            if os.path.isdir(folder_path) and os.path.exists(config_path) and os.path.exists(game_script):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    self.games.append({
                        "id": folder.lower(),
                        "title": config.get("title", folder.upper()),
                        "description": config.get("description", "No description provided."),
                        "high_score": config.get("high_score", 0),
                        "config_path": config_path
                    })
                except Exception as e:
                    print(f"Error loading game '{folder}': {e}")

    def transition_out_and_launch(self, game_id):
        """Handles the smooth audio/visual fade out before passing control to the game."""
        pygame.mixer.music.fadeout(800)
        play_sound("launch.mp3")
        
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
        self.launch_game(game_id)

    def transition_out_and_quit(self):
        """Fades out the screen and audio before cleanly exiting the app."""
        pygame.mixer.music.fadeout(800)
        play_sound("exit.mp3")
        
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
        """Dynamically imports and runs the selected game's main() function."""
        global screen
        
        try:
            # Handle standard games module routing vs standalone other folder dependencies
            if game_id == "update":
                module_name = "other.update"
            else:
                module_name = f"games.{game_id}.game"
                
            if module_name in sys.modules:
                game_module = importlib.reload(sys.modules[module_name])
            else:
                game_module = importlib.import_module(module_name)
            
            game_module.main(screen)
            
        except Exception as e:
            print(f"Failed to run game {game_id}: {e}")
        
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("🕹️ THE CABINET")
        self.load_games()
        play_sound("menu.mp3", loop=-1, volume=0.5)

    def draw_special_effects(self, game_id, rect):
        """Renders specific custom container animations based on the game profile."""
        self.animation_ticks += 1
        t = self.animation_ticks

        if "pong" in game_id:
            pass 

        elif "racer" in game_id or "neon" in game_id:
            lane_w = 12
            start_x = rect.right - 80
            pygame.draw.rect(screen, (10, 10, 15), (start_x, rect.y + 5, lane_w * 4 + 8, rect.h - 10), border_radius=4)
            for l in range(1, 4):
                lx = start_x + 4 + (l * lane_w)
                for ly in range(rect.y + 5, rect.bottom - 5, 12):
                    pygame.draw.line(screen, (150, 150, 150), (lx, ly), (lx, ly + 6), 1)
            for car in self.racer_cars:
                car["y"] += car["speed"]
                if car["y"] > rect.h - 18:
                    car["y"] = 0
                    car["speed"] = random.uniform(1.5, 3.5)
                cx = start_x + 6 + (car["lane"] * lane_w)
                cy = rect.y + 5 + car["y"]
                pygame.draw.rect(screen, car["color"], (cx, cy, 8, 12), border_radius=2)

        elif "snake" in game_id:
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

        elif "tetris" in game_id:
            pass

        elif "sort" in game_id or "water" in game_id:
            for thick in range(3, 0, -1):
                hue = (t * 3 + thick * 20) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 100, 100, 100)
                pygame.draw.rect(screen, color, rect.inflate(thick * 2, thick * 2), width=1, border_radius=8 + thick)

    def draw(self):
        screen.fill(BG_COLOR)
        
        # --- THE CABINET: Beast Title Rendering ---
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
        
        subtitle = FONT_BODY.render("Select a game using UP/DOWN arrows and hit ENTER to play", True, NEON_PINK)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 105))
        
        pygame.draw.line(screen, NEON_PINK, (50, 140), (WIDTH - 50, 140), 2)
        pygame.draw.line(screen, NEON_CYAN, (50, 580), (WIDTH - 50, 580), 2)

        if not self.games:
            no_games_text = FONT_SUB.render("No games found in /games/ folder!", True, NEON_PINK)
            screen.blit(no_games_text, (WIDTH // 2 - no_games_text.get_width() // 2, 300))
            return

        base_start_y = 165
        card_height = 90
        gap = 15
        
        # Lock target viewport constraint bound matrices cleanly
        self.target_scroll_y = -max(0, (self.selected_index - 3) * (card_height + gap))
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.15 

        mx, my = pygame.mouse.get_pos()

        for i, game in enumerate(self.games):
            y_pos = base_start_y + i * (card_height + gap) + self.scroll_y
            
            mouse_hover = pygame.Rect(50, y_pos, WIDTH - 100, card_height).collidepoint(mx, my)
            is_focused = (i == self.selected_index) or mouse_hover
            
            current_w = WIDTH - 100
            current_h = card_height
            current_x = 50
            current_y = y_pos

            if is_focused:
                current_w += 20
                current_h += 10
                current_x -= 10
                current_y -= 5

            if is_focused and "tetris" in game["id"]:
                shift_x = math.sin(self.animation_ticks * 0.1) * 12
                current_x += shift_x

            if is_focused and "pong" in game["id"]:
                current_x += random.randint(-3, 3)
                current_y += random.randint(-3, 3)

            card_rect = pygame.Rect(current_x, current_y, current_w, current_h)
            
            if card_rect.bottom < 145 or card_rect.top > 575:
                continue

            bg_color = CARD_SELECTED if is_focused else CARD_BG
            pygame.draw.rect(screen, bg_color, card_rect, border_radius=8)
            
            if is_focused:
                pygame.draw.rect(screen, NEON_CYAN, card_rect, width=2, border_radius=8)
                self.draw_special_effects(game["id"], card_rect)
            
            color_title = NEON_CYAN if is_focused else TEXT_MAIN
            title_surf = FONT_SUB.render(game["title"], True, color_title)
            screen.blit(title_surf, (current_x + 20, current_y + 15 if not is_focused else current_y + 20))
            
            desc_surf = FONT_BODY.render(game["description"], True, TEXT_MUTED)
            screen.blit(desc_surf, (current_x + 20, current_y + 45 if not is_focused else current_y + 50))
            
            score_text = f"HI-SCORE: {game['high_score']}"
            score_surf = FONT_SUB.render(score_text, True, NEON_PINK if is_focused else TEXT_MUTED)
            
            right_offset = 110 if ("racer" in game["id"] or "neon" in game["id"]) else 30
            screen.blit(score_surf, (current_x + current_w - score_surf.get_width() - right_offset, current_y + (current_h // 2) - (score_surf.get_height() // 2)))

        # --- SYSTEM UPDATE BUTTON MATRIX ---
        btn_base_w, btn_base_h = 220, 36
        btn_base_x = WIDTH // 2 - btn_base_w // 2
        btn_base_y = 598
        
        # Test mouse overlap for button hover transitions
        btn_hover = pygame.Rect(btn_base_x, btn_base_y, btn_base_w, btn_base_h).collidepoint(mx, my)
        
        if btn_hover:
            btn_base_w += 14
            btn_base_h += 6
            btn_base_x -= 7
            btn_base_y -= 3
            
        btn_rect = pygame.Rect(btn_base_x, btn_base_y, btn_base_w, btn_base_h)
        pygame.draw.rect(screen, (20, 20, 35) if not btn_hover else (10, 40, 30), btn_rect, border_radius=6)
        pygame.draw.rect(screen, NEON_CYAN if not btn_hover else NEON_GREEN, btn_rect, width=2, border_radius=6)
        
        # If hovered, draw internal glowing binary stream effect
        if btn_hover:
            btn_clip_surf = pygame.Surface((btn_base_w - 4, btn_base_h - 4))
            btn_clip_surf.fill((10, 40, 30))
            for drop in self.update_drops:
                drop["y"] += drop["speed"]
                if drop["y"] > btn_base_h - 4:
                    drop["y"] = -10
                    drop["speed"] = random.uniform(1, 3)
                drop_surf = FONT_BTN.render(drop["char"], True, (0, 200, 80))
                # Scale mouse drop coordinate vectors to clip bounding box
                btn_clip_surf.blit(drop_surf, (int(drop["x"] % (btn_base_w - 10)), int(drop["y"])))
            screen.blit(btn_clip_surf, (btn_base_x + 2, btn_base_y + 2))

        btn_txt_color = NEON_CYAN if not btn_hover else TEXT_MAIN
        btn_surf = FONT_BTN.render("[ SYSTEM UPDATE ]", True, btn_txt_color)
        screen.blit(btn_surf, (WIDTH // 2 - btn_surf.get_width() // 2, btn_base_y + (btn_base_h // 2) - (btn_surf.get_height() // 2)))

    def run(self):
        running = True
        while running:
            self.animation_ticks += 1
            self.draw()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.transition_out_and_quit()
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: 
                        mx, my = pygame.mouse.get_pos()
                        
                        # Check System Update Button Trigger Point
                        btn_base_w, btn_base_h = 220, 36
                        if pygame.Rect(WIDTH // 2 - btn_base_w // 2, 598, btn_base_w, btn_base_h).collidepoint(mx, my):
                            self.transition_out_and_launch("update")
                            continue

                        base_start_y = 165
                        card_height = 90
                        gap = 15
                        for i, game in enumerate(self.games):
                            y_pos = base_start_y + i * (card_height + gap) + self.scroll_y
                            if pygame.Rect(50, y_pos, WIDTH - 100, card_height).collidepoint(mx, my):
                                self.selected_index = i
                                self.transition_out_and_launch(self.games[self.selected_index]["id"])

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_index = (self.selected_index - 1) % len(self.games)
                        play_sound("move.mp3")
                    elif event.key == pygame.K_DOWN:
                        self.selected_index = (self.selected_index + 1) % len(self.games)
                        play_sound("move.mp3")
                    elif event.key == pygame.K_RETURN and self.games:
                        self.transition_out_and_launch(self.games[self.selected_index]["id"])
                    elif event.key == pygame.K_ESCAPE:
                        self.transition_out_and_quit()
            
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    launcher = ArcadeLauncher()
    launcher.run()