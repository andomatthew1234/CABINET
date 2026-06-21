import os
import sys
import pygame
import random
import math
import subprocess

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init()

# Window Setup
WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("INITIALIZING... THE CABINET")
clock = pygame.time.Clock()

# Fonts
FONT_BEAST = pygame.font.SysFont("Courier New", 90, bold=True, italic=True)
FONT_MASSIVE = pygame.font.SysFont("Impact", 110, bold=True)
FONT_SUB = pygame.font.SysFont("Courier New", 28, bold=True)
FONT_TERMINAL = pygame.font.SysFont("Consolas", 16)

# Absolute Path Resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR) 
MUSIC_DIR = os.path.join(BASE_DIR, 'music')
APP_PATH = os.path.join(BASE_DIR, 'app.py')

def play_sound(filename, loop=0, volume=1.0):
    try:
        path = os.path.join(MUSIC_DIR, filename)
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

class IntroSequence:
    def __init__(self):
        # Target: 25 Seconds Total Runtime (1500 frames at 60 FPS)
        self.state = "BIOS"  # BIOS -> BIOS_FADE -> LOADING -> GLITCH -> SPRINT -> FADEOUT
        self.ticks = 0
        self.state_ticks = 0
        self.sprint_start_tick = 0
        
        # BIOS Sequence Data
        self.bios_lines = []
        self.bios_messages = [
            "CPU_CORE_INIT: CORE_MATRIX_OK", "MEM_ALLOC: 131072K BUFFER CACHE INITIALIZED", 
            "GRAPHICS LAYER: ACCELERATION MODULE DETECTED",
            "SCANNING /GAMES/ FILESYSTEM MATRIX...", "MOUNTING: ast, blocks, fighter, pong, racing, snake, tetris",
            "D-PAD / JOYSTICK INTERFACE CONNECTED", "AUDIO ENGINE: 44100HZ MIXER ONLINE", 
            "DECOUPLING HOVER OVERLAY ARRAYS...", "ESTABLISHING MAIN SYSTEM TERMINAL HANDSHAKE..."
        ]
        
        # Animation & Special Effects State
        self.load_progress = 0.0
        self.fade_alpha = 0
        self.stars = [[random.uniform(-WIDTH, WIDTH), random.uniform(-HEIGHT, HEIGHT), random.uniform(0.1, 2.0)] for _ in range(350)]
        self.grid_y = 0
        self.skip_hint_alpha = 255

    def draw_skip_hint(self):
        """Renders an elegant fading 'Press Space to Skip' overlay at the bottom footer."""
        if self.ticks < 180:  # Fades smoothly over the first 3 seconds
            self.skip_hint_alpha = max(0, 255 - int((self.ticks / 180.0) * 255))
            
        if self.skip_hint_alpha > 0:
            hint_surface = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
            txt = FONT_TERMINAL.render("— PRESS SPACEBAR TO ABORT PROLOGUE SEQUENCE —", True, (0, 240, 255))
            hint_surface.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 10))
            hint_surface.set_alpha(self.skip_hint_alpha)
            screen.blit(hint_surface, (0, HEIGHT - 50))

    def draw_bios(self):
        screen.fill((8, 8, 12))
        # Speed up BIOS line feed to get into action faster
        if self.ticks % 3 == 0 and len(self.bios_lines) < len(self.bios_messages):
            self.bios_lines.append(self.bios_messages[len(self.bios_lines)])
            if len(self.bios_lines) % 2 == 0:
                play_sound("move.mp3", volume=0.10) 
            
        for i, line in enumerate(self.bios_lines):
            text = FONT_TERMINAL.render(line, True, (0, 255, 150))
            screen.blit(text, (30, 30 + (i * 22)))
            
        if len(self.bios_lines) >= len(self.bios_messages):
            if self.state_ticks == 0: self.state_ticks = self.ticks
            if self.ticks - self.state_ticks > 30: 
                self.state = "BIOS_FADE"
                self.fade_alpha = 0

    def draw_bios_fade(self):
        screen.fill((8, 8, 12))
        for i, line in enumerate(self.bios_lines):
            text = FONT_TERMINAL.render(line, True, (0, 255, 150))
            screen.blit(text, (30, 30 + (i * 22)))
            
        self.fade_alpha += 8
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(min(255, self.fade_alpha))
        screen.blit(overlay, (0, 0))
        
        if self.fade_alpha >= 255:
            self.state = "LOADING"
            self.state_ticks = self.ticks

    def draw_loading(self):
        screen.fill((5, 5, 8))
        
        # Accelerated asset processing speed
        self.load_progress += 1.4
        if self.load_progress >= 100:
            self.load_progress = 100
            self.state = "GLITCH"
            self.state_ticks = self.ticks
            play_sound("move.mp3", volume=0.7) 
            return
        
        # Sleek Neon Loading Bar Construction
        pygame.draw.rect(screen, (30, 30, 45), (WIDTH//2 - 250, HEIGHT//2 - 15, 500, 30), border_radius=6)
        pygame.draw.rect(screen, (0, 240, 255), (WIDTH//2 - 247, HEIGHT//2 - 12, int((self.load_progress/100) * 494), 24), border_radius=4)
        
        load_text = FONT_SUB.render("COMPILING RUNTIME INFRASTRUCTURE", True, (255, 0, 127))
        bar_text = FONT_TERMINAL.render(f"SYNCHRONIZING FILE ENGINES: {int(self.load_progress)}%", True, (150, 150, 180))
        
        screen.blit(load_text, (WIDTH//2 - load_text.get_width()//2, HEIGHT//2 - 60))
        screen.blit(bar_text, (WIDTH//2 - bar_text.get_width()//2, HEIGHT//2 + 35))

    def draw_glitch(self):
        screen.fill((0, 0, 0))
        local_t = self.ticks - self.state_ticks
        
        # Sharp 20 frame crash matrix simulation
        if local_t < 20:
            pygame.draw.rect(screen, (255, 0, 80), (WIDTH//2 - 250, HEIGHT//2 - 15, 500, 30))
            glitch_chars = ['@', 'Ø', '$', '%', '&', '▒', '!', '█', 'SYSTEM_ERR']
            glitch_str = "".join([random.choice(glitch_chars) for _ in range(12)])
            
            load_text = FONT_SUB.render(f"OVERFLOW: {glitch_str}", True, (255, 255, 0))
            bar_text = FONT_TERMINAL.render("STACK_LEAK_CORRUPT_TERMINAL_0x000000", True, (255, 30, 30))
            
            jx = random.randint(-12, 12)
            jy = random.randint(-12, 12)
            
            screen.blit(load_text, (WIDTH//2 - load_text.get_width()//2 + jx, HEIGHT//2 - 60 + jy))
            screen.blit(bar_text, (WIDTH//2 - bar_text.get_width()//2 - jx, HEIGHT//2 + 35 - jy))
        elif local_t < 35:
            pass  # Pure cinematic dead space frame pause
        else:
            # Shift master orchestration layer to intro track soundtrack execution
            self.state = "SPRINT"
            self.sprint_start_tick = self.ticks
            play_sound("intro.mp3", loop=-1, volume=0.8)

    def draw_sprint(self):
        st = self.ticks - self.sprint_start_tick
        screen.fill((0, 0, 0))

        # --- PHASE 1: THE CORE GATEWAY (0s - 3s) ---
        if st < 180:
            progress_w = min(1.0, st / 45.0)
            progress_h = min(1.0, max(0.0, st - 45) / 45.0) ** 4
            
            line_w = int(progress_w * WIDTH)
            line_h = int(progress_h * HEIGHT)
            
            pygame.draw.rect(screen, (255, 255, 255), (WIDTH//2 - line_w//2, HEIGHT//2 - line_h//2, line_w, max(2, line_h)))
            
            if st > 80:
                txt = FONT_SUB.render("INITIALIZING MAIN SELECTION VAULT", True, (10, 10, 20))
                screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2))

        # --- PHASE 2: DYNAMIC GAME CAROUSEL SHOWCASE (3s - 10s) ---
        elif st < 600:
            local_t = st - 180
            # 60 frames per phase loop sequence showcase
            phase = local_t // 60 
            
            games_pool = [
                ("ASTREIOIDS", (0, 240, 255)),
                ("GRIDFUSION", (0, 255, 150)),
                ("STREET FIGHTER", (255, 100, 0)),
                ("NEON RACER", (255, 0, 127)),
                ("TOXIC SNAKE", (100, 255, 50)),
                ("TETRIS MATRIX", (255, 255, 0)),
                ("WATER SORT", (200, 0, 255))
            ]
            
            if phase < len(games_pool):
                name, color = games_pool[phase]
                bg_radius = int((local_t % 60) / 60.0 * WIDTH * 1.6)
                pygame.draw.circle(screen, (*color, 25), (WIDTH//2, HEIGHT//2), bg_radius, 4)
                
                jx = random.randint(-3, 3)
                jy = random.randint(-3, 3)
                
                txt_shadow = FONT_MASSIVE.render(name, True, (255, 255, 255))
                txt_main = FONT_MASSIVE.render(name, True, color)
                
                screen.blit(txt_shadow, (WIDTH//2 - txt_shadow.get_width()//2 + jx - 3, HEIGHT//2 - txt_shadow.get_height()//2 + jy))
                screen.blit(txt_main, (WIDTH//2 - txt_main.get_width()//2 + jx, HEIGHT//2 - txt_main.get_height()//2 + jy))

        # --- PHASE 3: GRID ACCELERATION (10s - 14s) ---
        elif st < 840:
            self.grid_y += 24 
            if self.grid_y > 100: self.grid_y = 0
            
            for y in range(0, HEIGHT, 40):
                py = HEIGHT - int((HEIGHT - y) ** 2 / HEIGHT) + self.grid_y
                if py < HEIGHT:
                    pygame.draw.line(screen, (0, 240, 255), (0, py), (WIDTH, py), 1)
            
            for x in range(0, WIDTH + 200, 100):
                offset = x - WIDTH//2
                pygame.draw.line(screen, (0, 240, 255), (WIDTH//2, HEIGHT//2 - 50), (WIDTH//2 + offset * 3, HEIGHT), 2)
            
            if (st // 20) % 2 == 0:
                gt = FONT_MASSIVE.render("LAUNCH SEQUENCE ACTIVE", True, (255, 0, 100))
                screen.blit(gt, (WIDTH//2 - gt.get_width()//2, HEIGHT//4))

        # --- PHASE 4: TUNNEL SPRINT HYPERSPACE (14s - 20s) ---
        elif st < 1200:
            for star in self.stars:
                star[2] -= 0.22  # High speed hyperspace drift mechanics
                if star[2] <= 0.1: 
                    star[0] = random.uniform(-WIDTH, WIDTH)
                    star[1] = random.uniform(-HEIGHT, HEIGHT)
                    star[2] = 2.0
                    
                k = 128.0 / star[2]
                x = int(star[0] * k + WIDTH / 2)
                y = int(star[1] * k + HEIGHT / 2)
                prev_k = 128.0 / (star[2] + 0.3)
                px = int(star[0] * prev_k + WIDTH / 2)
                py = int(star[1] * prev_k + HEIGHT / 2)
                
                if -1000 <= x <= WIDTH + 1000 and -1000 <= y <= HEIGHT + 1000:
                    pygame.draw.line(screen, (255, 255, 255), (px, py), (x, y), 2)

            pulse = math.sin(st * 0.2) * 15
            float_y = math.sin(st * 0.08) * 12
            title_str = "THE CABINET"
            
            t_red = FONT_BEAST.render(title_str, True, (255, 0, 50))
            t_blue = FONT_BEAST.render(title_str, True, (0, 200, 255))
            t_main = FONT_BEAST.render(title_str, True, (255, 255, 255))
            
            bx = WIDTH // 2 - t_main.get_width() // 2
            by = HEIGHT // 2 - t_main.get_height() // 2 + float_y
            
            screen.blit(t_red, (bx - 8 + pulse, by))
            screen.blit(t_blue, (bx + 8 - pulse, by))
            screen.blit(t_main, (bx, by))

        # --- PHASE 5: ULTIMATE RADIAL COUNTDOWN (20s - 25s) ---
        elif st < 1500:
            local_t = st - 1200
            count = 5 - (local_t // 60)
            
            if count > 0:
                # Pulsing circular shockwaves matching countdown numbers
                rad_pulse = (local_t % 60) / 60.0
                pygame.draw.circle(screen, (0, 255, 150), (WIDTH//2, HEIGHT//2), int(rad_pulse * 300), 3)
                
                ct = FONT_MASSIVE.render(str(count), True, (255, 255, 255))
                sx = random.randint(-6, 6)
                sy = random.randint(-6, 6)
                screen.blit(ct, (WIDTH//2 - ct.get_width()//2 + sx, HEIGHT//2 - ct.get_height()//2 + sy))
        else:
            self.trigger_launch()

    def trigger_launch(self):
        if self.state != "FADEOUT":
            self.state = "FADEOUT"
            play_sound("launch.mp3")
            pygame.mixer.music.fadeout(1000)

    def run(self):
        running = True
        while running:
            self.ticks += 1
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_SPACE:
                        self.trigger_launch()

            if self.state == "BIOS":
                self.draw_bios()
            elif self.state == "BIOS_FADE":
                self.draw_bios_fade()
            elif self.state == "LOADING":
                self.draw_loading()
            elif self.state == "GLITCH":
                self.draw_glitch()
            elif self.state == "SPRINT":
                self.draw_sprint()
            elif self.state == "FADEOUT":
                self.draw_sprint() 
                
                self.fade_alpha += 12  # Faster flash velocity fade transition
                flash_surf = pygame.Surface((WIDTH, HEIGHT))
                flash_surf.fill((255, 255, 255))
                flash_surf.set_alpha(min(255, self.fade_alpha))
                screen.blit(flash_surf, (0,0))
                
                if self.fade_alpha >= 300: 
                    pygame.quit()
                    subprocess.Popen([sys.executable, APP_PATH], cwd=BASE_DIR)
                    sys.exit()

            # Ensure overlay hint stays active across initial boots
            if self.state in ["BIOS", "BIOS_FADE", "LOADING", "GLITCH", "SPRINT"]:
                self.draw_skip_hint()

            pygame.display.flip()
            clock.tick(60)

        pygame.mixer.quit()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    intro = IntroSequence()
    intro.run()