import pygame
import sys
import os
import json
import random
import math

def load_config():
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(path):
        save_config({"high_score": 0})
    with open(path, 'r') as f: return json.load(f)

def save_config(config):
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(path, 'w') as f: json.dump(config, f, indent=4)

# Audio Path Helper
def play_sound(filename, loop=0, volume=1.0):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(base_dir, 'music', filename)
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
        pass

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.life = random.randint(15, 30) 
        self.max_life = self.life
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(1.5, 4.5)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surf, offset_x, offset_y):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 255)
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (3, 3), 3)
            surf.blit(s, (int(self.x - 3 + offset_x), int(self.y - 3 + offset_y)))

def main(screen):
    pygame.mixer.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    play_sound("snake.mp3", loop=-1, volume=0.5)

    WIDTH, HEIGHT = screen.get_size()
    pygame.display.set_caption("Toxic Snake")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier New", 26, bold=True)
    title_font = pygame.font.SysFont("Impact", 45, italic=True)

    config = load_config()
    high_score = config.get("high_score", 0)

    # --- ARCHITECTURE LAYOUT BOUNDARIES ---
    HUD_HEIGHT = 60
    CELL = 25
    cols = WIDTH // CELL
    rows = (HEIGHT - HUD_HEIGHT) // CELL

    # Modes Engine Setup
    MODES = ["BITGAME", "TOXIC MELT", "ZONE CONTAINMENT"]
    selected_mode_idx = 0
    game_state = "MENU" # MENU, PLAYING, GAME_OVER

    # Game State Variables Matrix
    snake = []
    dx, dy = 1, 0
    food = (0, 0)
    obstacles = []
    particles = []
    score = 0
    
    # Mode Mechanics Metrics
    melt_timer = 100.0  # Percentage value for gauge
    containment_level = 0 # How many grid rings contracted inward
    last_containment_tick = 0
    
    # Juice State Matrix
    shake_timer = 0
    last_move = pygame.time.get_ticks()
    move_delay = 100
    joy_moved = False
    joy_menu_moved = False

    def spawn_food(snake_body, obstacle_list, min_col=0, max_col=cols-1, min_row=0, max_row=rows-1):
        # Prevent spawning outside zone constraints if contracted
        min_col = max(0, min_col)
        max_col = min(cols - 1, max_col)
        min_row = max(0, min_row)
        max_row = min(rows - 1, max_row)
        if max_col <= min_col or max_row <= min_row:
            return (cols // 2, rows // 2)
        while True:
            pos = (random.randint(min_col, max_col), random.randint(min_row, max_row))
            if pos not in snake_body and pos not in obstacle_list: return pos

    def start_game():
        nonlocal snake, dx, dy, obstacles, particles, score, move_delay, food, game_state, melt_timer, containment_level, last_containment_tick, last_move
        snake = [(cols//2, rows//2)]
        dx, dy = 1, 0
        obstacles = []
        particles.clear()
        score = 0
        move_delay = 100
        melt_timer = 100.0
        containment_level = 0
        last_containment_tick = pygame.time.get_ticks()
        
        food = spawn_food(snake, obstacles)
        game_state = "PLAYING"
        last_move = pygame.time.get_ticks()

    running = True
    while running:
        now = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()
        p1_controls = {"left": False, "right": False, "up": False, "down": False}
        trigger_select = False
        
        # --- UNIVERSAL EVENT INTERPRETATION ENGINE ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                play_sound("exit.mp3")
                pygame.time.wait(200)
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    if game_state == "PLAYING":
                        game_state = "MENU"
                    else:
                        play_sound("exit.mp3")
                        pygame.time.wait(200)
                        running = False
                if event.key == pygame.K_RETURN:
                    trigger_select = True
                if game_state == "MENU":
                    if event.key in [pygame.K_UP, pygame.K_w]: selected_mode_idx = (selected_mode_idx - 1) % len(MODES)
                    if event.key in [pygame.K_DOWN, pygame.K_s]: selected_mode_idx = (selected_mode_idx + 1) % len(MODES)

        # Polled Controls Matrix
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]: p1_controls["up"] = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: p1_controls["down"] = True
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: p1_controls["left"] = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: p1_controls["right"] = True

        if joysticks:
            joy = joysticks[0]
            if joy.get_axis(0) < -0.5: p1_controls["left"] = True
            if joy.get_axis(0) > 0.5: p1_controls["right"] = True
            if joy.get_axis(1) < -0.5: p1_controls["up"] = True
            if joy.get_axis(1) > 0.5: p1_controls["down"] = True
            if joy.get_numhats() > 0:
                hat = joy.get_hat(0)
                if hat[0] == -1: p1_controls["left"] = True
                if hat[0] == 1: p1_controls["right"] = True
                if hat[1] == 1: p1_controls["up"] = True
                if hat[1] == -1: p1_controls["down"] = True
            if joy.get_button(0): 
                trigger_select = True

        # --- STATE MACHINE CONTROLLERS ---
        if game_state == "MENU":
            if joysticks and not joy_menu_moved:
                if p1_controls["up"]: selected_mode_idx = (selected_mode_idx - 1) % len(MODES); joy_menu_moved = True
                elif p1_controls["down"]: selected_mode_idx = (selected_mode_idx + 1) % len(MODES); joy_menu_moved = True
            elif joysticks and not (p1_controls["up"] or p1_controls["down"]):
                joy_menu_moved = False
                
            if trigger_select:
                play_sound("launch.mp3")
                start_game()

        elif game_state == "GAME_OVER":
            if trigger_select:
                play_sound("launch.mp3")
                start_game()

        elif game_state == "PLAYING":
            active_mode = MODES[selected_mode_idx]
            
            # Safe Orientation Steering Changes
            input_dir_changed = False
            if p1_controls["up"] and dy != 1: dx, dy = 0, -1; input_dir_changed = True
            elif p1_controls["down"] and dy != -1: dx, dy = 0, 1; input_dir_changed = True
            elif p1_controls["left"] and dx != 1: dx, dy = -1, 0; input_dir_changed = True
            elif p1_controls["right"] and dx != -1: dx, dy = 1, 0; input_dir_changed = True
                
            if input_dir_changed and not joy_moved:
                play_sound("move.mp3", volume=0.3)
                joy_moved = True
            elif not (p1_controls["left"] or p1_controls["right"] or p1_controls["up"] or p1_controls["down"]):
                joy_moved = False

            # Mode Overrides Updates: Time Attack Melt calculations
            if active_mode == "TOXIC MELT":
                decay_rate = 0.15 + (score * 0.01) # Melt drains quicker as score scales
                melt_timer -= decay_rate
                if melt_timer <= 0:
                    melt_timer = 0
                    game_state = "GAME_OVER"
                    shake_timer = 30
                    play_sound("exit.mp3")

            # Mode Overrides Updates: Containment shrink evaluations
            if active_mode == "ZONE CONTAINMENT":
                if now - last_containment_tick > 15000: # 15 Seconds
                    last_containment_tick = now
                    containment_level += 1
                    shake_timer = 15
                    play_sound("move.mp3", volume=0.8)
                    # Verify safe food boundary recalculation
                    min_c, max_c = containment_level, cols - 1 - containment_level
                    min_r, max_r = containment_level, rows - 1 - containment_level
                    if food[0] < min_c or food[0] > max_c or food[1] < min_r or food[1] > max_r:
                        food = spawn_food(snake, obstacles, min_c, max_c, min_r, max_r)

            # --- MOTION CLOCK TICK ENGINE ---
            if now - last_move > move_delay:
                last_move = now
                head_x, head_y = snake[0][0] + dx, snake[0][1] + dy
                new_head = (head_x, head_y)

                # Boundary calculations dependent on containment compression factors
                min_col, max_col = 0, cols
                min_row, max_row = 0, rows
                if active_mode == "ZONE CONTAINMENT":
                    min_col += containment_level
                    max_col -= containment_level
                    min_row += containment_level
                    max_row -= containment_level

                if (head_x < min_col or head_x >= max_col or head_y < min_row or head_y >= max_row or 
                    new_head in snake or new_head in obstacles):
                    game_state = "GAME_OVER"
                    shake_timer = 25 
                    play_sound("exit.mp3")
                    if score > high_score:
                        high_score = score
                        config["high_score"] = high_score
                        save_config(config)
                else:
                    snake.insert(0, new_head)
                    if new_head == food:
                        play_sound("launch.mp3", volume=0.6)
                        score += 1
                        shake_timer = 8 
                        
                        # Recharge Melt timer container fully
                        if active_mode == "TOXIC MELT":
                            melt_timer = min(100.0, melt_timer + 35.0)
                        
                        pixel_food_x = food[0] * CELL + CELL // 2
                        pixel_food_y = food[1] * CELL + CELL // 2 + HUD_HEIGHT
                        for _ in range(20):
                            particles.append(Particle(pixel_food_x, pixel_food_y, (50, 255, 50)))
                        
                        move_delay = max(40, 100 - (score * 2))
                        if score % 5 == 0 and active_mode != "ZONE CONTAINMENT":
                            obstacles.append(spawn_food(snake, obstacles))
                        
                        if active_mode == "ZONE CONTAINMENT":
                            food = spawn_food(snake, obstacles, min_col, max_col-1, min_row, max_row-1)
                        else:
                            food = spawn_food(snake, obstacles)
                    else:
                        snake.pop()

        for p in particles[:]:
            p.update()
            if p.life <= 0: particles.remove(p)

        # --- RENDERING ENGINE GRAPHICS PIPELINE ---
        screen.fill((10, 12, 10))
        
        offset_x, offset_y = 0, 0
        if shake_timer > 0:
            offset_x = random.randint(-6, 6)
            offset_y = random.randint(-6, 6)
            shake_timer -= 1

        # Draw Base Field Arena Grid
        for x in range(0, WIDTH, CELL): 
            pygame.draw.line(screen, (18, 22, 18), (x + offset_x, HUD_HEIGHT), (x + offset_x, HEIGHT))
        for y in range(HUD_HEIGHT, HEIGHT, CELL): 
            pygame.draw.line(screen, (18, 22, 18), (offset_x, y + offset_y), (WIDTH + offset_x, y + offset_y))

        # Draw Zone Containment Walls if active mode selected
        if game_state == "PLAYING" and MODES[selected_mode_idx] == "ZONE CONTAINMENT":
            for layer in range(containment_level):
                # Draw top/bottom lines and side segments as warning perimeters
                pygame.draw.rect(screen, (40, 10, 10), (layer*CELL + offset_x, HUD_HEIGHT + layer*CELL + offset_y, WIDTH - (layer*2)*CELL, HEIGHT - HUD_HEIGHT - (layer*2)*CELL), CELL)
                pygame.draw.rect(screen, (200, 40, 40), (layer*CELL + offset_x, HUD_HEIGHT + layer*CELL + offset_y, WIDTH - (layer*2)*CELL, HEIGHT - HUD_HEIGHT - (layer*2)*CELL), 2)

        # Draw Obstacles
        for obs in obstacles:
            ox, oy = obs[0] * CELL + offset_x, obs[1] * CELL + HUD_HEIGHT + offset_y
            pygame.draw.rect(screen, (75, 0, 110), (ox, oy, CELL, CELL), border_radius=4)
            pygame.draw.rect(screen, (170, 0, 255), (ox + 2, oy + 2, CELL - 4, CELL - 4), border_radius=2)

        # Draw Glow-Aura Food Assets
        if game_state == "PLAYING":
            fx, fy = food[0] * CELL + CELL // 2 + offset_x, food[1] * CELL + CELL // 2 + HUD_HEIGHT + offset_y
            for r, alpha in [(20, 30), (14, 60)]:
                glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 50, 50, alpha), (r, r), r)
                screen.blit(glow_surf, (int(fx - r), int(fy - r)))
            pygame.draw.circle(screen, (255, 255, 255), (int(fx), int(fy)), 5)

        # Draw Segmented Entities
        if game_state != "MENU":
            for i, segment in enumerate(snake):
                sx, sy = segment[0] * CELL + offset_x, segment[1] * CELL + HUD_HEIGHT + offset_y
                if i == 0:
                    pygame.draw.rect(screen, (80, 255, 80), (sx, sy, CELL, CELL), border_radius=6)
                    pygame.draw.circle(screen, (255, 255, 255), (int(sx + 12 + dx * 6), int(sy + 12 + dy * 6)), 3)
                else:
                    pygame.draw.rect(screen, (0, 180, 0), (sx + 1, sy + 1, CELL - 2, CELL - 2), border_radius=4)
                    pygame.draw.rect(screen, (0, 130, 0), (sx + 4, sy + 4, CELL - 8, CELL - 4), border_radius=2)

        for p in particles: p.draw(screen, offset_x, offset_y)

        # --- DYNAMIC HUD OVERLAY RIBBON BAR ---
        pygame.draw.rect(screen, (5, 8, 5), (0, 0, WIDTH, HUD_HEIGHT))
        pygame.draw.line(screen, (50, 255, 50), (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT), 2)
        
        if game_state == "PLAYING" and MODES[selected_mode_idx] == "TOXIC MELT":
            # Render radioactive clock indicator decay gauge bar
            gauge_w = 250
            gauge_x = WIDTH // 2 - gauge_w // 2
            pygame.draw.rect(screen, (40, 10, 10), (gauge_x, 22, gauge_w, 16), border_radius=4)
            pygame.draw.rect(screen, (240, 200, 30), (gauge_x, 22, int(gauge_w * (melt_timer / 100.0)), 16), border_radius=4)
            melt_txt = pygame.font.SysFont("Courier New", 12, bold=True).render("MELT GAUGE CORROSION", True, (255, 255, 255))
            screen.blit(melt_txt, (WIDTH // 2 - melt_txt.get_width() // 2, 6))
        else:
            mode_lbl = font.render(MODES[selected_mode_idx] if game_state != "MENU" else "TOXIC SNAKE DIRECTORY", True, (200, 200, 250))
            screen.blit(mode_lbl, (WIDTH // 2 - mode_lbl.get_width() // 2, HUD_HEIGHT // 2 - mode_lbl.get_height() // 2))

        ui_score = font.render(f"SCORE: {score}", True, (255, 255, 255))
        ui_high = font.render(f"HI: {high_score}", True, (50, 255, 50))
        screen.blit(ui_score, (20, HUD_HEIGHT // 2 - ui_score.get_height() // 2))
        screen.blit(ui_high, (WIDTH - ui_high.get_width() - 20, HUD_HEIGHT // 2 - ui_high.get_height() // 2))

        # --- ARCADE OVERLAYS MODALS ---
        if game_state == "MENU":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 10, 5, 220))
            screen.blit(overlay, (0, 0))
            
            title = title_font.render("SELECT TOXIC MUTATION PROFILE", True, (50, 255, 50))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3 - 50))
            
            for i, mode_name in enumerate(MODES):
                is_sel = (i == selected_mode_idx)
                lbl_color = (255, 255, 255) if is_sel else (100, 130, 100)
                prefix = ">> " if is_sel else "   "
                mode_surf = font.render(f"{prefix}{mode_name}", True, lbl_color)
                
                rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//3 + 40 + (i * 50), 400, 40)
                if is_sel:
                    pygame.draw.rect(screen, (20, 50, 20), rect, border_radius=6)
                    pygame.draw.rect(screen, (50, 255, 50), rect, width=2, border_radius=6)
                screen.blit(mode_surf, (rect.x + 20, rect.centery - mode_surf.get_height() // 2))

        elif game_state == "GAME_OVER":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 0, 0, 195))
            screen.blit(overlay, (0, 0))
            
            go_text = font.render("CRASH SEVERE / MATRIX DISSOLVED", True, (255, 50, 50))
            sub_text = font.render("PRESS ENTER/START TO RE-STEER PROFILE", True, (255, 255, 255))
            esc_text = font.render("PRESS ESC TO EXIT TO HUB", True, (150, 150, 150))
            
            screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(sub_text, (WIDTH // 2 - sub_text.get_width() // 2, HEIGHT // 2 + 10))
            screen.blit(esc_text, (WIDTH // 2 - esc_text.get_width() // 2, HEIGHT // 2 + 60))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    pygame.init()
    test_screen = pygame.display.set_mode((1000, 650))
    main(test_screen)