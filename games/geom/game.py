import pygame
import json
import os
import inspect
import math
import random

pygame.init()

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Physics constants
GRAVITY = 0.8
JUMP_STRENGTH = -12.5
PLAYER_SPEED = 6
TERMINAL_VELOCITY = 15

# Colors
PLAYER_COLOR = (0, 255, 255)
PLATFORM_COLOR = (20, 20, 30)
SPIKE_COLOR = (255, 50, 50)
TEXT_COLOR = (255, 255, 255)
SUCCESS_COLOR = (50, 255, 50)

ui_font = pygame.font.Font(None, 48)
title_font = pygame.font.Font(None, 80)
stats_font = pygame.font.Font(None, 36)

class Particle:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(3, 15)
        self.vel = pygame.Vector2(math.cos(angle)*speed, math.sin(angle)*speed)
        self.color = color
        self.life = 255
        self.size = random.randint(3, 8)

    def update(self):
        self.pos += self.vel
        self.life -= 5

    def draw(self, surface, camera_x):
        if self.life > 0:
            alpha_color = (*self.color[:3], max(0, self.life))
            temp_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, alpha_color, (self.size, self.size), self.size)
            surface.blit(temp_surf, (int(self.pos.x - self.size - camera_x), int(self.pos.y - self.size)))

class Player:
    def __init__(self, x, y):
        self.size = 40
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.vel_y = 0
        self.angle = 0
        self.is_jumping = True
        self.dead = False

    def jump(self):
        if not self.is_jumping and not self.dead:
            self.vel_y = JUMP_STRENGTH
            self.is_jumping = True

    def update(self):
        if self.dead:
            return

        self.vel_y += GRAVITY
        if self.vel_y > TERMINAL_VELOCITY:
            self.vel_y = TERMINAL_VELOCITY
            
        self.pos_y += self.vel_y
        self.pos_x += PLAYER_SPEED
        
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if self.is_jumping:
            self.angle -= 6 
        else:
            self.angle = round(self.angle / 90) * 90

    def draw(self, surface, camera_x):
        cube_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(cube_surf, PLAYER_COLOR, (0, 0, self.size, self.size))
        pygame.draw.rect(cube_surf, (255, 255, 255), (0, 0, self.size, self.size), 3)

        rotated_surf = pygame.transform.rotate(cube_surf, self.angle)
        rotated_rect = rotated_surf.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery))
        
        surface.blit(rotated_surf, rotated_rect)

class Level:
    def __init__(self, filepath, level_index=0):
        self.platforms = []
        self.spikes = []
        self.length = 5000
        self.name = "Unknown Level"
        self.total_levels = 1
        self.load_data(filepath, level_index)

    def load_data(self, filepath, level_index):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            self.total_levels = len(data.get('levels', [{}]))
            if level_index >= self.total_levels:
                level_index = 0 # Wrap back to start
                
            level_data = data['levels'][level_index]
            self.name = level_data.get('name', f'Level {level_index + 1}')
            self.length = level_data.get('length', 5000)

            for plat in level_data.get('platforms', []):
                self.platforms.append(pygame.Rect(plat['x'], plat['y'], plat['width'], plat['height']))

            for spike in level_data.get('spikes', []):
                self.spikes.append((spike['x'], spike['y']))

        except Exception as e:
            print(f"Failed to load level JSON: {e}. Generating fallback level.")
            self.platforms = [pygame.Rect(0, 500, 5000, 100)]
            self.spikes = [(600, 500), (900, 500)]

    def draw(self, surface, camera_x):
        for plat in self.platforms:
            render_rect = pygame.Rect(plat.x - camera_x, plat.y, plat.width, plat.height)
            if render_rect.right > 0 and render_rect.left < WIDTH:
                pygame.draw.rect(surface, PLATFORM_COLOR, render_rect)
                pygame.draw.rect(surface, (100, 100, 120), render_rect, 2)

        for spike_x, spike_y in self.spikes:
            screen_x = spike_x - camera_x
            if -50 < screen_x < WIDTH + 50:
                points = [
                    (screen_x, spike_y),
                    (screen_x + 30, spike_y),
                    (screen_x + 15, spike_y - 30)
                ]
                pygame.draw.polygon(surface, SPIKE_COLOR, points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 1)

def handle_collisions(player, level):
    player.is_jumping = True
    
    for plat in level.platforms:
        if player.rect.colliderect(plat):
            if player.vel_y >= 0 and (player.rect.bottom - player.vel_y) <= plat.top + 2:
                player.rect.bottom = plat.top
                player.pos_y = player.rect.y
                player.vel_y = 0
                player.is_jumping = False
            else:
                player.dead = True
                
    if player.is_jumping and player.vel_y >= 0:
        for plat in level.platforms:
            if plat.left < player.rect.right and plat.right > player.rect.left:
                if abs(player.rect.bottom - plat.top) <= 2:
                    player.rect.bottom = plat.top
                    player.pos_y = player.rect.y
                    player.vel_y = 0
                    player.is_jumping = False
                    break

    hitbox = player.rect.inflate(-16, -16)
    for spike_x, spike_y in level.spikes:
        spike_rect = pygame.Rect(spike_x + 8, spike_y - 20, 14, 20)
        if hitbox.colliderect(spike_rect):
            player.dead = True

def main(*args):
    if args and isinstance(args[0], pygame.Surface):
        screen = args[0]
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
    pygame.display.set_caption("Geometry Dash Clone")
    clock = pygame.time.Clock()

    try:
        game_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    except Exception:
        game_dir = os.getcwd()

    level_path = os.path.join(game_dir, "levels.json")
    
    root_dir = os.path.dirname(os.path.dirname(game_dir))
    music_path = os.path.join(root_dir, "music", "geom.mp3")
    
    if os.path.exists(music_path):
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading music: {e}")

    # --- Session State ---
    current_level_idx = 0
    level = Level(level_path, current_level_idx)
    player = Player(100, 0)
    
    camera_x = 0
    camera_offset = WIDTH * 0.3
    
    attempts = 1
    level_start_time = pygame.time.get_ticks()
    
    death_timer = 0
    
    # Map Completion State
    map_complete = False
    completion_timer = 0
    final_time = 0
    particles = []

    running = True

    while running:
        clock.tick(FPS)
        current_ticks = pygame.time.get_ticks()
        
        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- Continuous Input (Hold to Jump) ---
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()
        if not map_complete and (keys[pygame.K_SPACE] or keys[pygame.K_UP] or mouse_pressed[0]):
            player.jump()

        # --- Update ---
        if map_complete:
            # Run particle logic and wait for next level
            for p in particles:
                p.update()
            particles = [p for p in particles if p.life > 0]
            
            if current_ticks - completion_timer > 4000: # Wait 4 seconds
                # Load next level
                current_level_idx += 1
                level = Level(level_path, current_level_idx)
                player = Player(100, 0)
                camera_x = 0
                attempts = 1
                level_start_time = pygame.time.get_ticks()
                map_complete = False
                particles.clear()
                
        elif not player.dead:
            player.update()
            handle_collisions(player, level)
            
            target_camera_x = player.rect.x - camera_offset
            camera_x += (target_camera_x - camera_x) * 0.2
            
            # Win Condition
            if player.rect.x > level.length:
                map_complete = True
                completion_timer = pygame.time.get_ticks()
                final_time = (completion_timer - level_start_time) / 1000.0
                
                # Generate Explosion
                for _ in range(120):
                    particles.append(Particle(player.rect.centerx, player.rect.centery, PLAYER_COLOR))
                    particles.append(Particle(player.rect.centerx, player.rect.centery, SUCCESS_COLOR))
                
            # Pit death
            if player.rect.y > HEIGHT + 100:
                player.dead = True
                
        else:
            death_timer += 1
            if death_timer > FPS * 0.8:
                player = Player(100, 0)
                camera_x = 0
                death_timer = 0
                attempts += 1

        # --- Render ---
        # Rainbow background using HSV - Brighter values
        hue = (current_ticks / 40.0) % 360
        bg_color = pygame.Color(0)
        bg_color.hsva = (hue, 50, 60, 100) # Saturation 50, Value 60 (Brighter rainbow)
        screen.fill(bg_color)
        
        level.draw(screen, camera_x)
        
        if not player.dead and not map_complete:
            player.draw(screen, camera_x)
        elif player.dead:
            pygame.draw.circle(screen, PLAYER_COLOR, (int(player.rect.centerx - camera_x), int(player.rect.centery)), death_timer * 4, 3)

        for p in particles:
            p.draw(screen, camera_x)

        # UI Overlay
        if map_complete:
            # Map Complete Text
            win_text = title_font.render("MAP COMPLETE", True, SUCCESS_COLOR)
            win_rect = win_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 40))
            screen.blit(win_text, win_rect)
            
            # Stats Text
            time_text = stats_font.render(f"Time: {final_time:.2f}s", True, TEXT_COLOR)
            time_rect = time_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
            screen.blit(time_text, time_rect)
            
            attempt_text = stats_font.render(f"Attempts: {attempts}", True, TEXT_COLOR)
            attempt_rect = attempt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
            screen.blit(attempt_text, attempt_rect)
        else:
            # Top-left UI
            progress = max(0, min(100, int((player.rect.x / level.length) * 100)))
            progress_text = ui_font.render(f"{level.name} - {progress}%", True, TEXT_COLOR)
            screen.blit(progress_text, (20, 20))
            
            att_text = stats_font.render(f"Attempt {attempts}", True, (200, 200, 200))
            screen.blit(att_text, (20, 60))

        pygame.display.flip()

    pygame.mixer.music.stop()
    if not args:
        pygame.quit()

if __name__ == "__main__":
    main()