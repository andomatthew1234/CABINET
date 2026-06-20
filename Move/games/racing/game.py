import pygame
import sys
import os
import json
import random

def get_config_path():
    return os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    with open(get_config_path(), 'r') as f: return json.load(f)

def save_config(config):
    with open(get_config_path(), 'w') as f: json.dump(config, f, indent=4)

# Audio Path Helper
def play_sound(filename, loop=0, volume=1.0):
    try:
        # Navigate up from games/racing/game.py to the root /music/ directory
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
        print(f"Audio error for {filename}: {e}")

def main(screen):
    # Ensure mixer is initialized and play the Racing soundtrack
    pygame.mixer.init()
    play_sound("racing.mp3", loop=-1, volume=0.5)

    width, height = screen.get_size()
    pygame.display.set_caption("Neon Racer - Simcade Edition")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier New", 30, bold=True)
    small_font = pygame.font.SysFont("Courier New", 20, bold=True)

    config = load_config()
    high_score = config.get("high_score", 0)

    # Initialize Controller/Wheel
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Colors
    ASPHALT = (30, 30, 35)
    LINE_COLOR = (200, 200, 200)
    PLAYER_COLOR = (0, 255, 255)
    ENEMY_COLORS = [(255, 50, 50), (255, 150, 0), (200, 0, 255), (255, 255, 0)]
    OIL_COLOR = (15, 15, 15)
    BOOST_COLOR = (0, 255, 150)

    # Road Setup
    road_width = 500
    road_x = (width - road_width) // 2
    lane_width = road_width // 4

    # Player Setup
    car_w, car_h = 40, 70
    player_x = road_x + (road_width // 2) - (car_w // 2)
    player_y = height - 120
    base_player_speed = 10
    
    # Game Variables
    base_scroll_speed = 15
    scroll_speed = base_scroll_speed
    lines_y = 0
    score = 0
    enemies = []
    hazards = []
    spawn_timer = 0
    hazard_timer = 100
    
    # Status effects
    night_mode = False
    traction = 1.0
    oil_timer = 0
    boost_timer = 0
    
    running = True
    game_over = False

    while running:
        screen.fill((15, 15, 20))
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                play_sound("exit.mp3")
                pygame.time.wait(200)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    play_sound("exit.mp3")
                    pygame.time.wait(200) 
                    running = False
                if event.key == pygame.K_n and not game_over:
                    night_mode = not night_mode
                if event.key == pygame.K_RETURN and game_over:
                    play_sound("launch.mp3")
                    player_x = road_x + (road_width // 2) - (car_w // 2)
                    enemies.clear()
                    hazards.clear()
                    score = 0
                    scroll_speed = base_scroll_speed
                    traction = 1.0
                    oil_timer = boost_timer = 0
                    game_over = False

        if not game_over:
            # Handle Inputs (Keyboard + Analog)
            steering_input = 0.0
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: steering_input = -1.0
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: steering_input = 1.0
            
            if len(joysticks) > 0:
                joy_x = joysticks[0].get_axis(0)
                if abs(joy_x) > 0.1: steering_input = joy_x

            # Apply Steering with Traction
            player_x += (steering_input * base_player_speed) * traction
            
            # Wall clamp
            if player_x < road_x: player_x = road_x
            if player_x > road_x + road_width - car_w: player_x = road_x + road_width - car_w

            # Status Timers
            if oil_timer > 0:
                oil_timer -= 1
                if oil_timer <= 0: traction = 1.0
            
            # WASD Speed Modifiers
            current_scroll_speed = scroll_speed
            if boost_timer > 0:
                current_scroll_speed = scroll_speed * 2.5 
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                current_scroll_speed = scroll_speed * 1.5
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                current_scroll_speed = scroll_speed * 0.5

            # Speed Scaling
            scroll_speed += 0.02 
            score += int(current_scroll_speed // 5)

            lines_y += current_scroll_speed
            if lines_y >= 60: lines_y -= 60

            # Enemy Spawning (With anti-wall and anti-cheat targeting)
            spawn_timer -= 1
            if spawn_timer <= 0:
                # Track occupied upper lanes to prevent impossible walls
                upper_lanes = set()
                for e in enemies:
                    if e["rect"].y < 250:
                        upper_lanes.add(int((e["rect"].centerx - road_x) // lane_width))

                # 30% chance to target the lane the player is currently in or nearest to
                if random.random() < 0.3:
                    target_lane = int((player_x + car_w/2 - road_x) // lane_width)
                    lane = max(0, min(3, target_lane))
                else:
                    lane = random.randint(0, 3)

                # Impossible Wall Prevention: If 3 lanes are blocked, don't spawn in the 4th
                if len(upper_lanes) >= 3 and lane not in upper_lanes:
                    valid_lanes = list(upper_lanes)
                    if valid_lanes:
                        lane = random.choice(valid_lanes) # Stack behind an existing car

                # Anti-Cheat: Random horizontal offset within the lane
                lane_offset = random.randint(5, lane_width - car_w - 5)
                ex = road_x + (lane * lane_width) + lane_offset
                ey = -car_h
                
                # Check to ensure we don't spawn a car inside another car
                clear = True
                for e in enemies:
                    if e["rect"].colliderect(pygame.Rect(ex, ey, car_w, car_h + 30)):
                        clear = False

                if clear:
                    e_speed = random.uniform(scroll_speed * 0.3, scroll_speed * 0.9) 
                    enemies.append({"rect": pygame.Rect(ex, ey, car_w, car_h), "speed": e_speed, "color": random.choice(ENEMY_COLORS)})
                
                spawn_timer = max(10, 45 - int(scroll_speed * 1.5)) 

            # Hazard Spawning
            hazard_timer -= 1
            if hazard_timer <= 0:
                lane = random.randint(0, 3)
                hx = road_x + (lane * lane_width) + (lane_width // 2) - 15
                htype = random.choice(["oil", "oil", "boost"])
                hazards.append({"rect": pygame.Rect(hx, -30, 30, 30), "type": htype})
                hazard_timer = random.randint(60, 150)

            player_rect = pygame.Rect(player_x, player_y, car_w, car_h)

            # Hazards Logic
            for h in hazards[:]:
                h["rect"].y += current_scroll_speed
                if h["rect"].y > height:
                    hazards.remove(h)
                elif player_rect.colliderect(h["rect"]):
                    if h["type"] == "oil":
                        traction = 0.2 
                        oil_timer = 90
                    elif h["type"] == "boost":
                        boost_timer = 60
                    hazards.remove(h)

            # Enemy AI & Collision Logic
            for i in range(len(enemies)):
                for j in range(len(enemies)):
                    if i != j:
                        # Prevent enemies from phasing through each other
                        if enemies[i]["rect"].colliderect(enemies[j]["rect"]):
                            if enemies[i]["rect"].y < enemies[j]["rect"].y:
                                enemies[i]["speed"] = max(enemies[i]["speed"], enemies[j]["speed"])
                                enemies[i]["rect"].bottom = enemies[j]["rect"].top - 2

            for e in enemies[:]:
                e["rect"].y += (current_scroll_speed - e["speed"])
                if e["rect"].y > height:
                    enemies.remove(e)
                elif player_rect.colliderect(e["rect"]):
                    if boost_timer > 0:
                        enemies.remove(e)
                        score += 1000
                    else:
                        game_over = True
                        if score > high_score:
                            high_score = score
                            config["high_score"] = high_score
                            save_config(config)

        # --- DRAWING ---
        pygame.draw.rect(screen, ASPHALT, (road_x, 0, road_width, height))
        pygame.draw.line(screen, LINE_COLOR, (road_x, 0), (road_x, height), 5)
        pygame.draw.line(screen, LINE_COLOR, (road_x + road_width, 0), (road_x + road_width, height), 5)

        for i in range(1, 4):
            lx = road_x + (i * lane_width)
            for y in range(int(lines_y) - 60, height, 60):
                pygame.draw.line(screen, (200, 200, 200, 100), (lx, y), (lx, y + 30), 2)

        for h in hazards:
            if h["type"] == "oil":
                pygame.draw.ellipse(screen, OIL_COLOR, h["rect"])
            elif h["type"] == "boost":
                pygame.draw.polygon(screen, BOOST_COLOR, [(h["rect"].left, h["rect"].bottom), (h["rect"].right, h["rect"].bottom), (h["rect"].centerx, h["rect"].top)])

        for e in enemies:
            pygame.draw.rect(screen, e["color"], e["rect"], border_radius=5)

        p_color = PLAYER_COLOR
        if oil_timer > 0 and (oil_timer // 5) % 2 == 0: p_color = (100, 100, 100)
        if boost_timer > 0 and (boost_timer // 3) % 2 == 0: p_color = (255, 255, 255)
        
        pygame.draw.rect(screen, p_color, (player_x, player_y, car_w, car_h), border_radius=5)
        
        if not game_over:
            pygame.draw.polygon(screen, (255, 100, 0), [(player_x + 10, player_y + car_h), (player_x + 30, player_y + car_h), (player_x + 20, player_y + car_h + random.randint(15, 30 + (50 if boost_timer > 0 else 0)))])

        if night_mode:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 230)) 
            
            cone_l = [(player_x, player_y), (player_x - 100, 0), (player_x + 20, 0)]
            cone_r = [(player_x + car_w, player_y), (player_x + car_w - 20, 0), (player_x + car_w + 100, 0)]
            pygame.draw.polygon(overlay, (255, 255, 200, 60), cone_l)
            pygame.draw.polygon(overlay, (255, 255, 200, 60), cone_r)
            
            for e in enemies:
                pygame.draw.circle(overlay, (255, 0, 0, 150), (e["rect"].left + 5, e["rect"].bottom), 8)
                pygame.draw.circle(overlay, (255, 0, 0, 150), (e["rect"].right - 5, e["rect"].bottom), 8)

            screen.blit(overlay, (0,0))

        # UI
        screen.blit(small_font.render(f"SPEED: {int(current_scroll_speed * 10)} MPH", True, (255, 255, 255)), (20, 20))
        screen.blit(font.render(f"SCORE: {score}", True, (0, 255, 255)), (20, 50))
        screen.blit(small_font.render(f"HIGH: {high_score}", True, (150, 150, 150)), (20, 90))
        
        mode_txt = "NIGHT ON (Press 'N')" if night_mode else "NIGHT OFF (Press 'N')"
        screen.blit(small_font.render(mode_txt, True, (100, 100, 150)), (20, 120))

        if game_over:
            go_text = font.render("CRASHED! PRESS ENTER", True, (255, 50, 50))
            screen.blit(go_text, (width//2 - go_text.get_width()//2, height//2))

        pygame.display.flip()