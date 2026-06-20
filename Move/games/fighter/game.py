import pygame
import sys
import os
import json
import random
import math

def get_config_path():
    return os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    path = get_config_path()
    if not os.path.exists(path):
        save_config({
            "title": "Neon Brawl",
            "description": "2D Hyper-Fighter. Player vs AI.",
            "high_score": 0
        })
    with open(path, 'r') as f: return json.load(f)

def save_config(config):
    with open(get_config_path(), 'w') as f: json.dump(config, f, indent=4)

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

# --- COMBAT DATA ---
# Frame Data (60fps) -> [Startup, Active, Recovery]
MOVESET = {
    "light": {"start": 4, "active": 6, "rec": 10, "dmg": 40, "stun": 15, "push": 8, "stop": 5, "box": (45, 20, 50, 15)},
    "heavy": {"start": 12, "active": 8, "rec": 20, "dmg": 95, "stun": 28, "push": 22, "stop": 10, "box": (40, 50, 50, 40)},
    "special": {"start": 16, "active": 2, "rec": 25, "dmg": 65, "stun": 18, "push": 12, "stop": 6, "box": (0,0,0,0)} 
}

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = 45
        self.font = pygame.font.SysFont("Impact", 30, italic=True)
        
    def update(self):
        self.y -= 2
        self.life -= 1
        
    def draw(self, surface, offset_x, offset_y):
        if self.life > 0:
            txt = self.font.render(self.text, True, self.color)
            txt.set_alpha(int(255 * (self.life / 45)))
            surface.blit(txt, (self.x + offset_x - txt.get_width()//2, self.y + offset_y))

class Spark:
    def __init__(self, x, y, angle, speed, color, life):
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.85 
        self.vy *= 0.85
        self.life -= 1

    def draw(self, surface, offset_x, offset_y):
        if self.life > 0:
            end_x = self.x - self.vx * 2
            end_y = self.y - self.vy * 2
            pygame.draw.line(surface, self.color, (self.x + offset_x, self.y + offset_y), (end_x + offset_x, end_y + offset_y), 3)

class Projectile:
    def __init__(self, x, y, dir, color, owner_id):
        self.x, self.y = x, y
        self.dir = dir
        self.vx = 22 * dir 
        self.color = color
        self.owner = owner_id
        self.rect = pygame.Rect(x, y, 40, 12)
        self.life = 80
        self.active = True

    def update(self):
        self.x += self.vx
        self.rect.x = int(self.x)
        self.life -= 1
        if self.life <= 0: self.active = False

    def draw(self, surface, offset_x, offset_y):
        if self.active:
            core = pygame.Rect(self.rect.x + offset_x, self.rect.y + offset_y, self.rect.w, self.rect.h)
            pygame.draw.rect(surface, (*self.color, 150), core.inflate(20, 10), border_radius=10)
            pygame.draw.rect(surface, (255, 255, 255), core, border_radius=5)

class Fighter:
    def __init__(self, x, y, color, is_ai=False):
        self.x, self.y = x, y
        self.vx, self.vy = 0, 0
        self.w, self.h = 60, 140 
        self.color = color
        self.dir = 1 
        self.is_ai = is_ai
        
        self.max_hp = 1000
        self.hp = 1000
        self.speed = 8.5    
        self.jump_power = -22 
        self.stun_duration = 0
        
        self.state = "idle" 
        self.timer = 0
        self.block_timer = 0 # Tracks precise frames for Just Defend parries
        self.current_attack = None
        self.active_hitbox = None
        self.has_hit = False 
        
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def change_state(self, new_state):
        self.state = new_state
        self.timer = 0
        self.active_hitbox = None
        self.has_hit = False
        if new_state != "attack":
            self.current_attack = None

    def attack(self, attack_type):
        if self.state in ["idle", "walk", "crouch"]:
            self.change_state("attack")
            self.current_attack = attack_type
            play_sound("move.mp3", volume=0.3)

    def update(self, controls, enemy_x):
        if self.state not in ["attack", "hitstun", "dead"]:
            self.dir = 1 if enemy_x > self.x else -1

        self.vy += 1.5 
        if self.vy > 25: self.vy = 25 
        self.y += self.vy
        
        if self.y >= 550 - self.h:
            self.y = 550 - self.h
            self.vy = 0
            if self.state == "jump":
                self.change_state("idle")

        self.x += self.vx
        if self.state not in ["walk", "jump"]:
            if self.state == "attack":
                self.vx *= 0.85 
            else:
                self.vx *= 0.50 
            if abs(self.vx) < 0.5: self.vx = 0

        if self.x < 50: self.x = 50
        if self.x > 950 - self.w: self.x = 950 - self.w

        self.timer += 1

        # --- BLOCK TIMER MATRIX (Just Defend Logic) ---
        is_holding_back = (self.dir == 1 and controls["left"]) or (self.dir == -1 and controls["right"])
        if self.state in ["idle", "walk", "crouch"]:
            if is_holding_back:
                self.block_timer += 1
            else:
                self.block_timer = 0
        elif self.state != "block":
            self.block_timer = 0

        # State Execution
        if self.state == "hitstun" or self.state == "block":
            if self.timer > self.stun_duration:
                self.change_state("idle")

        elif self.state == "attack":
            data = MOVESET[self.current_attack]
            start, active, rec = data["start"], data["active"], data["rec"]
            
            if self.current_attack == "special" and self.timer == start:
                return "SPAWN_PROJ" 

            if self.current_attack != "special":
                if start <= self.timer < start + active:
                    bw, bh, ox, oy = data["box"]
                    hx = self.x + self.w/2 + (ox * self.dir) - (bw if self.dir == -1 else 0)
                    hy = self.y + oy
                    self.active_hitbox = pygame.Rect(hx, hy, bw, bh)
                    
                    if self.current_attack == "heavy" and self.timer == start:
                        self.vx = 12 * self.dir
                else:
                    self.active_hitbox = None

            if self.timer >= start + active + rec:
                self.change_state("idle")

        elif self.state in ["idle", "walk", "crouch"]:
            if self.hp <= 0:
                self.change_state("dead")
                return
                
            if controls["up"] and self.vy == 0:
                self.change_state("jump")
                self.vy = self.jump_power
            elif controls["down"]:
                self.change_state("crouch")
                self.vx = 0
            else:
                moving = False
                if controls["left"]:
                    self.vx = -self.speed
                    moving = True
                if controls["right"]:
                    self.vx = self.speed
                    moving = True
                
                if moving:
                    self.state = "walk"
                else:
                    self.state = "idle"

    def get_joint(self, start_pos, angle, length):
        rad = angle * self.dir
        x = start_pos[0] + math.sin(rad) * length
        y = start_pos[1] + math.cos(rad) * length
        return (x, y)

    def draw(self, surface, offset_x, offset_y):
        cx = self.x + self.w/2 + offset_x
        cy = self.y + offset_y
        
        u_arm, l_arm = 25, 25
        u_leg, l_leg = 35, 35
        torso_len = 50
        
        pose = {
            "spine": 0, "neck": 0,
            "f_hip": 0, "f_knee": 0, "b_hip": 0, "b_knee": 0,
            "f_sh": 0, "f_el": 0, "b_sh": 0, "b_el": 0
        }
        
        t = self.timer
        breathe = math.sin(pygame.time.get_ticks() * 0.005) * 0.05
        pelvis_y = cy + 65
        
        if self.state == "idle":
            pose["spine"] = breathe
            pose["f_sh"] = 0.2 + breathe; pose["f_el"] = -0.2
            pose["b_sh"] = -0.2 - breathe; pose["b_el"] = -0.2
            pose["f_hip"] = 0.1; pose["b_hip"] = -0.1
            
        elif self.state == "walk":
            cycle = t * 0.2
            pose["spine"] = 0.1 
            pose["f_hip"] = math.sin(cycle) * 0.8
            pose["f_knee"] = max(0, math.sin(cycle) * 0.8)
            pose["b_hip"] = math.sin(cycle + math.pi) * 0.8
            pose["b_knee"] = max(0, math.sin(cycle + math.pi) * 0.8)
            pose["f_sh"] = math.sin(cycle + math.pi) * 0.5
            pose["b_sh"] = math.sin(cycle) * 0.5
            
        elif self.state == "crouch":
            pelvis_y += 20
            pose["spine"] = 0.4
            pose["f_hip"] = 1.0; pose["f_knee"] = -1.0
            pose["b_hip"] = 0.5; pose["b_knee"] = -1.0
            pose["f_sh"] = 0.5; pose["f_el"] = -1.5
            
        elif self.state == "jump":
            pose["f_hip"] = -0.2; pose["f_knee"] = -0.5
            pose["b_hip"] = 0.5; pose["b_knee"] = -0.8
            pose["f_sh"] = 2.0; pose["b_sh"] = -2.0 
            
        elif self.state == "block":
            pose["spine"] = -0.2
            pose["f_sh"] = 1.0; pose["f_el"] = -2.0 
            pose["b_sh"] = 1.2; pose["b_el"] = -2.2
            pose["f_hip"] = 0.2; pose["b_hip"] = -0.2
            
        elif self.state == "hitstun":
            pose["spine"] = -0.6 
            pose["neck"] = -0.8
            pose["f_sh"] = -1.5; pose["b_sh"] = -2.0 
            pose["f_hip"] = 0.3; pose["b_hip"] = 0.0
            
        elif self.state == "attack":
            start = MOVESET[self.current_attack]["start"]
            active = MOVESET[self.current_attack]["active"]
            
            if self.current_attack == "light": 
                pose["b_sh"] = -0.5
                if t < start: 
                    pose["f_sh"] = -0.5; pose["f_el"] = -1.5
                elif t < start + active: 
                    pose["spine"] = 0.3
                    pose["f_sh"] = math.pi/2; pose["f_el"] = 0.1 
                else: 
                    pose["f_sh"] = 0.5; pose["f_el"] = -1.0
                    
            elif self.current_attack == "heavy": 
                if t < start: 
                    pose["spine"] = -0.2
                    pose["f_hip"] = 0.5; pose["f_knee"] = -1.5 
                elif t < start + active: 
                    pose["spine"] = -0.5 
                    pose["f_hip"] = math.pi/2 - 0.2; pose["f_knee"] = 0.0 
                    pose["b_hip"] = 0.2; pose["b_knee"] = 0.2 
                    pose["f_sh"] = -1.0; pose["b_sh"] = 1.0 
                else:
                    pose["spine"] = -0.2
                    pose["f_hip"] = 0.5; pose["f_knee"] = -0.5
                    
            elif self.current_attack == "special": 
                pose["spine"] = 0.1
                if t < start: 
                    pose["f_sh"] = 0.5; pose["f_el"] = -1.5
                elif t < start + active: 
                    pose["f_sh"] = math.pi/2 + 0.2; pose["f_el"] = -0.2
                else: 
                    pose["f_sh"] = math.pi/2; pose["f_el"] = 0

        pelvis = (cx, pelvis_y)
        neck = (cx + math.sin(pose["spine"]*self.dir)*torso_len, pelvis_y - math.cos(pose["spine"]*self.dir)*torso_len)
        head = (neck[0] + math.sin((pose["spine"]+pose["neck"])*self.dir)*20, neck[1] - math.cos((pose["spine"]+pose["neck"])*self.dir)*20)
        
        f_knee_pos = self.get_joint(pelvis, pose["f_hip"], u_leg)
        f_foot_pos = self.get_joint(f_knee_pos, pose["f_hip"] + pose["f_knee"], l_leg)
        b_knee_pos = self.get_joint(pelvis, pose["b_hip"], u_leg)
        b_foot_pos = self.get_joint(b_knee_pos, pose["b_hip"] + pose["b_knee"], l_leg)
        
        f_el_pos = self.get_joint(neck, pose["f_sh"], u_arm)
        f_hand_pos = self.get_joint(f_el_pos, pose["f_sh"] + pose["f_el"], l_arm)
        b_el_pos = self.get_joint(neck, pose["b_sh"], u_arm)
        b_hand_pos = self.get_joint(b_el_pos, pose["b_sh"] + pose["b_el"], l_arm)

        c_body = self.color if self.state != "hitstun" else (255, 255, 255)
        c_dark = (self.color[0]//2, self.color[1]//2, self.color[2]//2) if self.state != "hitstun" else (200,200,200)
        thick = 12

        pygame.draw.line(surface, c_dark, pelvis, b_knee_pos, thick)
        pygame.draw.line(surface, c_dark, b_knee_pos, b_foot_pos, thick)
        pygame.draw.line(surface, c_dark, neck, b_el_pos, thick)
        pygame.draw.line(surface, c_dark, b_el_pos, b_hand_pos, thick)
        
        pygame.draw.line(surface, c_body, pelvis, neck, thick + 4)
        pygame.draw.circle(surface, c_body, (int(head[0]), int(head[1])), 16)
        
        eye_dir = 1 if self.dir == 1 else -1
        pygame.draw.rect(surface, (255,255,255), (head[0] + 4*eye_dir - 4, head[1] - 4, 8, 4))
        
        pygame.draw.line(surface, c_body, pelvis, f_knee_pos, thick)
        pygame.draw.line(surface, c_body, f_knee_pos, f_foot_pos, thick)
        pygame.draw.line(surface, c_body, neck, f_el_pos, thick)
        pygame.draw.line(surface, c_body, f_el_pos, f_hand_pos, thick)

        if self.state == "attack" and self.timer >= MOVESET[self.current_attack]["start"]:
            if self.current_attack == "light":
                d_end = (f_hand_pos[0] + 35 * self.dir, f_hand_pos[1] - 5)
                pygame.draw.line(surface, (200, 200, 220), f_hand_pos, d_end, 6)
            elif self.current_attack == "special":
                gun_rect = pygame.Rect(0, 0, 30, 14)
                gun_rect.centery = f_hand_pos[1]
                if self.dir == 1: gun_rect.left = f_hand_pos[0] - 10
                else: gun_rect.right = f_hand_pos[0] + 10
                pygame.draw.rect(surface, (80, 80, 90), gun_rect, border_radius=3)

def controls_dict(fighter):
    if fighter.is_ai: return {"left": False, "right": False} 
    keys = pygame.key.get_pressed()
    return {"left": keys[pygame.K_LEFT] or keys[pygame.K_a], "right": keys[pygame.K_RIGHT] or keys[pygame.K_d]}

def main(screen):
    pygame.mixer.init()
    play_sound("racing.mp3", loop=-1, volume=0.4) 

    width, height = screen.get_size()
    pygame.display.set_caption("Neon Brawl")
    clock = pygame.time.Clock()
    
    # Internal Rendering Canvas for Camera Manipulation
    canvas = pygame.Surface((width, height))
    
    font_massive = pygame.font.SysFont("Impact", 100, italic=True)
    font_ui = pygame.font.SysFont("Courier New", 24, bold=True)

    def reset_match():
        p1 = Fighter(200, 410, (0, 240, 255), is_ai=False)
        p2 = Fighter(750, 410, (255, 0, 127), is_ai=True)
        p2.dir = -1
        return p1, p2, [], [], [], 0, 0, "INTRO", 120, (width//2, height//2), 0

    p1, p2, sparks, projectiles, floating_texts, hitstop, shake, game_state, state_timer, final_blow_pos, flash_alpha = reset_match()

    running = True
    while running:
        dt = clock.tick(60)
        canvas.fill((10, 10, 15))

        p1_controls = {"left": False, "right": False, "up": False, "down": False}
        p2_controls = {"left": False, "right": False, "up": False, "down": False}
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    play_sound("exit.mp3")
                    pygame.time.wait(200)
                    running = False
                
                if game_state == "FIGHT":
                    if event.key == pygame.K_z: p1.attack("light")
                    if event.key == pygame.K_x: p1.attack("heavy")
                    if event.key == pygame.K_c: p1.attack("special")
                    
                if game_state == "KO" and state_timer <= 0:
                    if event.key == pygame.K_RETURN:
                        play_sound("launch.mp3")
                        p1, p2, sparks, projectiles, floating_texts, hitstop, shake, game_state, state_timer, final_blow_pos, flash_alpha = reset_match()
                        
            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE) and p1.vy < -5:
                    p1.vy = -5

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: p1_controls["left"] = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: p1_controls["right"] = True
        if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]: p1_controls["up"] = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: p1_controls["down"] = True

        # --- AI LOGIC ---
        if game_state == "FIGHT" and p2.state not in ["hitstun", "dead"]:
            dist = abs(p1.x - p2.x)
            if dist > 300:
                if random.random() < 0.02: p2.attack("special")
                else:
                    p2_controls["left"] = (p1.x < p2.x)
                    p2_controls["right"] = (p1.x > p2.x)
            else:
                if p1.state == "attack" and random.random() < 0.7:
                    p2_controls["left"] = (p2.x > p1.x)
                    p2_controls["right"] = (p2.x < p1.x)
                elif random.random() < 0.05:
                    if dist < 90: p2.attack(random.choice(["light", "heavy"]))
                    else:
                        p2_controls["left"] = (p1.x < p2.x)
                        p2_controls["right"] = (p1.x > p2.x)

        # --- UPDATE PIPELINE ---
        if hitstop > 0:
            hitstop -= 1 
        else:
            if game_state in ["FIGHT", "KO"]:
                action1 = p1.update(p1_controls, p2.x)
                action2 = p2.update(p2_controls, p1.x)
                
                if action1 == "SPAWN_PROJ":
                    projectiles.append(Projectile(p1.x + (50 * p1.dir), p1.y + 35, p1.dir, p1.color, "p1"))
                    play_sound("launch.mp3", volume=0.5)
                if action2 == "SPAWN_PROJ":
                    projectiles.append(Projectile(p2.x + (50 * p2.dir), p2.y + 35, p2.dir, p2.color, "p2"))
                    play_sound("launch.mp3", volume=0.5)

                for proj in projectiles: proj.update()
                projectiles = [p for p in projectiles if p.active]

                for s in sparks: s.update()
                sparks = [s for s in sparks if s.life > 0]
                
                for f_txt in floating_texts: f_txt.update()
                floating_texts = [f for f in floating_texts if f.life > 0]

                # --- HIT DETECTION ---
                fighters = [(p1, p2), (p2, p1)]
                for attacker, defender in fighters:
                    
                    # Melee Collisions
                    if attacker.active_hitbox and not attacker.has_hit:
                        if attacker.active_hitbox.colliderect(defender.rect()):
                            attacker.has_hit = True
                            data = MOVESET[attacker.current_attack]
                            
                            def_ctrl = controls_dict(defender) if not defender.is_ai else p2_controls
                            is_holding_back = (defender.dir == 1 and def_ctrl["left"]) or (defender.dir == -1 and def_ctrl["right"])
                            is_blocking = defender.state in ["idle", "walk", "crouch", "block"] and is_holding_back
                            
                            hit_x = attacker.active_hitbox.centerx
                            hit_y = attacker.active_hitbox.centery

                            if is_blocking:
                                # JUST DEFEND PARRY WINDOW (1-5 Frames)
                                if 0 < defender.block_timer <= 5:
                                    hitstop = data["stop"] * 2
                                    flash_alpha = 255
                                    play_sound("launch.mp3", volume=1.0)
                                    
                                    attacker.change_state("hitstun")
                                    attacker.stun_duration = 45 # Massive punish window
                                    attacker.vx = -6 * attacker.dir
                                    defender.block_timer = 0
                                    
                                    floating_texts.append(FloatingText(defender.x + defender.w//2, defender.y - 20, "JUST DEFEND!", (255, 255, 255)))
                                    
                                    for _ in range(25):
                                        angle = random.uniform(-math.pi, math.pi)
                                        sparks.append(Spark(hit_x, hit_y, angle, random.uniform(8, 25), (255, 255, 255), random.randint(15, 30)))
                                else:
                                    # Normal Block
                                    defender.hp -= data["dmg"] * 0.1
                                    defender.vx = data["push"] * 1.5 * attacker.dir
                                    defender.stun_duration = 10
                                    defender.change_state("block")
                                    hitstop = 4
                                    play_sound("move.mp3", volume=0.8) 
                            else:
                                # Normal Hit
                                defender.hp -= data["dmg"]
                                defender.vx = data["push"] * attacker.dir
                                defender.stun_duration = data["stun"]
                                defender.change_state("hitstun")
                                hitstop = data["stop"]
                                shake = data["stop"] + 4
                                play_sound("launch.mp3", volume=0.8) 
                                
                                for _ in range(15):
                                    angle = random.uniform(-math.pi/4, math.pi/4) if attacker.dir == 1 else random.uniform(math.pi - math.pi/4, math.pi + math.pi/4)
                                    sparks.append(Spark(hit_x, hit_y, angle, random.uniform(5, 18), attacker.color, random.randint(10, 25)))
                                    
                            if defender.hp <= 0: final_blow_pos = (hit_x, hit_y)

                    # Projectile Collisions
                    for proj in projectiles:
                        if proj.active and proj.owner != ("p1" if attacker == p1 else "p2"):
                            if proj.rect.colliderect(defender.rect()):
                                proj.active = False
                                
                                def_ctrl = controls_dict(defender) if not defender.is_ai else p2_controls
                                is_holding_back = (defender.dir == 1 and def_ctrl["left"]) or (defender.dir == -1 and def_ctrl["right"])
                                is_blocking = defender.state in ["idle", "walk", "crouch", "block"] and is_holding_back

                                if is_blocking:
                                    if 0 < defender.block_timer <= 5:
                                        hitstop = 10
                                        flash_alpha = 255
                                        play_sound("launch.mp3", volume=1.0)
                                        defender.block_timer = 0
                                        floating_texts.append(FloatingText(defender.x + defender.w//2, defender.y - 20, "JUST DEFEND!", (255, 255, 255)))
                                    else:
                                        defender.hp -= MOVESET["special"]["dmg"] * 0.1
                                        defender.vx = MOVESET["special"]["push"] * 1.5 * proj.dir
                                        defender.stun_duration = 10
                                        defender.change_state("block")
                                        hitstop = 4
                                        play_sound("move.mp3", volume=0.8)
                                else:
                                    defender.hp -= MOVESET["special"]["dmg"]
                                    defender.vx = MOVESET["special"]["push"] * proj.dir
                                    defender.stun_duration = MOVESET["special"]["stun"]
                                    defender.change_state("hitstun")
                                    hitstop = 6
                                    shake = 8
                                    play_sound("launch.mp3", volume=0.8)
                                    for _ in range(20):
                                        angle = random.uniform(-math.pi, math.pi)
                                        sparks.append(Spark(proj.x, proj.y, angle, random.uniform(8, 20), proj.color, random.randint(15, 30)))
                                
                                if defender.hp <= 0: final_blow_pos = (proj.x, proj.y)

                # Check KO State Trigger
                if (p1.hp <= 0 or p2.hp <= 0) and game_state != "KO":
                    game_state = "KO"
                    state_timer = 180
                    hitstop = 30 
                    shake = 0 # Handled by Zoom

        # --- RENDERING PIPELINE ---
        cam_x, cam_y = 0, 0
        if shake > 0 and hitstop == 0: 
            cam_x = random.randint(-shake, shake)
            cam_y = random.randint(-shake, shake)
            shake -= 1

        pygame.draw.line(canvas, (0, 255, 255), (0, 550 + cam_y), (width, 550 + cam_y), 4)

        p1.draw(canvas, cam_x, cam_y)
        p2.draw(canvas, cam_x, cam_y)
        
        for proj in projectiles: proj.draw(canvas, cam_x, cam_y)
        for s in sparks: s.draw(canvas, cam_x, cam_y)
        for f_txt in floating_texts: f_txt.draw(canvas, cam_x, cam_y)
        
        # Determine Display Buffer (Zoom logic applies here)
        screen.fill((0, 0, 0))
        if game_state == "KO" and hitstop > 0:
            # Cinematic K.O. Zoom directly on final blow coordinates
            zoom = 2.0
            scaled_w, scaled_h = int(width * zoom), int(height * zoom)
            scaled_canvas = pygame.transform.scale(canvas, (scaled_w, scaled_h))
            
            ox = width // 2 - int(final_blow_pos[0] * zoom)
            oy = height // 2 - int(final_blow_pos[1] * zoom)
            screen.blit(scaled_canvas, (ox, oy))
        else:
            screen.blit(canvas, (0, 0))
            
        # Draw High-Impact Flash Overlays
        if flash_alpha > 0:
            flash_surf = pygame.Surface((width, height))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(flash_alpha)
            screen.blit(flash_surf, (0, 0))
            flash_alpha = max(0, flash_alpha - 15)

        # UI rendering (Drawn statically on screen so it doesn't get zoomed/shook)
        pygame.draw.rect(screen, (50, 0, 0), (50, 30, 400, 30))
        if p1.hp > 0: pygame.draw.rect(screen, p1.color, (50 + (400 - int((p1.hp/p1.max_hp)*400)), 30, int((p1.hp/p1.max_hp)*400), 30))
        pygame.draw.rect(screen, (255, 255, 255), (50, 30, 400, 30), 3)

        pygame.draw.rect(screen, (50, 0, 0), (550, 30, 400, 30))
        if p2.hp > 0: pygame.draw.rect(screen, p2.color, (550, 30, int((p2.hp/p2.max_hp)*400), 30))
        pygame.draw.rect(screen, (255, 255, 255), (550, 30, 400, 30), 3)

        if game_state == "INTRO":
            state_timer -= 1
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0,0))
            
            msg = "FIGHT!" if state_timer < 40 else "ROUND 1"
            txt = font_massive.render(msg, True, (255, 255, 255))
            screen.blit(txt, (width//2 - txt.get_width()//2, height//2 - txt.get_height()//2))
            
            if state_timer <= 0:
                game_state = "FIGHT"
                play_sound("launch.mp3")

        elif game_state == "KO":
            if hitstop == 0: state_timer -= 1 # Only decay timer after hitstop freeze
            if state_timer < 160: 
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0,0))
                
                ko_txt = font_massive.render("K. O.", True, (255, 0, 50))
                screen.blit(ko_txt, (width//2 - ko_txt.get_width()//2, height//2 - ko_txt.get_height()//2 - 50))
                
                if state_timer <= 0:
                    win_msg = "PLAYER 1 WINS" if p1.hp > 0 else "CPU WINS"
                    sub_txt = font_ui.render(f"{win_msg} - PRESS ENTER TO REMATCH", True, (255, 255, 255))
                    screen.blit(sub_txt, (width//2 - sub_txt.get_width()//2, height//2 + 80))

        pygame.display.flip()

if __name__ == "__main__":
    pygame.init()
    test_screen = pygame.display.set_mode((1000, 650))
    main(test_screen)