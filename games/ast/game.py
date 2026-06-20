import pygame
import math
import random
import sys
import os

# --- GLOBAL AUDIO HELPER (Fixed Namespace Scope Shadowing) ---
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

def main(screen):
    # System Initialization
    pygame.mixer.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()
        
    play_sound("Astroid.mp3", loop=-1, volume=0.4) 

    WIDTH, HEIGHT = screen.get_size()
    clock = pygame.time.Clock()
    
    BG_COLOR = (5, 5, 12)
    STARS = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 3.0), random.choice([1, 2, 3])] for _ in range(150)]
    
    # --- HELPER CLASSES ---
    class FloatingText:
        def __init__(self, x, y, text, color, size=20):
            self.x, self.y = x, y
            self.text = text
            self.color = color
            self.life = 40
            self.font = pygame.font.SysFont("Impact", size, italic=True)
            self.vy = -2

        def update(self):
            self.y += self.vy
            self.vy *= 0.9
            self.life -= 1

        def draw(self, surf, offset_x, offset_y):
            if self.life > 0:
                txt = self.font.render(self.text, True, self.color)
                txt.set_alpha(int(255 * (self.life / 40)))
                surf.blit(txt, (int(self.x + offset_x - txt.get_width()//2), int(self.y + offset_y)))

    class Shockwave:
        def __init__(self, x, y, color, max_radius=60, speed=5, width=3):
            self.x, self.y = x, y
            self.radius = 5
            self.max_radius = max_radius
            self.speed = speed
            self.color = color
            self.width = width
            self.active = True

        def update(self):
            self.radius += self.speed
            if self.radius >= self.max_radius:
                self.active = False

        def draw(self, surf, offset_x, offset_y):
            if self.active:
                alpha = max(0, 255 - int((self.radius / self.max_radius) * 255))
                s = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (self.max_radius, self.max_radius), int(self.radius), self.width)
                surf.blit(s, (int(self.x - self.max_radius + offset_x), int(self.y - self.max_radius + offset_y)))

    class Detonator:
        def __init__(self, x, y):
            self.x, self.y = x, y
            self.radius = 10
            self.max_radius = 450
            self.active = True
            
        def update(self):
            self.radius += 20  
            if self.radius >= self.max_radius:
                self.active = False
                
        def draw(self, surf, offset_x, offset_y):
            if self.active:
                alpha = max(0, 255 - int((self.radius / self.max_radius) * 255))
                s = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 100, 200, alpha), (self.max_radius, self.max_radius), int(self.radius))
                pygame.draw.circle(s, (255, 255, 255, alpha), (self.max_radius, self.max_radius), int(self.radius), 10)
                surf.blit(s, (int(self.x - self.max_radius + offset_x), int(self.y - self.max_radius + offset_y)))

    class Player:
        def __init__(self):
            self.x, self.y = WIDTH // 2, HEIGHT - 100
            self.speed = 6.0
            self.vx, self.vy = 0, 0
            
            self.health = 100
            self.shield = 100
            self.max_shield = 100
            self.shield_regen = 0.05
            
            self.fire_rate = 12 
            self.damage = 15
            self.bullet_size = 4
            
            self.shoot_timer = 0
            self.score = 0
            
            self.has_mega_explode = False
            self.mega_cooldown = 0
            self.max_mega_cooldown = 600 

        def update(self, controls):
            self.vx, self.vy = 0, 0
            if controls["up"]: 
                self.y -= self.speed; self.vy = -self.speed
            if controls["down"]: 
                self.y += self.speed; self.vy = self.speed
            if controls["left"]: 
                self.x -= self.speed; self.vx = -self.speed
            if controls["right"]: 
                self.x += self.speed; self.vx = self.speed
            
            self.x = max(30, min(WIDTH - 30, self.x))
            self.y = max(HEIGHT - 250, min(HEIGHT - 30, self.y))
            
            if self.shield < self.max_shield: self.shield += self.shield_regen
            if self.shoot_timer > 0: self.shoot_timer -= 1
            if self.mega_cooldown > 0: self.mega_cooldown -= 1

        def draw(self, surf, offset_x, offset_y):
            if self.shield > 0:
                alpha = int((self.shield / self.max_shield) * 100) + 20
                shield_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (0, 200, 255, alpha), (30, 30), 22, 2)
                surf.blit(shield_surf, (int(self.x - 30 + offset_x), int(self.y - 30 + offset_y)))
            
            p1 = (self.x + offset_x, self.y - 20 + offset_y)
            p2 = (self.x - 15 + offset_x, self.y + 15 + offset_y)
            p3 = (self.x + 15 + offset_x, self.y + 15 + offset_y)
            pygame.draw.polygon(surf, (200, 240, 255), [p1, p2, p3])
            pygame.draw.circle(surf, (0, 255, 255), (int(self.x + offset_x), int(self.y + 5 + offset_y)), 5)

    class Bullet:
        def __init__(self, x, y, vy, dmg, radius, color, is_enemy=False):
            self.x, self.y = x, y
            self.vy = vy
            self.dmg = dmg
            self.radius = radius
            self.color = color
            self.is_enemy = is_enemy
            self.life = 120

        def update(self):
            self.y += self.vy
            self.life -= 1

        def draw(self, surf, offset_x, offset_y):
            glow_rad = self.radius * 3
            glow = pygame.Surface((glow_rad * 2, glow_rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color, 100), (glow_rad, glow_rad), glow_rad)
            pygame.draw.circle(glow, (255, 255, 255), (glow_rad, glow_rad), self.radius)
            surf.blit(glow, (int(self.x - glow_rad + offset_x), int(self.y - glow_rad + offset_y)))

    class Enemy:
        def __init__(self, x, y, target_y, hp, form_dir, form_speed, color):
            self.x, self.y = x, y
            self.target_y = target_y 
            self.hp = hp
            self.max_hp = hp
            self.color = color
            self.radius = 18
            self.form_dir = form_dir
            self.form_speed = form_speed
            self.hit_flash = 0

        def draw(self, surf, offset_x, offset_y):
            p1 = (self.x + offset_x, self.y + 15 + offset_y)
            p2 = (self.x - 15 + offset_x, self.y - 15 + offset_y)
            p3 = (self.x + 15 + offset_x, self.y - 15 + offset_y)
            
            draw_col = self.color if self.hit_flash <= 0 else (255, 255, 255)
            pygame.draw.polygon(surf, draw_col, [p1, p2, p3])
            if self.hit_flash > 0: self.hit_flash -= 1

            if self.hp < self.max_hp:
                bar_w = 30
                ratio = self.hp / self.max_hp
                pygame.draw.rect(surf, (150, 0, 0), (self.x - bar_w//2 + offset_x, self.y - 25 + offset_y, bar_w, 4))
                pygame.draw.rect(surf, (0, 255, 100), (self.x - bar_w//2 + offset_x, self.y - 25 + offset_y, bar_w * ratio, 4))

    class Particle:
        def __init__(self, x, y, color, is_thruster=False):
            self.x, self.y = x, y
            self.is_thruster = is_thruster
            if is_thruster:
                self.life = random.randint(10, 20)
                ang = random.uniform(math.pi*0.4, math.pi*0.6)
                spd = random.uniform(2, 5)
            else:
                self.life = random.randint(20, 40)
                ang = random.uniform(0, math.pi * 2)
                spd = random.uniform(2, 12) 
            self.vx = math.cos(ang) * spd
            self.vy = math.sin(ang) * spd
            self.color = color

        def update(self):
            if self.is_thruster:
                self.vx *= 0.9
                self.vy *= 0.9
            else:
                self.vx *= 0.92
                self.vy *= 0.92
            self.x += self.vx
            self.y += self.vy
            self.life -= 1

        def draw(self, surf, offset_x, offset_y):
            max_life = 20 if self.is_thruster else 40
            alpha = int((max(0, self.life) / max_life) * 255)
            c = (*self.color[:3], alpha)
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            rad = 3 if not self.is_thruster else int((self.life/20)*4)
            pygame.draw.circle(s, c, (3, 3), rad)
            surf.blit(s, (self.x - 3 + offset_x, self.y - 3 + offset_y))

    # Initialization Tasks
    def reset_match():
        return Player(), [], [], [], [], [], [], 1, "PLAYING", 0, 0, (0,0)

    player, bullets, enemies, particles, shockwaves, texts, detonators, wave, state, shake_timer, hitstop, death_pos = reset_match()
    state_timer = 0
    menu_index = 0
    joy_moved = False
    
    font = pygame.font.SysFont("Courier New", 20, bold=True)
    title_font = pygame.font.SysFont("Impact", 50, bold=True)
    mega_font = pygame.font.SysFont("Courier New", 12, bold=True)
    
    base_upgrades_pool = [
        {"name": "RAPID FIRE", "desc": "Increases auto-fire speed", "func": lambda: setattr(player, 'fire_rate', max(4, player.fire_rate - 2))},
        {"name": "DAMAGE UP", "desc": "Bullets deal more damage", "func": lambda: setattr(player, 'damage', player.damage + 8)},
        {"name": "CALIBER UP", "desc": "Larger projectile radius", "func": lambda: setattr(player, 'bullet_size', player.bullet_size + 1)},
        {"name": "ENGINE TUNE", "desc": "Increases move speed", "func": lambda: setattr(player, 'speed', player.speed + 1.0)},
        {"name": "SHIELD BOOST", "desc": "Faster shield recharge", "func": lambda: setattr(player, 'shield_regen', player.shield_regen + 0.05)},
    ]
    current_choices = []

    def spawn_wave():
        enemies.clear()
        if wave > 100: return 
        
        troops = min(6, 1 + wave // 2)
        shapes = ['grid', 'v_shape', 'circle', 'x_shape', 'u_shape', 'scatter']
        
        for t in range(troops):
            shape = random.choice(shapes)
            f_dir = random.choice([-1, 1])
            f_spd = random.uniform(1.5, 3.5) + (wave * 0.2)
            f_col = (random.randint(150, 255), random.randint(50, 150), random.randint(50, 255))
            
            start_x = random.randint(200, WIDTH - 200)
            base_y = -100 - (t * 200)
            target_base_y = min(HEIGHT - 350, 50 + (t * 80))
            hp = 15 + (wave * 5)
            
            if shape == 'grid':
                cols, rows = random.randint(4, 8), random.randint(2, 4)
                for r in range(rows):
                    for c in range(cols):
                        enemies.append(Enemy(start_x + (c - cols//2) * 60, base_y + r * 50, target_base_y + r * 50, hp, f_dir, f_spd, f_col))
            elif shape == 'v_shape':
                size = random.randint(4, 7)
                for i in range(size):
                    enemies.append(Enemy(start_x - i*50, base_y - i*50, target_base_y - i*50, hp, f_dir, f_spd, f_col))
                    if i > 0: enemies.append(Enemy(start_x + i*50, base_y - i*50, target_base_y - i*50, hp, f_dir, f_spd, f_col))
            elif shape == 'circle':
                count = random.randint(8, 14)
                rad = random.randint(60, 120)
                for i in range(count):
                    ang = (i/count) * math.pi * 2
                    enemies.append(Enemy(start_x + math.cos(ang)*rad, base_y + math.sin(ang)*rad, target_base_y + math.sin(ang)*rad, hp, f_dir, f_spd, f_col))
            elif shape == 'x_shape':
                size = random.randint(3, 6)
                for i in range(-size, size+1):
                    enemies.append(Enemy(start_x + i*50, base_y + abs(i)*50, target_base_y + abs(i)*50, hp, f_dir, f_spd, f_col))
                    if i != 0: enemies.append(Enemy(start_x - i*50, base_y + abs(i)*50, target_base_y + abs(i)*50, hp, f_dir, f_spd, f_col))
            elif shape == 'u_shape':
                size = random.randint(3, 6)
                for i in range(-size, size+1):
                    oy = (i**2) * 12
                    enemies.append(Enemy(start_x + i*50, base_y + oy, target_base_y + oy, hp, f_dir, f_spd, f_col))
            elif shape == 'scatter':
                count = random.randint(10, 20)
                for _ in range(count):
                    enemies.append(Enemy(start_x + random.randint(-150, 150), base_y + random.randint(-100, 100), target_base_y + random.randint(-100, 100), hp, f_dir, f_spd, f_col))

    def draw_button(surf, text, rect, is_selected):
        bg = (80, 20, 100) if is_selected else (40, 20, 60)
        brd = (0, 255, 100) if is_selected else (255, 0, 255)
        pygame.draw.rect(surf, bg, rect, border_radius=8)
        pygame.draw.rect(surf, brd, rect, width=3, border_radius=8)
        txt = font.render(text, True, (255, 255, 255))
        surf.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    spawn_wave()

    # --- MAIN LOOP ---
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()
        
        btn_play_again = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 20, 300, 60)
        btn_exit = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 100, 300, 60)
        
        trigger_menu_select = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            # MEGA EXPLODE TRIGGER
            if state == "PLAYING":
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                   (event.type == pygame.JOYBUTTONDOWN and event.button in [0, 1, 2, 3, 5]):
                    if player.has_mega_explode and player.mega_cooldown <= 0:
                        detonators.append(Detonator(player.x, player.y))
                        player.mega_cooldown = player.max_mega_cooldown
                        shake_timer = 20
            
            # MENU NAVIGATION
            if state in ["LEVEL_UP", "GAME_OVER", "VICTORY"]:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        menu_index -= 1
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        menu_index += 1
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        trigger_menu_select = True
                
                elif event.type == pygame.JOYHATMOTION:
                    if event.value[1] == 1: menu_index -= 1
                    elif event.value[1] == -1: menu_index += 1
                        
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0: 
                        trigger_menu_select = True
                        
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if state == "LEVEL_UP":
                        base_x = WIDTH // 2 - 300
                        for i, choice in enumerate(current_choices):
                            if pygame.Rect(base_x, 200 + (i * 90), 600, 75).collidepoint(mx, my):
                                menu_index = i
                                trigger_menu_select = True
                    else:
                        if btn_play_again.collidepoint(mx, my): menu_index = 0; trigger_menu_select = True
                        elif btn_exit.collidepoint(mx, my): menu_index = 1; trigger_menu_select = True

        if state == "LEVEL_UP":
            if current_choices:
                if menu_index < 0: menu_index = len(current_choices) - 1
                elif menu_index >= len(current_choices): menu_index = 0
        elif state in ["GAME_OVER", "VICTORY"]:
            if menu_index < 0: menu_index = 1
            elif menu_index > 1: menu_index = 0

        if trigger_menu_select:
            if state == "LEVEL_UP" and current_choices:
                current_choices[menu_index]["func"]()
                wave += 1
                spawn_wave()
                state = "PLAYING"
            elif state in ["GAME_OVER", "VICTORY"]:
                if menu_index == 0: 
                    player, bullets, enemies, particles, shockwaves, texts, detonators, wave, state, shake_timer, hitstop, death_pos = reset_match()
                    spawn_wave()
                elif menu_index == 1: 
                    running = False

        p1_controls = {
            "left": keys[pygame.K_LEFT] or keys[pygame.K_a],
            "right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            "up": keys[pygame.K_UP] or keys[pygame.K_w],
            "down": keys[pygame.K_DOWN] or keys[pygame.K_s]
        }

        if joysticks:
            joy = joysticks[0]
            if joy.get_axis(0) < -0.3: p1_controls["left"] = True
            if joy.get_axis(0) > 0.3: p1_controls["right"] = True
            if joy.get_axis(1) < -0.3: p1_controls["up"] = True
            if joy.get_axis(1) > 0.3: p1_controls["down"] = True
            
            if state in ["LEVEL_UP", "GAME_OVER", "VICTORY"]:
                jy = joy.get_axis(1)
                if jy < -0.6 and not joy_moved:
                    menu_index -= 1; joy_moved = True
                elif jy > 0.6 and not joy_moved:
                    menu_index += 1; joy_moved = True
                elif abs(jy) < 0.2:
                    joy_moved = False

        if hitstop > 0:
            hitstop -= 1
        else:
            for star in STARS:
                star[1] += star[2] * (10 if state == "WIN_CINEMATIC" else 1) 
                if star[1] > HEIGHT:
                    star[1] = 0
                    star[0] = random.randint(0, WIDTH)

            for b in bullets[:]:
                b.update()
                if b.life <= 0 or b.y < -50 or b.y > HEIGHT + 50: bullets.remove(b)

            for p in particles[:]:
                p.update()
                if p.life <= 0: particles.remove(p)
                    
            for sw in shockwaves[:]:
                sw.update()
                if not sw.active: shockwaves.remove(sw)
                    
            for txt in texts[:]:
                txt.update()
                if txt.life <= 0: texts.remove(txt)
                    
            for det in detonators[:]:
                det.update()
                for e in enemies[:]:
                    if math.hypot(det.x - e.x, det.y - e.y) < det.radius:
                        e.hp -= 1000 
                if not det.active: detonators.remove(det)

            # --- PLAYING STATE ---
            if state == "PLAYING":
                player.update(p1_controls)
                
                if player.vy < 0: 
                    particles.append(Particle(player.x + random.uniform(-5, 5), player.y + 15, (0, 255, 255), is_thruster=True))
                elif random.random() < 0.5:
                    particles.append(Particle(player.x + random.uniform(-3, 3), player.y + 15, (0, 150, 200), is_thruster=True))
                
                if player.shoot_timer <= 0:
                    bullets.append(Bullet(player.x, player.y - 15, -18, player.damage, player.bullet_size, (0, 255, 150)))
                    player.shoot_timer = player.fire_rate

                for e in enemies[:]:
                    if e.y < e.target_y: e.y += 6 
                    else: e.y += 0.2 + (wave * 0.05) 

                    e.x += e.form_dir * e.form_speed
                    if e.x > WIDTH - 20: e.form_dir = -1; e.x = WIDTH - 20
                    elif e.x < 20: e.form_dir = 1; e.x = 20
                        
                    if e.y > 0 and random.random() < 0.003 + (wave * 0.001):
                        bullets.append(Bullet(e.x, e.y + 15, random.uniform(6, 10), 15 + wave, 5, (255, 50, 50), is_enemy=True))

                    if math.hypot(player.x - e.x, player.y - e.y) < e.radius + 15:
                        dmg = 30
                        if player.shield > 0:
                            player.shield -= dmg
                            if player.shield < 0: player.health += player.shield; player.shield = 0
                        else: player.health -= dmg
                        shake_timer = 15
                        e.hp = 0

                for b in bullets[:]:
                    if b.is_enemy:
                        if math.hypot(b.x - player.x, b.y - player.y) < b.radius + 15:
                            if player.shield > 0:
                                player.shield -= b.dmg
                                if player.shield < 0: player.health += player.shield; player.shield = 0
                            else: player.health -= b.dmg
                            shake_timer = 10
                            if b in bullets: bullets.remove(b)
                            shockwaves.append(Shockwave(player.x, player.y, (255,50,50), 40, 8, 2))
                    else:
                        for e in enemies[:]:
                            if math.hypot(b.x - e.x, b.y - e.y) < e.radius + b.radius:
                                e.hp -= b.dmg
                                e.hit_flash = 3
                                if b in bullets: bullets.remove(b)
                                for _ in range(3): particles.append(Particle(b.x, b.y, (255, 255, 200)))
                                break

                for e in enemies[:]:
                    if e.hp <= 0:
                        if e in enemies: enemies.remove(e)
                        player.score += 25
                        shake_timer = max(shake_timer, 8)
                        if random.random() < 0.3: hitstop = 1 
                        shockwaves.append(Shockwave(e.x, e.y, e.color, max_radius=80, speed=10, width=4))
                        for _ in range(25): particles.append(Particle(e.x, e.y, e.color))
                        texts.append(FloatingText(e.x, e.y - 10, "+25", (0, 255, 255)))

                if player.health <= 0:
                    state = "LOSE_CINEMATIC"
                    state_timer = 150 
                    shake_timer = 30
                    hitstop = 15
                    death_pos = (player.x, player.y)
                    shockwaves.append(Shockwave(death_pos[0], death_pos[1], (255, 50, 50), 200, 15, 8))
                    for _ in range(50): particles.append(Particle(death_pos[0], death_pos[1], (255, 100, 50)))

                elif len(enemies) == 0:
                    if wave >= 100:
                        state = "WIN_CINEMATIC"
                        state_timer = 240
                        shake_timer = 60
                        bullets.clear()
                    else:
                        shake_timer = 20
                        pool = list(base_upgrades_pool)
                        if not player.has_mega_explode:
                            pool.append({"name": "MEGA EXPLODE (SPACEBAR)", "desc": "Instantly drops a screen-clearing tactical nuke. (10s Cooldown)", "func": lambda: setattr(player, 'has_mega_explode', True)})
                        current_choices = random.sample(pool, min(3, len(pool)))
                        menu_index = 0 
                        state = "LEVEL_UP"

            # --- LOSE CINEMATIC ---
            elif state == "LOSE_CINEMATIC":
                state_timer -= 1
                for e in enemies:
                    ang = math.atan2(death_pos[1] - e.y, death_pos[0] - e.x)
                    e.x += math.cos(ang) * 2.5
                    e.y += math.sin(ang) * 2.5
                if state_timer <= 0:
                    menu_index = 0
                    state = "GAME_OVER"

            # --- WIN CINEMATIC ---
            elif state == "WIN_CINEMATIC":
                state_timer -= 1
                player.vy -= 0.6 
                player.y += player.vy
                particles.append(Particle(player.x + random.uniform(-5, 5), player.y + 15, (0, 255, 255), is_thruster=True))
                
                if random.random() < 0.2:
                    ex, ey = random.randint(0, WIDTH), random.randint(0, HEIGHT)
                    shockwaves.append(Shockwave(ex, ey, (255, random.randint(100,200), 50), max_radius=150, speed=15, width=6))
                    for _ in range(15): particles.append(Particle(ex, ey, (255, 150, 50)))
                    shake_timer = 5
                
                if state_timer <= 0:
                    menu_index = 0
                    state = "VICTORY"

        # --- DRAWING ---
        screen.fill(BG_COLOR)
        
        offset_x, offset_y = 0, 0
        if shake_timer > 0:
            offset_x = random.randint(-8, 8)
            offset_y = random.randint(-8, 8)
            shake_timer -= 1
        
        for sx, sy, spd, sr in STARS:
            pygame.draw.circle(screen, (80, 80, 110), (int(sx + offset_x * 0.2), int(sy + offset_y * 0.2)), sr)

        for p in particles: p.draw(screen, offset_x, offset_y)
        for b in bullets: b.draw(screen, offset_x, offset_y)
        for e in enemies: e.draw(screen, offset_x, offset_y)
        for sw in shockwaves: sw.draw(screen, offset_x, offset_y)
        for det in detonators: det.draw(screen, offset_x, offset_y)
        for txt in texts: txt.draw(screen, offset_x, offset_y)
        
        if state in ["PLAYING", "WIN_CINEMATIC"]:
            player.draw(screen, offset_x, offset_y)
            
        if state in ["PLAYING", "LEVEL_UP", "WIN_CINEMATIC"]:
            pygame.draw.rect(screen, (100, 0, 0), (20, 20, 200, 15))
            pygame.draw.rect(screen, (0, 255, 0), (20, 20, max(0, 200 * (player.health / 100)), 15))
            
            pygame.draw.rect(screen, (0, 50, 100), (20, 40, 200, 10))
            pygame.draw.rect(screen, (0, 200, 255), (20, 40, max(0, 200 * (player.shield / player.max_shield)), 10))
            
            if player.has_mega_explode:
                pygame.draw.rect(screen, (50, 20, 50), (20, 60, 200, 10))
                if player.mega_cooldown <= 0:
                    pygame.draw.rect(screen, (255, 0, 255), (20, 60, 200, 10))
                    ready_txt = mega_font.render("MEGA READY [SPACE]", True, (255, 255, 255))
                    screen.blit(ready_txt, (25, 58))
                else:
                    ratio = 1.0 - (player.mega_cooldown / player.max_mega_cooldown)
                    pygame.draw.rect(screen, (150, 0, 150), (20, 60, max(0, 200 * ratio), 10))
            
            ui_s = font.render(f"SCORE: {player.score}  WAVE: {wave}/100", True, (0, 255, 255))
            screen.blit(ui_s, (WIDTH - ui_s.get_width() - 20, 20))

        if state == "LEVEL_UP":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            t = title_font.render("WAVE CLEARED! SELECT UPGRADE", True, (0, 255, 150))
            screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 80))
            
            menu_w = 650
            base_x = WIDTH // 2 - menu_w // 2
            for i, choice in enumerate(current_choices):
                rect = pygame.Rect(base_x, 200 + (i * 90), menu_w, 75)
                
                is_mega = "MEGA EXPLODE" in choice["name"]
                is_selected = (i == menu_index)
                
                bg_col = (80, 20, 100) if (is_mega and is_selected) else (40, 20, 60) if is_mega else (60, 60, 90) if is_selected else (40, 40, 60)
                brd_col = (255, 0, 255) if is_mega else (0, 255, 100) if is_selected else (100, 100, 150)
                
                pygame.draw.rect(screen, bg_col, rect, border_radius=8)
                pygame.draw.rect(screen, brd_col, rect, width=3, border_radius=8)
                
                name_col = (255, 100, 255) if is_mega else (255, 255, 255)
                name_surf = font.render(choice["name"], True, name_col)
                desc_surf = pygame.font.SysFont("Courier New", 14).render(choice["desc"], True, (200, 200, 200))
                
                screen.blit(name_surf, (rect.x + 20, rect.y + 15))
                screen.blit(desc_surf, (rect.x + 20, rect.y + 45))

        elif state == "GAME_OVER":
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                t = title_font.render("MISSION FAILED", True, (255, 50, 50))
                screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 80))
                
            draw_button(screen, "PLAY AGAIN", btn_play_again, menu_index == 0)
            draw_button(screen, "EXIT TO CABINET", btn_exit, menu_index == 1)

        elif state == "VICTORY":
            t = title_font.render("MISSION SUCCEEDED", True, (0, 255, 150))
            screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 80))
            
            draw_button(screen, "PLAY AGAIN", btn_play_again, menu_index == 0)
            draw_button(screen, "EXIT TO CABINET", btn_exit, menu_index == 1)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    pygame.init()
    test_screen = pygame.display.set_mode((1000, 650))
    main(test_screen)