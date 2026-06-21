import pygame
import sys
import os
import json
import math
import random

def load_config():
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(path):
        save_config({"high_score": 0})
    with open(path, 'r') as f: return json.load(f)

def save_config(config):
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(path, 'w') as f: json.dump(config, f, indent=4)

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

# --- CONSTANTS & CONFIG ---
FPS = 60
ROAD_WIDTH = 2000
SEGMENT_LENGTH = 200
DRAW_DISTANCE = 300
FOV = 100

CHECKPOINTS = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]

class Line:
    def __init__(self, z, index):
        self.x = 0
        self.y = 0
        self.z = z
        self.curve = 0
        
        self.is_checkpoint = (index in CHECKPOINTS)
        self.is_finish_line = (index == CHECKPOINTS[-1])
        
        self.sx = 0
        self.sy = 0
        self.sw = 0
        self.scale = 0
        
    def project(self, cam_x, cam_y, cam_z, screen_w, screen_h, stretch):
        dz = self.z - cam_z
        if dz <= 0: dz = 0.001 
            
        self.scale = FOV / dz
        self.sx = (1 + self.scale * (self.x - cam_x)) * screen_w / 2
        self.sy = (1 - self.scale * ((self.y - cam_y) * stretch)) * screen_h / 2
        self.sw = self.scale * ROAD_WIDTH * screen_w / 2

class Particle:
    def __init__(self, x, y, color, speed_modifier):
        self.x = x
        self.y = y
        self.color = color
        self.life = random.randint(10, 20)
        self.max_life = self.life
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(5, 15) * speed_modifier

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 255)
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (5, 5), 4)
            surf.blit(s, (int(self.x - 5), int(self.y - 5)))

def get_biome_colors(stage, is_checker, i):
    if stage == 1: 
        grass = (10, int(15 + (i%5)*2), 30) if is_checker else (15, int(20 + (i%5)*2), 40)
        road = (40, 40, 45) if is_checker else (45, 45, 50)
        rumble = (200, 200, 200) if is_checker else (255, 0, 50)
    elif stage == 2: 
        grass = (5, 25, int(40 + (i%5)*3)) if is_checker else (10, 30, int(50 + (i%5)*3))
        road = (20, 25, 30) if is_checker else (25, 30, 35)
        rumble = (0, 255, 255) if is_checker else (255, 255, 255)
    elif stage == 3: 
        grass = (int(40 + (i%5)*3), 5, 5) if is_checker else (int(50 + (i%5)*3), 10, 10)
        road = (15, 10, 10) if is_checker else (20, 15, 15)
        rumble = (255, 200, 0) if is_checker else (255, 50, 50)
    else: 
        h = (pygame.time.get_ticks() // 10) % 255
        grass = (h, 20, 255-h) if is_checker else (255-h, 20, h)
        road = (10, 10, 15) if is_checker else (15, 15, 20)
        rumble = (0, 255, 0) if is_checker else (255, 0, 255)
    return grass, road, rumble

def main(screen):
    pygame.mixer.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks: joy.init()

    play_sound("racing.mp3", loop=-1, volume=0.5)

    WIDTH, HEIGHT = screen.get_size()
    pygame.display.set_caption("Cyber Horizon")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier New", 28, bold=True)
    title_font = pygame.font.SysFont("Impact", 60, italic=True)
    hud_font = pygame.font.SysFont("Impact", 35, italic=True)
    
    config = load_config()
    high_score = config.get("high_score", 0)

    lines = []
    track_length = 8500 
    for i in range(track_length):
        l = Line(i * SEGMENT_LENGTH, i)
        if 300 < i % 1000 < 600: l.curve = 0.5
        elif 700 < i % 1000 < 900: l.curve = -0.5
        if i > 2000 and 100 < i % 600 < 300: l.curve = 1.2 * math.sin(i / 30.0)
        lines.append(l)

    game_state = "PLAYING"
    pos_z, cam_x, speed = 0, 0, 0
    max_speed, base_max = 300, 300
    accel, decel = 2.0, 4.0
    
    time_left = 60.0
    score, current_stage, next_cp_idx = 0, 1, 0
    checkpoint_banner_timer, flash_alpha = 0, 0
    
    is_nitrous = False
    nitrous_fuel = 100.0
    camera_tilt, screen_stretch = 0.0, 1.0 
    particles, shake_timer = [], 0
    
    car_y, car_width, car_height = HEIGHT - 150, 160, 80

    running = True
    while running:
        dt = clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif game_state in ["GAME_OVER", "VICTORY"] and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                pos_z, cam_x, speed, score, current_stage, next_cp_idx = 0, 0, 0, 0, 1, 0
                time_left, nitrous_fuel, game_state = 60.0, 100.0, "PLAYING"

        keys = pygame.key.get_pressed()
        controls = {"left": keys[pygame.K_LEFT] or keys[pygame.K_a],
                    "right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
                    "accel": keys[pygame.K_UP] or keys[pygame.K_w],
                    "brake": keys[pygame.K_DOWN] or keys[pygame.K_s],
                    "boost": keys[pygame.K_SPACE]}
                    
        if joysticks:
            joy = joysticks[0]
            if joy.get_axis(0) < -0.3: controls["left"] = True
            if joy.get_axis(0) > 0.3: controls["right"] = True
            if joy.get_button(0) or joy.get_axis(5) > 0.5: controls["accel"] = True
            if joy.get_button(2) or joy.get_axis(4) > 0.5: controls["brake"] = True
            if joy.get_button(5): controls["boost"] = True

        if game_state == "PLAYING":
            is_nitrous = False
            max_speed = base_max
            if controls["boost"] and nitrous_fuel > 0 and speed > 100:
                is_nitrous = True
                max_speed, accel = 500, 5.0
                nitrous_fuel -= 0.5
                screen_stretch += (0.8 - screen_stretch) * 0.1
            else:
                accel = 2.0
                screen_stretch += (1.0 - screen_stretch) * 0.1
                if nitrous_fuel < 100: nitrous_fuel += 0.1 

            if controls["accel"]:
                speed = min(speed + accel, max_speed)
            elif controls["brake"]:
                speed = max(0, speed - decel * 2)
            else:
                speed = max(0, speed - decel)

            pos_z += speed
            if pos_z >= (track_length - DRAW_DISTANCE) * SEGMENT_LENGTH:
                pos_z = (track_length - DRAW_DISTANCE) * SEGMENT_LENGTH
                speed = 0

            start_pos = int(pos_z / SEGMENT_LENGTH)

            if next_cp_idx < len(CHECKPOINTS) and start_pos >= CHECKPOINTS[next_cp_idx]:
                next_cp_idx += 1
                time_left += 20.0 
                score += 1000 * next_cp_idx
                play_sound("launch.mp3", volume=0.8)
                checkpoint_banner_timer, flash_alpha, shake_timer = 120, 255, 15
                
                if next_cp_idx % 2 == 0 and current_stage < 4:
                    current_stage += 1
                if next_cp_idx == len(CHECKPOINTS):
                    game_state = "VICTORY"
                    play_sound("launch.mp3", volume=1.0)
                    score += int(time_left * 100) 
                    if score > high_score:
                        save_config({"high_score": score})

            current_curve = lines[start_pos % len(lines)].curve
            centrifugal = (speed / base_max) * current_curve * 1.5
            cam_x -= centrifugal

            steer = -4.0 if controls["left"] else 4.0 if controls["right"] else 0
            cam_x += steer * (speed / base_max)

            camera_tilt += ((steer + centrifugal) * 2.5 - camera_tilt) * 0.1
            speed_ratio = speed / base_max

            if is_nitrous:
                particles.append(Particle(WIDTH//2 - car_width//2 + 20, car_y + car_height, (0, 255, 255), speed_ratio * 1.5))
                particles.append(Particle(WIDTH//2 + car_width//2 - 20, car_y + car_height, (255, 0, 255), speed_ratio * 1.5))
            elif speed > 10 and random.random() < 0.3:
                particles.append(Particle(WIDTH//2 - car_width//3, car_y + car_height, (150, 150, 150), speed_ratio))
                particles.append(Particle(WIDTH//2 + car_width//3, car_y + car_height, (150, 150, 150), speed_ratio))

            time_left -= dt / 1000.0
            if time_left <= 0:
                time_left, game_state = 0, "GAME_OVER"
                play_sound("exit.mp3")
                if score > high_score:
                    save_config({"high_score": score})

            score += int(speed * 0.05)

        for p in particles[:]:
            p.update()
            if p.life <= 0: particles.remove(p)

        # --- RENDERING PIPELINE ---
        bg_col = (10, 5, 20) if current_stage == 1 else (5, 15, 25) if current_stage == 2 else (20, 5, 5) if current_stage == 3 else (0, 0, 0)
        screen.fill(bg_col)
        
        horizon_y = HEIGHT // 2 * screen_stretch
        sun_y = int(horizon_y - 120)
        sun_core = (255, 200, 50, 255) if current_stage != 3 else (255, 50, 50, 255)
        sun_glow = (255, 50, 150, 100) if current_stage != 2 else (50, 200, 255, 100)
        
        sun_surf = pygame.Surface((240, 240), pygame.SRCALPHA)
        pygame.draw.circle(sun_surf, sun_glow, (120, 120), 120)
        pygame.draw.circle(sun_surf, sun_core, (120, 120), 100)
        screen.blit(sun_surf, (WIDTH//2 - 120, sun_y - 120))
        
        for i in range(8): pygame.draw.rect(screen, bg_col, (WIDTH//2 - 120, sun_y + i * 15, 240, i * 2))

        dx, curve_acc, cam_y, max_y = 0, 0, 1500, HEIGHT
        ox = random.randint(-6, 6) if shake_timer > 0 else 0
        oy = random.randint(-6, 6) if shake_timer > 0 else 0
        if shake_timer > 0: shake_timer -= 1

        visible_scenery = [] # Pass 2 Rendering Buffer

        # PASS 1: Floor Rendering (Front to Back)
        for i in range(DRAW_DISTANCE):
            if start_pos + i >= len(lines): break
            l = lines[start_pos + i]
            curve_acc += l.curve
            dx += curve_acc
            l.x = cam_x - dx 
            
            l.project(0, cam_y, pos_z, WIDTH, HEIGHT, screen_stretch)
            
            if l.sy >= max_y: continue
            max_y = l.sy
            
            if l.is_checkpoint: visible_scenery.append(l)
            
            if i == 0: continue
            p = lines[start_pos + i - 1]

            is_checker = (i // 3) % 2
            grass_col, road_col, rumble_col = get_biome_colors(current_stage, is_checker, i)
            
            pygame.draw.rect(screen, grass_col, (0, int(p.sy + oy), WIDTH, int(l.sy - p.sy + 2)))
            
            p1, p2 = (p.sx - p.sw + ox, p.sy + oy), (p.sx + p.sw + ox, p.sy + oy)
            p3, p4 = (l.sx + l.sw + ox, l.sy + oy), (l.sx - l.sw + ox, l.sy + oy)
            r1, r2 = (p.sx - p.sw * 1.2 + ox, p.sy + oy), (p.sx + p.sw * 1.2 + ox, p.sy + oy)
            r3, r4 = (l.sx + l.sw * 1.2 + ox, l.sy + oy), (l.sx - l.sw * 1.2 + ox, l.sy + oy)
            
            pygame.draw.polygon(screen, rumble_col, [r1, p1, p4, r4])
            pygame.draw.polygon(screen, rumble_col, [p2, r2, r3, p3])
            pygame.draw.polygon(screen, road_col, [p1, p2, p3, p4])
            
            if (i // 4) % 2 == 0:
                pygame.draw.line(screen, (0, 255, 255), (int((p.sx + p2[0]) / 2), int(p.sy + oy)), (int((l.sx + p3[0]) / 2), int(l.sy + oy)), int(max(1, p.sw * 0.05)))

        # PASS 2: Scenery Rendering (Back to Front)
        for l in reversed(visible_scenery):
            arch_w = int(max(6, l.sw * 0.20))
            arch_h = int(3500 * l.scale) 
            
            core_col = (255, 255, 0) if not l.is_finish_line else (0, 255, 255)
            border_col = (0, 0, 0)
            
            left_x = l.sx - l.sw * 1.4 + ox
            right_x = l.sx + l.sw * 1.4 - arch_w + ox
            y_top = l.sy - arch_h + oy
            
            # Outer Glow
            pygame.draw.rect(screen, (150, 150, 0), (left_x - 4, y_top - 4, arch_w + 8, arch_h + 8))
            pygame.draw.rect(screen, (150, 150, 0), (right_x - 4, y_top - 4, arch_w + 8, arch_h + 8))
            pygame.draw.rect(screen, (150, 150, 0), (left_x - 4, y_top - 4, l.sw * 2.8 + 8, arch_w * 2 + 8))
            
            # Solid Core
            pygame.draw.rect(screen, core_col, (left_x, y_top, arch_w, arch_h))
            pygame.draw.rect(screen, core_col, (right_x, y_top, arch_w, arch_h))
            pygame.draw.rect(screen, core_col, (left_x, y_top, l.sw * 2.8, arch_w * 2))
            
            # Borders
            pygame.draw.rect(screen, border_col, (left_x, y_top, arch_w, arch_h), 2)
            pygame.draw.rect(screen, border_col, (right_x, y_top, arch_w, arch_h), 2)
            pygame.draw.rect(screen, border_col, (left_x, y_top, l.sw * 2.8, arch_w * 2), 2)
            
            # Hazard Stripes
            stripes = 5
            for s_idx in range(stripes):
                sx_pos = left_x + (l.sw * 2.8 / stripes) * s_idx
                pygame.draw.polygon(screen, border_col, [(sx_pos + 10, y_top), (sx_pos + 30, y_top), (sx_pos + 20, y_top + arch_w * 2), (sx_pos, y_top + arch_w * 2)])

        # 3. Draw Player Car
        car_surf = pygame.Surface((car_width, car_height), pygame.SRCALPHA)
        pygame.draw.polygon(car_surf, (20, 20, 25), [(10, car_height), (40, 20), (car_width-40, 20), (car_width-10, car_height)])
        pygame.draw.polygon(car_surf, (0, 255, 255), [(10, car_height), (40, 20), (car_width-40, 20), (car_width-10, car_height)], 3)
        tail_c = (255, 255, 255) if is_nitrous else (255, 50, 50)
        pygame.draw.rect(car_surf, tail_c, (20, car_height-20, 30, 10), border_radius=4)
        pygame.draw.rect(car_surf, tail_c, (car_width-50, car_height-20, 30, 10), border_radius=4)

        rotated_car = pygame.transform.rotate(car_surf, camera_tilt)
        rx = WIDTH//2 - rotated_car.get_width()//2 + ox
        ry = car_y - rotated_car.get_height()//2 + oy
        screen.blit(rotated_car, (int(rx), int(ry)))

        for p in particles: p.draw(screen)

        if flash_alpha > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(flash_alpha)
            screen.blit(flash_surf, (0, 0))
            flash_alpha = max(0, flash_alpha - 10)

        # --- UI LAYOUT ---
        pygame.draw.rect(screen, (0, 50, 100), (20, HEIGHT - 40, 200, 20), border_radius=4)
        bar_col = (0, 255, 255) if not is_nitrous else (255, 0, 255)
        pygame.draw.rect(screen, bar_col, (20, HEIGHT - 40, max(0, int(200 * (speed / 500.0))), 20), border_radius=4)
        screen.blit(font.render(f"{int(speed)} KM/H", True, (255, 255, 255)), (20, HEIGHT - 75))
        
        pygame.draw.rect(screen, (50, 10, 30), (20, HEIGHT - 100, 150, 10), border_radius=2)
        pygame.draw.rect(screen, (255, 50, 150), (20, HEIGHT - 100, int(150 * (nitrous_fuel / 100.0)), 10), border_radius=2)
        screen.blit(pygame.font.SysFont("Courier New", 14, bold=True).render("N2O READY [SPACE/RB]" if nitrous_fuel > 20 else "N2O RECHARGING", True, (255, 100, 200)), (20, HEIGHT - 120))

        ui_stage = hud_font.render(f"STAGE {current_stage}/4", True, (0, 255, 255))
        ui_time = title_font.render(f"{int(time_left)}", True, (255, 255, 255) if time_left > 10 else (255, 50, 50))
        ui_score = font.render(f"SCORE: {score}", True, (255, 255, 255))
        
        screen.blit(ui_stage, (WIDTH//2 - ui_stage.get_width()//2, 10))
        screen.blit(ui_time, (WIDTH//2 - ui_time.get_width()//2, 50))
        screen.blit(ui_score, (20, 20))

        if checkpoint_banner_timer > 0:
            checkpoint_banner_timer -= 1
            cp_txt = title_font.render("CHECKPOINT CLEARED! +20s", True, (0, 255, 150))
            screen.blit(cp_txt, (WIDTH//2 - cp_txt.get_width()//2, HEIGHT//3))

        # --- END STATES ---
        if game_state in ["GAME_OVER", "VICTORY"]:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 5, 20, 200))
            screen.blit(overlay, (0, 0))
            
            go = title_font.render("HORIZON REACHED!" if game_state == "VICTORY" else "TIME EXPIRED", True, (0, 255, 150) if game_state == "VICTORY" else (255, 50, 100))
            sc = font.render(f"FINAL SCORE: {score}", True, (0, 255, 255))
            rst = font.render("PRESS ENTER TO RESTART", True, (255, 255, 255))
            
            screen.blit(go, (WIDTH//2 - go.get_width()//2, HEIGHT//2 - 60))
            screen.blit(sc, (WIDTH//2 - sc.get_width()//2, HEIGHT//2 + 20))
            screen.blit(rst, (WIDTH//2 - rst.get_width()//2, HEIGHT//2 + 80))

        pygame.display.flip()

if __name__ == "__main__":
    pygame.init()
    main(pygame.display.set_mode((1000, 650), pygame.RESIZABLE))