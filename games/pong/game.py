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
        # Navigate up from games/pong/game.py to the root /music/ directory
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

MODES = {
    "BitGame": {"bg": (10, 10, 20), "p1": (0, 255, 255), "p2": (255, 0, 127), "ball": (255, 255, 255), "particles": True, "accel": 1.08, "time_limit": None, "snowball": False, "font": "Courier New"},
    "Classic": {"bg": (0, 0, 0), "p1": (255, 255, 255), "p2": (255, 255, 255), "ball": (255, 255, 255), "particles": False, "accel": 1.05, "time_limit": None, "snowball": False, "font": "Arial"},
    "Snowball": {"bg": (20, 25, 30), "p1": (200, 200, 200), "p2": (100, 100, 100), "ball": (255, 255, 255), "particles": True, "accel": 1.08, "time_limit": None, "snowball": True, "font": "Courier New"},
    "XDistopia": {"bg": (5, 15, 5), "p1": (0, 255, 0), "p2": (0, 150, 0), "ball": (0, 255, 0), "particles": False, "accel": 1.08, "time_limit": None, "snowball": False, "font": "Consolas"},
    "Time Attack": {"bg": (20, 20, 10), "p1": (255, 255, 0), "p2": (255, 150, 0), "ball": (255, 255, 255), "particles": True, "accel": 1.08, "time_limit": 30.0, "snowball": False, "font": "Courier New"},
    "Acceleration": {"bg": (25, 10, 10), "p1": (255, 50, 50), "p2": (150, 0, 0), "ball": (255, 255, 255), "particles": True, "accel": 1.40, "time_limit": None, "snowball": False, "font": "Courier New"}
}

def main(screen):
    # Ensure mixer is initialized and play the Pong soundtrack
    pygame.mixer.init()
    play_sound("pong.mp3", loop=-1, volume=0.5)

    width, height = screen.get_size()
    pygame.display.set_caption("Omni-Pong")
    clock = pygame.time.Clock()
    
    canvas = pygame.Surface((width, height))
    config = load_config()
    
    if "high_scores" not in config:
        config["high_scores"] = {mode: config.get("high_score", 0) for mode in MODES.keys()}
        save_config(config)

    mode_names = list(MODES.keys())
    current_mode_idx = 0
    state = "MENU" # MENU, WARNING, or PLAYING

    # Game Objects
    player = pygame.Rect(30, height//2 - 65, 15, 130)
    ai = pygame.Rect(width - 45, height//2 - 65, 15, 130)
    ball = pygame.Rect(width//2 - 8, height//2 - 8, 16, 16)

    # State variables
    initial_ball_speed = 4
    ball_speed_x = initial_ball_speed
    ball_speed_y = initial_ball_speed
    player_speed = 0
    rally = 0
    max_rally = 0 # Tracks peak score before flashbang deductions
    time_left = 0
    particles = []
    impact_effects = []
    
    # COLLISIONBREAK Setup
    collisionbreak_unlocked = config["high_scores"].get("BitGame", 0) >= 100
    collisionbreak_active = False
    shake_timer = 0
    
    # Flashbang Setup
    flashbang_timer = 0
    flashbang_alpha = 0
    
    # Snowball variables
    snowball_active = False
    snowball_rect = pygame.Rect(0, 0, 12, 12)
    snowball_timer = 0

    running = True
    game_over = False
    win_message = ""

    def reset_game(active_mode):
        nonlocal rally, max_rally, ball_speed_x, ball_speed_y, game_over, particles, impact_effects, time_left, snowball_active, shake_timer, flashbang_timer, flashbang_alpha, win_message
        game_over = False
        win_message = ""
        rally = 0
        max_rally = 0
        shake_timer = 0
        flashbang_timer = 0
        flashbang_alpha = 0
        ball.center = (width//2, height//2)
        ball_speed_x = initial_ball_speed * random.choice((1, -1))
        ball_speed_y = initial_ball_speed * random.choice((1, -1))
        particles.clear()
        impact_effects.clear()
        snowball_active = False
        if MODES[active_mode]["time_limit"]:
            time_left = MODES[active_mode]["time_limit"]

    def spawn_impact(mode, x, y):
        nonlocal shake_timer
        
        if collisionbreak_active:
            shake_timer = 15 
            for _ in range(400):
                particles.append({
                    "pos": [x, y],
                    "vel": [random.uniform(-15, 15), random.uniform(-15, 15)],
                    "life": random.uniform(10, 40),
                    "color": random.choice([(0, 255, 255), (255, 0, 127), (255, 255, 255)])
                })
        
        if mode == "XDistopia":
            for _ in range(6):
                impact_effects.append({
                    "type": "text", "text": random.choice(["0", "1", "ERR", "0xFF", "SYS"]),
                    "x": x, "y": y + random.randint(-30, 30),
                    "vx": random.uniform(2, 6), "vy": random.uniform(-2, 2),
                    "life": 30, "max_life": 30, "color": (0, random.randint(150, 255), 0)
                })
        elif mode == "Snowball":
            for _ in range(15):
                impact_effects.append({
                    "type": "snow",
                    "x": x, "y": y + random.randint(-10, 10),
                    "vx": random.uniform(3, 8), "vy": random.uniform(-5, 5),
                    "life": 40, "max_life": 40,
                    "radius": random.uniform(3, 7),
                    "color": random.choice([(255, 255, 255), (200, 230, 255), (150, 200, 255)])
                })

    while running:
        dt = clock.tick(60)
        mode = mode_names[current_mode_idx]
        theme = MODES[mode]
        high_score = config["high_scores"].get(mode, 0)
        
        font = pygame.font.SysFont(theme["font"], 36, bold=True)
        small_font = pygame.font.SysFont(theme["font"], 18)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                play_sound("exit.mp3")
                pygame.time.wait(200)
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if (mods & pygame.KMOD_ALT) and (mods & pygame.KMOD_SHIFT) and event.key == pygame.K_a:
                    collisionbreak_unlocked = True

                if event.key == pygame.K_ESCAPE:
                    play_sound("exit.mp3")
                    if state == "PLAYING" or state == "WARNING":
                        state = "MENU" 
                    else:
                        pygame.time.wait(200) 
                        running = False 
                
                if state == "MENU":
                    if event.key == pygame.K_LEFT:
                        current_mode_idx = (current_mode_idx - 1) % len(mode_names)
                        collisionbreak_active = False 
                        play_sound("move.mp3")
                    if event.key == pygame.K_RIGHT:
                        current_mode_idx = (current_mode_idx + 1) % len(mode_names)
                        collisionbreak_active = False
                        play_sound("move.mp3")
                    
                    if event.key == pygame.K_UP and mode == "BitGame" and collisionbreak_unlocked:
                        collisionbreak_active = not collisionbreak_active
                        play_sound("move.mp3")

                    if event.key == pygame.K_RETURN:
                        play_sound("launch.mp3")
                        if collisionbreak_active:
                            state = "WARNING"
                        else:
                            state = "PLAYING"
                            reset_game(mode)

                elif state == "WARNING":
                    if event.key == pygame.K_RETURN:
                        play_sound("launch.mp3")
                        state = "PLAYING"
                        reset_game(mode)
                
                elif state == "PLAYING":
                    if event.key == pygame.K_UP: player_speed = -10
                    if event.key == pygame.K_DOWN: player_speed = 10
                    
                    # FLASHBANG Mechanic 
                    if event.key == pygame.K_a and collisionbreak_active and not game_over:
                        if rally >= 5 and flashbang_timer <= 0:
                            rally -= 5
                            flashbang_timer = 180 # 3 seconds of AI confusion
                            flashbang_alpha = 255

                    if event.key == pygame.K_RETURN and game_over:
                        play_sound("launch.mp3")
                        reset_game(mode)

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    player_speed = 0

        canvas.fill(theme["bg"])

        if state == "MENU":
            title = font.render("SELECT PONG MODE", True, (255, 255, 255))
            canvas.blit(title, (width//2 - title.get_width()//2, 150))
            
            mode_display = f"<  {mode.upper()}  >"
            color1 = theme["p1"]
            if collisionbreak_active:
                mode_display = f"<  [COLLISIONBREAK]  >"
                color1 = (255, random.randint(0,255), random.randint(0,255))
                
            mode_text = font.render(mode_display, True, color1)
            canvas.blit(mode_text, (width//2 - mode_text.get_width()//2, 250))
            
            start_txt = small_font.render("PRESS ENTER TO START", True, (150, 150, 150))
            canvas.blit(start_txt, (width//2 - start_txt.get_width()//2, 350))
            
            hi_text = small_font.render(f"{mode.upper()} HIGH SCORE: {high_score}", True, theme["p2"])
            canvas.blit(hi_text, (width//2 - hi_text.get_width()//2, 450))

            if mode == "BitGame":
                if collisionbreak_unlocked:
                    txt = "Press UP to toggle COLLISIONBREAK"
                    color = (255, 50, 50)
                else:
                    txt = "COLLISIONBREAK: LOCKED (Score 100 in BitGame)"
                    color = (100, 100, 100)
                
                stress_txt = small_font.render(txt, True, color)
                canvas.blit(stress_txt, (width//2 - stress_txt.get_width()//2, 500))

        elif state == "WARNING":
            warn_title = font.render("! WARNING: EPILEPSY RISK !", True, (255, 50, 50))
            warn_sub1 = small_font.render("COLLISIONBREAK mode contains intense flashing lights,", True, (255, 255, 255))
            warn_sub2 = small_font.render("extreme screen shake, and visual distortion.", True, (255, 255, 255))
            warn_sub3 = font.render("PRESS ENTER TO ACCEPT", True, (0, 255, 255))
            
            canvas.blit(warn_title, (width//2 - warn_title.get_width()//2, 200))
            canvas.blit(warn_sub1, (width//2 - warn_sub1.get_width()//2, 280))
            canvas.blit(warn_sub2, (width//2 - warn_sub2.get_width()//2, 320))
            canvas.blit(warn_sub3, (width//2 - warn_sub3.get_width()//2, 450))
            
        elif state == "PLAYING":
            keys = pygame.key.get_pressed()
            
            if not game_over:
                if theme["time_limit"]:
                    time_left -= dt / 1000.0
                    if time_left <= 0:
                        time_left = 0
                        game_over = True
                        win_message = "TIME UP! - PRESS ENTER"
                        if max_rally > high_score:
                            config["high_scores"][mode] = max_rally
                            save_config(config)

                if theme["snowball"]:
                    if not snowball_active and random.randint(1, 200) == 1:
                        sx = random.randint(100, width//2 - 50)
                        sy = random.randint(50, height - 50)
                        snowball_rect.center = (sx, sy)
                        snowball_timer = 120 
                        snowball_active = True
                    
                    if snowball_active:
                        snowball_timer -= 1
                        if keys[pygame.K_z] and player.top - 20 <= snowball_rect.centery <= player.bottom + 20:
                            rally += 5
                            max_rally = max(max_rally, rally)
                            snowball_active = False
                        elif snowball_timer <= 0:
                            snowball_active = False

                player.y += player_speed
                player.clamp_ip(canvas.get_rect())

                # Move AI (Affected by Flashbang)
                if collisionbreak_active and flashbang_timer > 0:
                    target_y = ball.centery + random.randint(-300, 300)
                    ai_speed = 1.5 
                    flashbang_timer -= 1
                else:
                    target_y = ball.centery
                    ai_speed = (7.0 if collisionbreak_active else 4.0) + (rally * 0.35)
                
                if ai.centery < target_y: ai.y += min(ai_speed, target_y - ai.centery)
                if ai.centery > target_y: ai.y -= min(ai_speed, ai.centery - target_y)
                ai.clamp_ip(canvas.get_rect())

                ball.x += ball_speed_x
                ball.y += ball_speed_y

                if theme["particles"] and not collisionbreak_active:
                    p_color = theme["p1"] if theme["snowball"] else theme["p2"]
                    particles.append({"pos": [ball.centerx, ball.centery], "vel": [random.uniform(-1, 1), random.uniform(-1, 1)], "life": random.randint(4, 8), "color": p_color})

                if ball.top <= 0 or ball.bottom >= height:
                    ball_speed_y *= -1
                    if collisionbreak_active: shake_timer = 5

                # Paddle Collisions
                if ball.colliderect(player) and ball_speed_x < 0:
                    ball_speed_x *= -theme["accel"]
                    ball_speed_y += 0.5 if ball_speed_y > 0 else -0.5
                    rally += 1
                    max_rally = max(max_rally, rally)
                    spawn_impact(mode, player.right, ball.centery)
                    
                if ball.colliderect(ai) and ball_speed_x > 0:
                    ball_speed_x *= -theme["accel"]
                    ball_speed_y += 0.5 if ball_speed_y > 0 else -0.5
                    if collisionbreak_active: spawn_impact(mode, ai.left, ball.centery)

                # Scoring and Game Over Logic
                if ball.left <= 0:
                    if not theme["time_limit"]: 
                        game_over = True
                        win_message = "AI WINS! - PRESS ENTER"
                        if max_rally > high_score:
                            config["high_scores"][mode] = max_rally
                            save_config(config)
                    else:
                        ball.center = (width//2, height//2)
                        ball_speed_x = initial_ball_speed
                        
                elif ball.right >= width:
                    rally += 5
                    max_rally = max(max_rally, rally)
                    if not theme["time_limit"]:
                        game_over = True
                        win_message = "PLAYER WINS! - PRESS ENTER"
                        if max_rally > high_score:
                            config["high_scores"][mode] = max_rally
                            save_config(config)
                    else:
                        ball.center = (width//2, height//2)
                        ball_speed_x = initial_ball_speed

            # Draw Standard Particles
            for p in particles[:]:
                p["pos"][0] += p["vel"][0]
                p["pos"][1] += p["vel"][1]
                p["life"] -= 0.2 if not collisionbreak_active else 0.5
                
                if collisionbreak_active:
                    rad = int(p["life"])
                    if rad > 0:
                        surf = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (*p["color"], 150), (rad, rad), rad)
                        canvas.blit(surf, (int(p["pos"][0]-rad), int(p["pos"][1]-rad)), special_flags=pygame.BLEND_RGB_ADD)
                else:
                    pygame.draw.circle(canvas, p["color"], (int(p["pos"][0]), int(p["pos"][1])), int(p["life"]))
                    
                if p["life"] <= 0: particles.remove(p)

            if mode != "Classic":
                pygame.draw.aaline(canvas, (70, 70, 90), (width//2, 0), (width//2, height))

            pygame.draw.rect(canvas, theme["p1"], player, border_radius=5)
            pygame.draw.rect(canvas, theme["p2"], ai, border_radius=5)
            pygame.draw.ellipse(canvas, theme["ball"], ball)
            
            if collisionbreak_active:
                for obj, col in [(player, theme["p1"]), (ai, theme["p2"]), (ball, theme["ball"])]:
                    bloom = pygame.Surface((obj.w + 40, obj.h + 40), pygame.SRCALPHA)
                    pygame.draw.rect(bloom, (*col, 50), (20, 20, obj.w, obj.h), border_radius=10)
                    canvas.blit(bloom, (obj.x - 20, obj.y - 20), special_flags=pygame.BLEND_RGB_ADD)

            if theme["snowball"] and snowball_active:
                radius = 6 + (snowball_timer % 10) // 5
                pygame.draw.circle(canvas, (255, 255, 255), snowball_rect.center, radius)
                canvas.blit(small_font.render("[Z]", True, (200,200,200)), (snowball_rect.x - 10, snowball_rect.y - 25))

            for eff in impact_effects[:]:
                eff["x"] += eff["vx"]
                eff["y"] += eff["vy"]
                eff["life"] -= 1
                if eff["life"] <= 0:
                    impact_effects.remove(eff)
                    continue
                
                if eff["type"] == "text":
                    surf = small_font.render(eff["text"], True, eff["color"])
                    canvas.blit(surf, (eff["x"], eff["y"]))
                elif eff["type"] == "snow":
                    current_radius = max(1, int(eff["radius"] * (eff["life"] / eff["max_life"])))
                    pygame.draw.circle(canvas, eff["color"], (int(eff["x"]), int(eff["y"])), current_radius)

            # UI
            score_text = font.render(f"SCORE: {rally}", True, theme["p1"])
            canvas.blit(score_text, (20, 20))
            
            if collisionbreak_active and not game_over:
                fb_color = (0, 255, 255) if rally >= 5 else (100, 100, 100)
                fb_text = small_font.render("Press 'A' for FLASHBANG (Cost: 5 Points)", True, fb_color)
                canvas.blit(fb_text, (20, 60))
            
            if theme["time_limit"]:
                time_text = font.render(f"TIME: {max(0, int(time_left))}", True, (255, 50, 50) if time_left < 10 else theme["p1"])
                canvas.blit(time_text, (width - 200, 20))

            # Flashbang Visual Rendering
            if flashbang_alpha > 0:
                fb_surf = pygame.Surface((width, height))
                fb_surf.fill((255, 255, 255))
                fb_surf.set_alpha(flashbang_alpha)
                canvas.blit(fb_surf, (0, 0))
                flashbang_alpha = max(0, flashbang_alpha - 5)

            # High-Visibility Game Over Rendering
            if game_over:
                text_color = theme["p1"] if "PLAYER" in win_message else theme["p2"]
                
                # Dark dimming overlay for maximum contrast
                dim_surf = pygame.Surface((width, height), pygame.SRCALPHA)
                dim_surf.fill((0, 0, 0, 180))
                canvas.blit(dim_surf, (0, 0))

                go_text = font.render(win_message, True, text_color)
                shadow_text = font.render(win_message, True, (0, 0, 0))
                
                # Dynamic Background Box
                box_w = go_text.get_width() + 60
                box_h = go_text.get_height() + 40
                box_x = width//2 - box_w//2
                box_y = height//2 - box_h//2
                
                pygame.draw.rect(canvas, (20, 20, 25), (box_x, box_y, box_w, box_h), border_radius=8)
                pygame.draw.rect(canvas, text_color, (box_x, box_y, box_w, box_h), width=4, border_radius=8)
                
                # Text Draw
                canvas.blit(shadow_text, (width//2 - shadow_text.get_width()//2 + 3, height//2 - shadow_text.get_height()//2 + 3))
                canvas.blit(go_text, (width//2 - go_text.get_width()//2, height//2 - go_text.get_height()//2))

        # Screen Shake Render Pipeline
        render_x, render_y = 0, 0
        if shake_timer > 0:
            shake_timer -= 1
            render_x = random.randint(-10, 10)
            render_y = random.randint(-10, 10)
            
        screen.blit(canvas, (render_x, render_y))
        pygame.display.flip()