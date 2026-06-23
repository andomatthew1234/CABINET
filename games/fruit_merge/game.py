import pygame
import random
import math
import os

pygame.init()

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.4
BOUNCE = 0.2
RESTITUTION = 0.1 # Energy lost in collisions
MERGE_COOLDOWN = 10 # Frames to prevent multi-merging the same fruit

# Colors
BG_COLOR = (245, 235, 220)
WALL_COLOR = (180, 160, 140)
DANGER_COLOR = (255, 100, 100)

# Fruit Tiers: (Emoji, Color, Radius, Mass, Points)
FRUITS = [
    ("🍒", (200, 0, 50), 15, 1.0, 2),       # 0: Cherry
    ("🍓", (255, 50, 50), 22, 1.5, 4),      # 1: Strawberry
    ("🍇", (120, 50, 180), 30, 2.0, 8),     # 2: Grape
    ("🍊", (255, 150, 0), 38, 2.5, 16),     # 3: Orange
    ("🍎", (220, 20, 40), 48, 3.0, 32),     # 4: Apple
    ("🍐", (180, 220, 50), 58, 3.5, 64),    # 5: Pear
    ("🍑", (255, 180, 170), 70, 4.0, 128),  # 6: Peach
    ("🍍", (255, 220, 50), 82, 4.5, 256),   # 7: Pineapple
    ("🍈", (150, 255, 150), 96, 5.0, 512),  # 8: Melon
    ("🍉", (50, 200, 80), 115, 6.0, 1024)   # 9: Watermelon (Max)
]

# Try to load a system emoji font, fallback to default
try:
    emoji_font = pygame.font.SysFont("segoeuiemoji", 40)
except:
    emoji_font = pygame.font.Font(None, 40)

ui_font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 72)

# Container boundaries
CONTAINER_LEFT = 200
CONTAINER_RIGHT = 600
CONTAINER_BOTTOM = 550
WARNING_LINE = 150

class Fruit:
    def __init__(self, x, y, tier):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.tier = tier
        self.emoji, self.color, self.radius, self.mass, self.points = FRUITS[tier]
        self.active = True # False means it's held by the player
        self.marked_for_deletion = False
        self.merge_cooldown = 0
        
        # Render emoji surface once
        self.text_surf = emoji_font.render(self.emoji, True, (0, 0, 0))
        # Scale text surface to fit inside the circle
        scale_factor = (self.radius * 1.5) / max(self.text_surf.get_width(), 1)
        new_size = (int(self.text_surf.get_width() * scale_factor), int(self.text_surf.get_height() * scale_factor))
        self.text_surf = pygame.transform.scale(self.text_surf, new_size)
        self.text_rect = self.text_surf.get_rect()

    def update(self):
        if not self.active:
            return

        if self.merge_cooldown > 0:
            self.merge_cooldown -= 1

        # Apply gravity
        self.vel.y += GRAVITY
        
        # Terminal velocity
        if self.vel.length() > 20:
            self.vel.scale_to_length(20)

        self.pos += self.vel

        # Wall Collisions
        if self.pos.x - self.radius < CONTAINER_LEFT:
            self.pos.x = CONTAINER_LEFT + self.radius
            self.vel.x *= -BOUNCE
        elif self.pos.x + self.radius > CONTAINER_RIGHT:
            self.pos.x = CONTAINER_RIGHT - self.radius
            self.vel.x *= -BOUNCE

        # Floor Collision
        if self.pos.y + self.radius > CONTAINER_BOTTOM:
            self.pos.y = CONTAINER_BOTTOM - self.radius
            self.vel.y *= -BOUNCE
            # Apply ground friction
            self.vel.x *= 0.8

    def draw(self, surface):
        # Draw base circle
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), self.radius, 2)
        
        # Draw emoji centered
        self.text_rect.center = (int(self.pos.x), int(self.pos.y))
        surface.blit(self.text_surf, self.text_rect)

class Particle:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-5, 5), random.uniform(-5, 5))
        self.color = color
        self.life = 255
        self.decay = random.randint(10, 20)
        self.size = random.randint(3, 8)

    def update(self):
        self.pos += self.vel
        self.vel.y += 0.2
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha_color = (*self.color[:3], max(0, self.life))
            temp_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, alpha_color, (self.size, self.size), self.size)
            surface.blit(temp_surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))

def resolve_collisions(fruits, particles, game_state):
    # Iterative solver for stability
    for _ in range(3):
        for i in range(len(fruits)):
            for j in range(i + 1, len(fruits)):
                f1 = fruits[i]
                f2 = fruits[j]

                if not f1.active or not f2.active:
                    continue
                if f1.marked_for_deletion or f2.marked_for_deletion:
                    continue

                diff = f1.pos - f2.pos
                dist = diff.length()
                min_dist = f1.radius + f2.radius

                if dist < min_dist:
                    # Check for merge
                    if f1.tier == f2.tier and f1.tier < len(FRUITS) - 1 and f1.merge_cooldown == 0 and f2.merge_cooldown == 0:
                        f1.marked_for_deletion = True
                        f2.marked_for_deletion = True
                        
                        # Create new merged fruit
                        new_tier = f1.tier + 1
                        new_pos = (f1.pos + f2.pos) / 2
                        new_fruit = Fruit(new_pos.x, new_pos.y, new_tier)
                        new_fruit.merge_cooldown = MERGE_COOLDOWN
                        
                        # Conservation of momentum (roughly)
                        new_fruit.vel = (f1.vel * f1.mass + f2.vel * f2.mass) / new_fruit.mass
                        game_state['new_fruits'].append(new_fruit)
                        
                        # Juice effects
                        game_state['score'] += FRUITS[new_tier][4]
                        game_state['screen_shake'] = min(20, (new_tier + 1) * 3)
                        for _ in range(15):
                            particles.append(Particle(new_pos.x, new_pos.y, FRUITS[new_tier][1]))
                        continue

                    # Collision Resolution (Position correction to prevent sinking)
                    if dist == 0:
                        diff = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                        dist = diff.length()
                    
                    overlap = min_dist - dist
                    direction = diff / dist

                    # Push apart based on mass ratio
                    total_mass = f1.mass + f2.mass
                    ratio1 = f2.mass / total_mass
                    ratio2 = f1.mass / total_mass

                    f1.pos += direction * (overlap * ratio1)
                    f2.pos -= direction * (overlap * ratio2)

                    # Velocity resolution (Bounce)
                    rel_vel = f1.vel - f2.vel
                    vel_along_normal = rel_vel.dot(direction)

                    if vel_along_normal < 0:
                        # Calculate restitution (bounciness)
                        e = RESTITUTION
                        j_impulse = -(1 + e) * vel_along_normal
                        j_impulse /= (1 / f1.mass + 1 / f2.mass)

                        impulse = direction * j_impulse
                        f1.vel += impulse / f1.mass
                        f2.vel -= impulse / f2.mass

def main(*args):
    # If THE CABINET passes the master screen surface, use it. 
    # Otherwise, create a new window for standalone testing.
    if args and isinstance(args[0], pygame.Surface):
        screen = args[0]
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
    pygame.display.set_caption("Fruit Merge")
    clock = pygame.time.Clock()

    # --- Setup Music ---
    try:
        # Dynamically build path: game.py -> fruit_merge dir -> games dir -> root dir -> music dir
        try:
            game_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(game_dir))
            music_path = os.path.join(root_dir, "music", "fruit_merge.mp3")
        except NameError:
            # Fallback if __file__ is undefined (e.g. loaded via exec() directly from root)
            music_path = os.path.join("music", "fruit_merge.mp3")
            
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1) # Loop indefinitely
        else:
            print(f"Notice: Soundtrack not found at {music_path}")
    except Exception as e:
        print(f"Error loading soundtrack: {e}")

    fruits = []
    particles = []
    
    # Next fruit queue (tiers 0 to 3)
    next_fruit_tier = random.randint(0, 3)
    current_tier = random.randint(0, 3)
    
    player_x = WIDTH // 2
    
    game_state = {
        'score': 0,
        'new_fruits': [],
        'screen_shake': 0,
        'game_over': False,
        'game_over_timer': 0
    }

    drop_cooldown = 0
    running = True

    while running:
        dt = clock.tick(FPS)
        
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game_state['game_over'] and event.key == pygame.K_RETURN:
                    pygame.mixer.music.stop() # Reset music for next run
                    main(*args) # Restart, pass args back in case of custom screen
                    return

        keys = pygame.key.get_pressed()
        
        if not game_state['game_over']:
            # Move Launcher
            speed = 6
            if keys[pygame.K_LEFT]:
                player_x -= speed
            if keys[pygame.K_RIGHT]:
                player_x += speed
                
            # Clamp player to container bounds
            current_radius = FRUITS[current_tier][2]
            player_x = max(CONTAINER_LEFT + current_radius, min(player_x, CONTAINER_RIGHT - current_radius))

            # Drop Fruit
            if keys[pygame.K_SPACE] or keys[pygame.K_DOWN]:
                if drop_cooldown <= 0:
                    new_drop = Fruit(player_x, 100, current_tier)
                    new_drop.active = True
                    fruits.append(new_drop)
                    
                    # Cycle queue
                    current_tier = next_fruit_tier
                    next_fruit_tier = random.randint(0, 3)
                    drop_cooldown = 45 # Prevent spamming

        if drop_cooldown > 0:
            drop_cooldown -= 1

        # --- Physics Update ---
        for fruit in fruits:
            fruit.update()

        resolve_collisions(fruits, particles, game_state)

        # Apply merged fruits and clean up
        fruits.extend(game_state['new_fruits'])
        game_state['new_fruits'].clear()
        fruits = [f for f in fruits if not f.marked_for_deletion]

        # Update particles
        for p in particles:
            p.update()
        particles = [p for p in particles if p.life > 0]

        # Check Game Over condition
        highest_point = HEIGHT
        for fruit in fruits:
            if fruit.active and fruit.pos.y - fruit.radius < highest_point:
                highest_point = fruit.pos.y - fruit.radius

        if highest_point < WARNING_LINE and drop_cooldown == 0:
            game_state['game_over_timer'] += 1
            if game_state['game_over_timer'] > FPS * 2: # 2 seconds over the line
                game_state['game_over'] = True
        else:
            game_state['game_over_timer'] = max(0, game_state['game_over_timer'] - 2)

        # --- Rendering ---
        screen.fill(BG_COLOR)

        # Screen Shake calculation
        shake_x, shake_y = 0, 0
        if game_state['screen_shake'] > 0:
            shake_intensity = game_state['screen_shake']
            shake_x = random.randint(-shake_intensity, shake_intensity)
            shake_y = random.randint(-shake_intensity, shake_intensity)
            game_state['screen_shake'] -= 1

        # Create main drawing surface to apply camera effects
        render_surf = pygame.Surface((WIDTH, HEIGHT))
        render_surf.fill(BG_COLOR)

        # Draw UI/Environment
        pygame.draw.rect(render_surf, WALL_COLOR, (CONTAINER_LEFT-10, WARNING_LINE, 10, CONTAINER_BOTTOM - WARNING_LINE + 10))
        pygame.draw.rect(render_surf, WALL_COLOR, (CONTAINER_RIGHT, WARNING_LINE, 10, CONTAINER_BOTTOM - WARNING_LINE + 10))
        pygame.draw.rect(render_surf, WALL_COLOR, (CONTAINER_LEFT-10, CONTAINER_BOTTOM, CONTAINER_RIGHT - CONTAINER_LEFT + 20, 10))
        
        # Draw Danger Line (pulses if close to losing)
        pulse = math.sin(pygame.time.get_ticks() / 100.0) * 50 if game_state['game_over_timer'] > 0 else 0
        danger_alpha = 150 + int(pulse)
        line_surf = pygame.Surface((CONTAINER_RIGHT - CONTAINER_LEFT, 4), pygame.SRCALPHA)
        line_surf.fill((*DANGER_COLOR, danger_alpha))
        render_surf.blit(line_surf, (CONTAINER_LEFT, WARNING_LINE))

        # Draw Score & Next Fruit Text
        score_text = ui_font.render(f"Score: {game_state['score']}", True, (50, 50, 50))
        render_surf.blit(score_text, (20, 20))
        
        next_text = ui_font.render("Next:", True, (50, 50, 50))
        render_surf.blit(next_text, (650, 20))
        
        # Draw Next Fruit Preview
        next_color = FRUITS[next_fruit_tier][1]
        next_radius = min(40, FRUITS[next_fruit_tier][2]) # Cap visual size for UI
        pygame.draw.circle(render_surf, next_color, (700, 100), next_radius)
        pygame.draw.circle(render_surf, (255,255,255), (700, 100), next_radius, 2)

        # Draw Player's Holding Fruit
        if not game_state['game_over']:
            # Draw aim line
            pygame.draw.line(render_surf, (200, 200, 200), (player_x, 100), (player_x, CONTAINER_BOTTOM), 2)
            
            p_radius = FRUITS[current_tier][2]
            p_color = FRUITS[current_tier][1]
            pygame.draw.circle(render_surf, p_color, (int(player_x), 100), p_radius)
            pygame.draw.circle(render_surf, (255,255,255), (int(player_x), 100), p_radius, 2)

        # Draw Fruits
        for fruit in fruits:
            fruit.draw(render_surf)

        # Draw Particles
        for p in particles:
            p.draw(render_surf)

        # Draw Game Over Overlay
        if game_state['game_over']:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            render_surf.blit(overlay, (0, 0))
            
            go_text = title_font.render("GAME OVER", True, (255, 100, 100))
            go_rect = go_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            render_surf.blit(go_text, go_rect)
            
            restart_text = ui_font.render("Press ENTER to Restart", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
            render_surf.blit(restart_text, restart_rect)

        # Apply Screen Shake & Blit to screen
        screen.blit(render_surf, (shake_x, shake_y))
        pygame.display.flip()

    # Stop the music before returning to the launcher or quitting
    pygame.mixer.music.stop()

    # Only quit pygame if we are running standalone, otherwise it kills the main launcher
    if not args:
        pygame.quit()

if __name__ == "__main__":
    main()