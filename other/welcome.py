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
FONT_MASSIVE = pygame.font.SysFont("Impact", 120, bold=True)
FONT_SUB = pygame.font.SysFont("Courier New", 28, bold=True)
FONT_TERMINAL = pygame.font.SysFont("Consolas", 16)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
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
        # Master State Pipeline
        self.state = "BIOS" # BIOS -> BIOS_FADE -> LOADING -> GLITCH -> SPRINT -> FADEOUT
        self.ticks = 0
        self.state_ticks = 0
        self.sprint_start_tick = 0
        
        # BIOS Sequence Data
        self.bios_lines = []
        self.bios_messages = [
            "CPU_INIT_OK()", "MEM_CHECK: 64000K OK", "LOADING GRAPHICS KERNEL...",
            "MOUNTING /games/pong.cart ... OK", "MOUNTING /games/racer.cart ... OK",
            "MOUNTING /games/tetris.cart ... OK", "MOUNTING /games/snake.cart ... OK",
            "MOUNTING /games/water_sort.cart ... OK", "BYPASSING NEURAL LIMITERS...",
            "AUDIO_SYSTEM: ONLINE", "AWAITING SYSTEM WAKE..."
        ]
        
        # Animation Data
        self.load_progress = 0.0
        self.fade_alpha = 0
        self.stars = [[random.uniform(-WIDTH, WIDTH), random.uniform(-HEIGHT, HEIGHT), random.uniform(0.1, 2.0)] for _ in range(400)]
        self.grid_y = 0

    def draw_bios(self):
        screen.fill((5, 5, 10))
        if self.ticks % 4 == 0 and len(self.bios_lines) < len(self.bios_messages):
            self.bios_lines.append(self.bios_messages[len(self.bios_lines)])
            if len(self.bios_lines) % 3 == 0:
                play_sound("move.mp3", volume=0.15) 
            
        for i, line in enumerate(self.bios_lines):
            text = FONT_TERMINAL.render(line, True, (0, 255, 100))
            screen.blit(text, (20, 20 + (i * 20)))
            
        if len(self.bios_lines) >= len(self.bios_messages):
            if self.state_ticks == 0: self.state_ticks = self.ticks
            if self.ticks - self.state_ticks > 60: 
                self.state = "BIOS_FADE"
                self.fade_alpha = 0

    def draw_bios_fade(self):
        # Continue rendering BIOS beneath fade
        screen.fill((5, 5, 10))
        for i, line in enumerate(self.bios_lines):
            text = FONT_TERMINAL.render(line, True, (0, 255, 100))
            screen.blit(text, (20, 20 + (i * 20)))
            
        self.fade_alpha += 4
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(min(255, self.fade_alpha))
        screen.blit(overlay, (0, 0))
        
        if self.fade_alpha >= 255:
            self.state = "LOADING"
            self.state_ticks = self.ticks

    def draw_loading(self):
        screen.fill((0, 0, 0))
        
        self.load_progress += 0.6
        if self.load_progress >= 100:
            self.load_progress = 100
            self.state = "GLITCH"
            self.state_ticks = self.ticks
            play_sound("move.mp3", volume=1.0) # Sharp glitch noise
            return
        
        # Clean progress bar
        pygame.draw.rect(screen, (20, 20, 30), (WIDTH//2 - 200, HEIGHT//2 - 20, 400, 40), 2)
        pygame.draw.rect(screen, (0, 255, 255), (WIDTH//2 - 198, HEIGHT//2 - 18, int((self.load_progress/100) * 396), 36))
        
        load_text = FONT_SUB.render("COMPILING SYSTEM ASSETS...", True, (255, 0, 127))
        bar_text = FONT_TERMINAL.render(f"PROGRESS: {int(self.load_progress)}%", True, (255, 255, 255))
        
        screen.blit(load_text, (WIDTH//2 - load_text.get_width()//2, HEIGHT//2 - 70))
        screen.blit(bar_text, (WIDTH//2 - bar_text.get_width()//2, HEIGHT//2 + 40))

    def draw_glitch(self):
        screen.fill((0, 0, 0))
        local_t = self.ticks - self.state_ticks
        
        # 40 frames of severe glitching
        if local_t < 40:
            pygame.draw.rect(screen, (20, 20, 30), (WIDTH//2 - 200, HEIGHT//2 - 20, 400, 40), 2)
            pygame.draw.rect(screen, (255, 0, 50), (WIDTH//2 - 198, HEIGHT//2 - 18, 396, 36))
            
            glitch_chars = ['@', '#', '$', '%', '&', '*', '!', 'X', 'ERR']
            glitch_str = "".join([random.choice(glitch_chars) for _ in range(15)])
            
            load_text = FONT_SUB.render(f"SYS_FAIL: {glitch_str}", True, (255, 255, 0))
            bar_text = FONT_TERMINAL.render("FATAL_MEMORY_LEAK_0xFFFFFFFF", True, (255, 0, 50))
            
            jx = random.randint(-15, 15)
            jy = random.randint(-15, 15)
            
            screen.blit(load_text, (WIDTH//2 - load_text.get_width()//2 + jx, HEIGHT//2 - 70 + jy))
            screen.blit(bar_text, (WIDTH//2 - bar_text.get_width()//2 - jx, HEIGHT//2 + 40 - jy))
        
        # 20 frames of pure black silence
        elif local_t < 60:
            pass # Screen stays pure black
            
        else:
            # Boom. Hit the music and start the sprint.
            self.state = "SPRINT"
            self.sprint_start_tick = self.ticks
            play_sound("menu.mp3", loop=-1, volume=1.0)

    def draw_sprint(self):
        """ The 31-second (1860 tick) cinematic showcase synced perfectly to 60fps. """
        st = self.ticks - self.sprint_start_tick
        screen.fill((0, 0, 0))

        # --- PHASE 1: THE SINGULARITY (0s - 4s / 0 - 240 ticks) ---
        if st < 240:
            # First second: Draw horizontal line
            progress_w = min(1.0, st / 60.0)
            # Second second: Explode vertically
            progress_h = min(1.0, max(0.0, st - 60) / 60.0) ** 4
            
            line_w = int(progress_w * WIDTH)
            line_h = int(progress_h * HEIGHT)
            
            pygame.draw.rect(screen, (255, 255, 255), (WIDTH//2 - line_w//2, HEIGHT//2 - line_h//2, line_w, max(2, line_h)))
            
            if st > 120:
                txt = FONT_SUB.render("Welcome to the Cabinet", True, (0, 0, 0))
                screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2))

        # --- PHASE 2: THE SHOWCASE (4s - 9s / 240 - 540 ticks) ---
        elif st < 540:
            local_t = st - 240
            phase = local_t // 60 # 60 frames (1 second) per game
            
            games = [
                ("OMNI-PONG", (0, 255, 255)),
                ("NEON RACER", (255, 0, 127)),
                ("TOXIC SNAKE", (0, 255, 100)),
                ("TETRIS MATRIX", (255, 255, 0)),
                ("WATER SORT", (150, 0, 255))
            ]
            
            if phase < len(games):
                name, color = games[phase]
                
                # Extreme contrast: Solid black background, neon color bursts
                bg_radius = int((local_t % 60) / 60.0 * WIDTH * 1.5)
                pygame.draw.circle(screen, (*color, 30), (WIDTH//2, HEIGHT//2), bg_radius)
                
                jitter_x = random.randint(-4, 4)
                jitter_y = random.randint(-4, 4)
                
                txt_shadow = FONT_MASSIVE.render(name, True, (255, 255, 255))
                txt_main = FONT_MASSIVE.render(name, True, color)
                
                screen.blit(txt_shadow, (WIDTH//2 - txt_shadow.get_width()//2 + jitter_x - 4, HEIGHT//2 - txt_shadow.get_height()//2 + jitter_y))
                screen.blit(txt_main, (WIDTH//2 - txt_main.get_width()//2 + jitter_x, HEIGHT//2 - txt_main.get_height()//2 + jitter_y))

        # --- PHASE 3: THE OVERDRIVE (9s - 15s / 540 - 900 ticks) ---
        elif st < 900:
            self.grid_y += 20 
            if self.grid_y > 100: self.grid_y = 0
            
            for y in range(0, HEIGHT, 40):
                py = HEIGHT - int((HEIGHT - y) ** 2 / HEIGHT) + self.grid_y
                if py < HEIGHT:
                    pygame.draw.line(screen, (0, 255, 100), (0, py), (WIDTH, py), 1)
            
            for x in range(0, WIDTH + 200, 100):
                offset = x - WIDTH//2
                pygame.draw.line(screen, (0, 255, 100), (WIDTH//2, HEIGHT//2 - 50), (WIDTH//2 + offset * 3, HEIGHT), 2)
            
            # Flash text on 30 frame intervals (half seconds)
            glitch_txt = "SYSTEM OVERDRIVE ENGAGED" if (st // 30) % 2 == 0 else ""
            if glitch_txt:
                gt = FONT_MASSIVE.render(glitch_txt, True, (255, 0, 50))
                screen.blit(gt, (WIDTH//2 - gt.get_width()//2, HEIGHT//4))

        # --- PHASE 4: THE BEAST (15s - 25s / 900 - 1500 ticks) ---
        elif st < 1500:
            for star in self.stars:
                star[2] -= 0.15 
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
                    pygame.draw.line(screen, (255, 255, 255), (px, py), (x, y), 3)

            pulse = math.sin(st * 0.15) * 12
            float_y = math.sin(st * 0.05) * 15
            title_str = "THE CABINET"
            
            t_red = FONT_BEAST.render(title_str, True, (255, 0, 50))
            t_blue = FONT_BEAST.render(title_str, True, (0, 200, 255))
            t_main = FONT_BEAST.render(title_str, True, (255, 255, 255))
            
            bx = WIDTH // 2 - t_main.get_width() // 2
            by = HEIGHT // 2 - t_main.get_height() // 2 + float_y
            
            screen.blit(t_red, (bx - 10 + pulse, by))
            screen.blit(t_blue, (bx + 10 - pulse, by))
            screen.blit(t_main, (bx, by))

        # --- PHASE 5: COUNTDOWN (25s - 31s / 1500 - 1860 ticks) ---
        elif st < 1860:
            if st < 1620:
                # "LAUNCHING IN..." takes up 1500 to 1620 (2 seconds)
                txt = FONT_MASSIVE.render("LAUNCHING IN...", True, (255, 255, 255))
                screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2))
            else:
                # 3, 2, 1 Countdown Sequence (80 frames / 1.33 seconds per number)
                local_t = st - 1620
                count = 3 - (local_t // 80)
                
                if count > 0:
                    ct = FONT_MASSIVE.render(str(count), True, (255, 255, 255))
                    sx = random.randint(-15, 15)
                    sy = random.randint(-15, 15)
                    screen.blit(ct, (WIDTH//2 - ct.get_width()//2 + sx, HEIGHT//2 - ct.get_height()//2 + sy))

        # --- TRIGGER AT 31 SECONDS ---
        else:
            self.trigger_launch()

    def trigger_launch(self):
        if self.state != "FADEOUT":
            self.state = "FADEOUT"
            play_sound("launch.mp3")
            # Smooth fadeout of the soundtrack
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
                        
                    # Dev Skip: Instantly trigger launch
                    if event.key == pygame.K_SPACE:
                        self.trigger_launch()

            # --- RENDER PIPELINE ---
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
                
                self.fade_alpha += 8
                flash_surf = pygame.Surface((WIDTH, HEIGHT))
                flash_surf.fill((255, 255, 255))
                flash_surf.set_alpha(min(255, self.fade_alpha))
                screen.blit(flash_surf, (0,0))
                
                if self.fade_alpha >= 300: 
                    pygame.quit()
                    subprocess.Popen([sys.executable, APP_PATH])
                    sys.exit()

            pygame.display.flip()
            clock.tick(60)

        pygame.mixer.quit()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    intro = IntroSequence()
    intro.run()