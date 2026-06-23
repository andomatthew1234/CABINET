import os
import sys
import json
import pygame
import urllib.request
import zipfile
import shutil
import subprocess
import math
import threading
import ssl  # Added to handle SSL verification issues

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init()

# Window Setup
WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("THE CABINET - SYSTEM UPDATE MATRIX")
clock = pygame.time.Clock()

# Colors (Consistent with Launcher/Welcome Matrix)
BG_COLOR = (10, 10, 15)
PANEL_BG = (20, 25, 35)
NEON_CYAN = (0, 240, 255)
NEON_PINK = (255, 0, 127)
NEON_GREEN = (0, 255, 100)
TEXT_MAIN = (255, 255, 255)
TEXT_MUTED = (100, 100, 120)

# Fonts
FONT_TITLE = pygame.font.SysFont("Courier New", 45, bold=True, italic=True)
FONT_SUB = pygame.font.SysFont("Courier New", 24, bold=True)
FONT_TERMINAL = pygame.font.SysFont("Consolas", 16)

# Configuration Vectors
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
MUSIC_DIR = os.path.join(BASE_DIR, 'music')
REPO_ZIP_URL = "https://github.com/andomatthew1234/CABINET/archive/refs/heads/main.zip"

def play_sound(filename, volume=1.0):
    try:
        path = os.path.join(MUSIC_DIR, filename)
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            sound.set_volume(volume)
            sound.play()
    except Exception as e:
        print(f"Audio error for {filename}: {e}")

class SystemUpdater:
    def __init__(self):
        self.state = "READY"  # READY, DOWNLOADING, EXTRACTING, APPLYING, DONE, FAILED
        self.ticks = 0
        self.progress = 0.0
        self.status_log = ["[SYSTEM]: UPDATE VECTOR READY. AWAITING USER COMMAND."]
        self.error_msg = ""
        self.log_lock = threading.Lock()
        
        # Paths for download sequence
        self.zip_path = os.path.join(os.environ.get('TEMP', BASE_DIR), 'cabinet_update.zip')
        self.extract_path = os.path.join(os.environ.get('TEMP', BASE_DIR), 'cabinet_update_extract')

    def log(self, message):
        with self.log_lock:
            self.status_log.append(message)
            if len(self.status_log) > 8:
                self.status_log.pop(0)

    def start_update(self):
        self.state = "DOWNLOADING"
        self.progress = 0.0
        self.log("[STATUS]: CONNECTING TO OUTBOUND REPOSITORY MATRIX...")
        play_sound("launch.mp3", volume=0.5)
        
        # Run network operations in a background thread to prevent Pygame window hangs
        download_thread = threading.Thread(target=self.network_worker, daemon=True)
        download_thread.start()

    def network_worker(self):
        """Background thread worker for accurate downloads and error handling."""
        try:
            # Set up request headers to match modern standard clients and provide an explicit 15s timeout
            req = urllib.request.Request(
                REPO_ZIP_URL, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            # Create an unverified context to bypass local expired/missing SSL root certificates
            context = ssl._create_unverified_context()
            
            with urllib.request.urlopen(req, timeout=15, context=context) as response:
                # Retrieve actual payload size if available from server headers
                total_size = response.getheader('Content-Length')
                if total_size is not None:
                    total_size = int(total_size)
                else:
                    # Fallback default estimation if GitHub compresses chunk transfers dynamically
                    total_size = 5000000 
                
                self.log("[STATUS]: CONNECTION ESTABLISHED. STREAMING REAL-TIME ZIP BUNDLE...")
                
                bytes_downloaded = 0
                chunk_size = 16384  # Read data stream smoothly in 16KB blocks
                
                with open(self.zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        
                        # Calculate mathematically accurate progress percent
                        calc_progress = (bytes_downloaded / total_size) * 90.0
                        self.progress = min(90.0, calc_progress)

            self.log("[OK]: PAYLOAD STREAM COMPLETED SUCCESSFULLY.")
            self.state = "EXTRACTING"
            self.process_extraction()
            
        except Exception as e:
            self.state = "FAILED"
            self.error_msg = str(e)
            self.log(f"[CRITICAL]: INTERRUPT DETECTED -> {self.error_msg[:40]}")

    def process_extraction(self):
        try:
            self.progress = 95.0
            self.log("[STATUS]: UNZIPPING DATA LAYERS INTO TEMP INVENTORY...")
            
            if os.path.exists(self.extract_path):
                shutil.rmtree(self.extract_path)
                
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_path)
                
            self.log("[OK]: DATA EXTRACTION CYCLE TERMINATED.")
            self.progress = 100.0
            self.state = "APPLYING"
        except Exception as e:
            self.state = "FAILED"
            self.error_msg = str(e)

    def apply_update_and_restart(self):
        self.log("[SYSTEM]: SPANNING OVERWRITE PAYLOAD SCRIPT...")
        
        source_dir = os.path.join(self.extract_path, 'CABINET-main')
        batch_updater = os.path.join(os.environ.get('TEMP', BASE_DIR), 'cabinet_hot_swap.bat')
        
        # Write batch routine that completely survives the death of the parent processes
        with open(batch_updater, 'w') as f:
            f.write(f"@echo off\n")
            f.write("timeout /t 1 >nul\n") 
            f.write(f"xcopy \"{source_dir}\\\" \"{BASE_DIR}\\\" /E /I /Y /Q >nul\n")
            f.write(f"del \"{self.zip_path}\"\n")
            f.write(f"start /d \"{BASE_DIR}\" python \"app.py\"\n")
            f.write("exit\n")
            
        pygame.quit()
        # Launch with completely detached windows to completely break out of app.py context limits
        subprocess.Popen([batch_updater], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        sys.exit()

    def draw(self):
        screen.fill(BG_COLOR)
        self.ticks += 1
        t = self.ticks
        
        # Hype Pulsing Header
        pulse = math.sin(t * 0.05) * 3
        title_red = FONT_TITLE.render("SYSTEM UPDATE MATRIX", True, (255, 0, 50))
        title_blue = FONT_TITLE.render("SYSTEM UPDATE MATRIX", True, (0, 200, 255))
        title_main = FONT_TITLE.render("SYSTEM UPDATE MATRIX", True, TEXT_MAIN)
        
        bx = WIDTH // 2 - title_main.get_width() // 2
        by = 40
        screen.blit(title_red, (bx - 2 + pulse, by))
        screen.blit(title_blue, (bx + 2 - pulse, by))
        screen.blit(title_main, (bx, by))
        
        # Main Terminal Log Display Box
        box_w, box_h = 750, 240
        box_x, box_y = WIDTH // 2 - box_w // 2, 140
        pygame.draw.rect(screen, PANEL_BG, (box_x, box_y, box_w, box_h), border_radius=8)
        pygame.draw.rect(screen, NEON_CYAN if self.state != "FAILED" else (255, 0, 50), (box_x, box_y, box_w, box_h), width=2, border_radius=8)
        
        # Access log under lock safety rules
        with self.log_lock:
            for i, line in enumerate(self.status_log):
                color = NEON_GREEN if "[OK]" in line else (NEON_PINK if "[SYSTEM]" in line else TEXT_MAIN)
                log_surf = FONT_TERMINAL.render(line, True, color)
                screen.blit(log_surf, (box_x + 25, box_y + 25 + (i * 24)))
            
        if self.state == "FAILED":
            err_surf = FONT_TERMINAL.render(f"ERROR: {self.error_msg[:65]}", True, (255, 50, 50))
            screen.blit(err_surf, (box_x + 25, box_y + box_h - 35))

        # Dynamic Progress Control Center
        bar_w, bar_h = 600, 30
        bar_x, bar_y = WIDTH // 2 - bar_w // 2, 440
        
        if self.state in ["DOWNLOADING", "EXTRACTING", "APPLYING"]:
            pygame.draw.rect(screen, (30, 30, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            pygame.draw.rect(screen, NEON_PINK, (bar_x + 2, bar_y + 2, int((self.progress / 100.0) * (bar_w - 4)), bar_h - 4), border_radius=2)
            
            bar_length = 25
            filled = int((self.progress / 100.0) * bar_length)
            ascii_str = f"[{'#' * filled}{'-' * (bar_length - filled)}] {int(self.progress)}%"
            ascii_surf = FONT_SUB.render(ascii_str, True, TEXT_MAIN)
            screen.blit(ascii_surf, (WIDTH // 2 - ascii_surf.get_width() // 2, bar_y + 50))
            
        elif self.state == "READY":
            if (t // 20) % 2 == 0:
                prompt_surf = FONT_SUB.render("PRESS [ENTER] TO EXECUTE CORE UPGRADE", True, NEON_GREEN)
                screen.blit(prompt_surf, (WIDTH // 2 - prompt_surf.get_width() // 2, bar_y))
                
            esc_surf = FONT_TERMINAL.render("Press [ESC] to abort and return to Dashboard", True, TEXT_MUTED)
            screen.blit(esc_surf, (WIDTH // 2 - esc_surf.get_width() // 2, bar_y + 60))
            
        elif self.state == "FAILED":
            prompt_surf = FONT_SUB.render("UPGRADE CRASHED. PRESS [ENTER] TO RETRY", True, (255, 50, 50))
            screen.blit(prompt_surf, (WIDTH // 2 - prompt_surf.get_width() // 2, bar_y))

    def run(self):
        running = True
        while running:
            if self.state == "APPLYING":
                # Only execute swapping right when extraction changes flags
                self.apply_update_and_restart()
                
            self.draw()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.state in ["READY", "FAILED"]:
                        running = False
                    elif event.key == pygame.K_RETURN and self.state in ["READY", "FAILED"]:
                        self.start_update()
                        
            pygame.display.flip()
            clock.tick(60)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    updater = SystemUpdater()
    updater.run()