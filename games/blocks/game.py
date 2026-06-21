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

# --- CONSTANTS & SHAPES ---
BOARD_SIZE = 8
CELL = 48

# A matrix of distinct block shapes (Block Blast style)
SHAPES = [
    [[1]],                                      # 1x1
    [[1, 1]], [[1], [1]],                       # 2x1, 1x2
    [[1, 1, 1]], [[1], [1], [1]],               # 3x1, 1x3
    [[1, 1, 1, 1]], [[1], [1], [1], [1]],       # 4x1, 1x4
    [[1, 1, 1, 1, 1]], [[1], [1], [1], [1], [1]], # 5x1, 1x5
    [[1, 1], [1, 1]],                           # 2x2
    [[1, 1, 1], [1, 1, 1], [1, 1, 1]],          # 3x3
    [[1, 1], [1, 0]], [[1, 1], [0, 1]],         # Small Ls
    [[1, 0], [1, 1]], [[0, 1], [1, 1]],
    [[1, 1, 1], [1, 0, 0], [1, 0, 0]],          # Big Ls
    [[1, 1, 1], [0, 0, 1], [0, 0, 1]],
    [[1, 0, 0], [1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [0, 0, 1], [1, 1, 1]],
    [[1, 1, 1], [0, 1, 0], [0, 1, 0]],          # T
    [[0, 1, 0], [1, 1, 1], [0, 0, 0]]
]

# Premium Neon Color Palette
COLORS = [
    (255, 60, 100),  # Neon Red
    (60, 255, 100),  # Neon Green
    (60, 150, 255),  # Neon Blue
    (255, 200, 60),  # Neon Yellow
    (200, 60, 255),  # Neon Purple
    (60, 255, 255)   # Neon Cyan
]

def create_block_surface(size, color, alpha=255, glow=False):
    """Caches a premium-looking rounded block to save render time."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, size, size)
    
    # Outer Glow
    if glow:
        pygame.draw.rect(surf, (*color, alpha // 3), rect, border_radius=8)
        rect = rect.inflate(-6, -6)
        
    # Main Block
    pygame.draw.rect(surf, (*color, alpha), rect, border_radius=6)
    
    # Inner Highlight (Top/Left)
    highlight = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(highlight, (255, 255, 255, 80), rect, width=2, border_radius=6)
    surf.blit(highlight, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    
    # Inner Shadow (Bottom/Right)
    shadow = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), rect.move(2, 2), width=3, border_radius=6)
    surf.blit(shadow, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    
    return surf

# --- JUICE CLASSES ---
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = color
        self.life = random.randint(30, 60)
        self.max_life = self.life
        self.size = random.uniform(4, 10)
        
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(2, 10)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.rot = 0
        self.rot_spd = random.uniform(-10, 10)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.rot += self.rot_spd
        self.life -= 1

    def draw(self, surf, offset_x, offset_y):
        if self.life > 0:
            scale = self.life / self.max_life
            s = int(self.size * scale)
            if s > 0:
                alpha = int(scale * 255)
                psurf = pygame.Surface((s*2, s*2), pygame.SRCALPHA)
                pygame.draw.rect(psurf, (*self.color, alpha), (0, 0, s*2, s*2), border_radius=2)
                rotated = pygame.transform.rotate(psurf, self.rot)
                rx = self.x + offset_x - rotated.get_width()//2
                ry = self.y + offset_y - rotated.get_height()//2
                surf.blit(rotated, (int(rx), int(ry)))

class FloatingText:
    def __init__(self, x, y, text, color, size, is_combo=False):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = 60 if is_combo else 40
        self.max_life = self.life
        self.font = pygame.font.SysFont("Impact", size, italic=True)
        self.vy = -1.5 if not is_combo else -0.5
        self.scale = 0.5
        self.target_scale = 1.2 if is_combo else 1.0

    def update(self):
        self.y += self.vy
        self.scale += (self.target_scale - self.scale) * 0.2
        if self.scale > 0.95: self.target_scale = 1.0
        self.life -= 1

    def draw(self, surf, offset_x, offset_y):
        if self.life > 0:
            txt = self.font.render(self.text, True, self.color)
            w, h = txt.get_size()
            scaled = pygame.transform.smoothscale(txt, (int(w * self.scale), int(h * self.scale)))
            scaled.set_alpha(int((self.life / self.max_life) * 255))
            surf.blit(scaled, (int(self.x + offset_x - scaled.get_width()//2), int(self.y + offset_y - scaled.get_height()//2)))

# --- PIECE CLASS ---
class Piece:
    def __init__(self, shape, color, slot_idx):
        self.shape = shape
        self.color = color
        self.slot_idx = slot_idx
        
        self.cols = len(shape[0])
        self.rows = len(shape)
        
        # Physics & Smoothing
        self.scale = 0.0
        self.target_scale = 0.5 # Tray scale
        
        self.x, self.y = 0, 0
        self.target_x, self.target_y = 0, 0
        self.home_x, self.home_y = 0, 0
        
        self.is_dragged = False
        self.is_placed = False
        self.surface = create_block_surface(CELL, self.color, glow=True)

    def update(self, cursor_x, cursor_y, screen_w, screen_h):
        # Dynamically map the tray slots based on screen width/height
        tray_y = screen_h - 100
        tray_spacing = screen_w // 3
        
        if self.is_dragged:
            self.target_scale = 1.15
            self.target_x = cursor_x - (self.cols * CELL * self.target_scale) // 2
            self.target_y = cursor_y - (self.rows * CELL * self.target_scale) // 2
        else:
            self.target_scale = 0.5
            self.home_x = (self.slot_idx * tray_spacing) + (tray_spacing // 2) - (self.cols * CELL * self.target_scale) // 2
            self.home_y = tray_y - (self.rows * CELL * self.target_scale) // 2
            
            self.target_x = self.home_x
            self.target_y = self.home_y
            
        # Spring physics interpolation
        self.x += (self.target_x - self.x) * 0.3
        self.y += (self.target_y - self.y) * 0.3
        self.scale += (self.target_scale - self.scale) * 0.25

    def draw(self, surf, offset_x, offset_y):
        if self.is_placed: return
        
        cur_cell = int(CELL * self.scale)
        scaled_surf = pygame.transform.smoothscale(self.surface, (cur_cell, cur_cell))
        
        # Draw Drop Shadow if Dragged
        if self.is_dragged:
            shadow = pygame.Surface((cur_cell, cur_cell), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 80))
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.shape[r][c]:
                        surf.blit(shadow, (int(self.x + c * cur_cell + offset_x + 15), int(self.y + r * cur_cell + offset_y + 20)))

        # Draw Blocks
        for r in range(self.rows):
            for c in range(self.cols):
                if self.shape[r][c]:
                    surf.blit(scaled_surf, (int(self.x + c * cur_cell + offset_x), int(self.y + r * cur_cell + offset_y)))

# --- MAIN GAME ENGINE ---
def main(screen):
    pygame.mixer.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()
        
    play_sound("blocks.mp3", loop=-1, volume=0.5)

    WIDTH, HEIGHT = screen.get_size()
    pygame.display.set_caption("Block Blast")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont("Courier New", 28, bold=True)
    title_font = pygame.font.SysFont("Impact", 60, italic=True)
    
    config = load_config()
    high_score = config.get("high_score", 0)

    # Controller / Mouse setup
    v_cursor_x, v_cursor_y = WIDTH // 2, HEIGHT // 2
    using_gamepad = False

    board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    # State Matrix
    pieces = []
    particles = []
    texts = []
    score = 0
    combo = 0
    shake_timer = 0
    shake_intensity = 0
    game_state = "PLAYING" # PLAYING, GAME_OVER
    game_over_timer = 0
    is_fullscreen = False

    bg_particles = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT), "s": random.uniform(1, 3), "vy": random.uniform(-0.5, -0.1)} for _ in range(40)]

    def spawn_pieces():
        pieces.clear()
        for i in range(3):
            shape = random.choice(SHAPES)
            color = random.choice(COLORS)
            p = Piece(shape, color, i)
            # Offset spawn so they animate up into the tray properly
            p.y = HEIGHT + 100 
            pieces.append(p)

    def check_fit(shape, br, bc):
        rows, cols = len(shape), len(shape[0])
        if br < 0 or bc < 0 or br + rows > BOARD_SIZE or bc + cols > BOARD_SIZE:
            return False
        for r in range(rows):
            for c in range(cols):
                if shape[r][c] and board[br + r][bc + c] is not None:
                    return False
        return True

    def is_game_over():
        if len(pieces) == 0: return False
        for p in pieces:
            if p.is_placed: continue
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if check_fit(p.shape, r, c):
                        return False
        return True

    spawn_pieces()
    dragged_piece = None

    # Block Surface Cache
    block_cache = {col: create_block_surface(CELL, col) for col in COLORS}
    empty_cell = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.rect(empty_cell, (30, 35, 45, 150), (0,0,CELL,CELL), border_radius=6)
    pygame.draw.rect(empty_cell, (50, 55, 65, 100), (0,0,CELL,CELL), width=1, border_radius=6)

    # Initialize Pygame Mouse Relative buffer
    pygame.mouse.get_rel()

    running = True
    while running:
        dt = clock.tick(60)
        
        # Calculate dynamic board constraints 
        HUD_HEIGHT = 80
        TRAY_HEIGHT = 150
        board_px_size = BOARD_SIZE * CELL
        board_offset_x = (WIDTH - board_px_size) // 2
        board_offset_y = (HEIGHT - HUD_HEIGHT - TRAY_HEIGHT - board_px_size) // 2 + HUD_HEIGHT
        
        action_down = False
        action_up = False
        
        # --- INPUT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                
            # Responsive Screen Logic
            elif event.type == pygame.VIDEORESIZE:
                if not is_fullscreen:
                    WIDTH, HEIGHT = event.w, event.h
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((1000, 650), pygame.RESIZABLE)
                WIDTH, HEIGHT = screen.get_size()
            
            # Universal Click/Drop Registration (Keyboard, Mouse, Gamepad)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                action_down = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action_down = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                action_up = True
            elif event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                action_down = True
            elif event.type == pygame.JOYBUTTONUP and event.button == 0:
                action_up = True

        # Virtual Cursor Updates
        m_rel = pygame.mouse.get_rel()
        if m_rel != (0, 0):
            using_gamepad = False
            v_cursor_x, v_cursor_y = pygame.mouse.get_pos()
            
        if joysticks:
            joy = joysticks[0]
            dx, dy = 0, 0
            if abs(joy.get_axis(0)) > 0.2: dx = joy.get_axis(0)
            if abs(joy.get_axis(1)) > 0.2: dy = joy.get_axis(1)
            if joy.get_numhats() > 0:
                hat = joy.get_hat(0)
                if hat[0] != 0: dx = hat[0]
                if hat[1] != 0: dy = -hat[1]
                
            if dx != 0 or dy != 0:
                using_gamepad = True
                v_cursor_x += dx * 16
                v_cursor_y += dy * 16
                
        # Clamp Cursor
        v_cursor_x = max(0, min(WIDTH, v_cursor_x))
        v_cursor_y = max(0, min(HEIGHT, v_cursor_y))
            
        # --- GAMEPLAY LOGIC ---
        if game_state == "PLAYING":
            if action_down:
                for p in reversed(pieces):
                    if not p.is_placed:
                        pw = p.cols * CELL * p.scale
                        ph = p.rows * CELL * p.scale
                        
                        # Generous Selection Hitbox (Padding)
                        pad = 40
                        if p.x - pad <= v_cursor_x <= p.x + pw + pad and p.y - pad <= v_cursor_y <= p.y + ph + pad:
                            dragged_piece = p
                            p.is_dragged = True
                            play_sound("move.mp3", volume=0.3)
                            pieces.remove(p)
                            pieces.append(p)
                            break
                            
            if action_up:
                if dragged_piece:
                    dp = dragged_piece
                    dp.is_dragged = False
                    dragged_piece = None
                    
                    # Board Snap
                    bc = round((dp.x - board_offset_x) / CELL)
                    br = round((dp.y - board_offset_y) / CELL)
                    
                    if check_fit(dp.shape, br, bc):
                        play_sound("launch.mp3", volume=0.5)
                        dp.is_placed = True
                        score += 10
                        shake_timer = 4
                        shake_intensity = 2
                        
                        for r in range(dp.rows):
                            for c in range(dp.cols):
                                if dp.shape[r][c]:
                                    board[br + r][bc + c] = dp.color
                                    px = board_offset_x + (bc+c)*CELL + CELL//2
                                    py = board_offset_y + (br+r)*CELL + CELL//2
                                    for _ in range(3): particles.append(Particle(px, py, (255,255,255)))

                        # Line Clear Math
                        lines_to_clear_r = []
                        lines_to_clear_c = []
                        for r in range(BOARD_SIZE):
                            if all(board[r][c] is not None for c in range(BOARD_SIZE)): lines_to_clear_r.append(r)
                        for c in range(BOARD_SIZE):
                            if all(board[r][c] is not None for r in range(BOARD_SIZE)): lines_to_clear_c.append(c)
                                
                        cleared_count = len(lines_to_clear_r) + len(lines_to_clear_c)
                        
                        if cleared_count > 0:
                            play_sound("launch.mp3", volume=1.0)
                            combo += 1
                            score += (100 * cleared_count) * combo
                            shake_timer = 15
                            shake_intensity = 5 + (combo * 2)
                            
                            to_explode = set()
                            for r in lines_to_clear_r:
                                for c in range(BOARD_SIZE): to_explode.add((r, c))
                            for c in lines_to_clear_c:
                                for r in range(BOARD_SIZE): to_explode.add((r, c))
                                
                            for (r, c) in to_explode:
                                col = board[r][c]
                                px = board_offset_x + c*CELL + CELL//2
                                py = board_offset_y + r*CELL + CELL//2
                                for _ in range(12): particles.append(Particle(px, py, col))
                                board[r][c] = None

                            texts.append(FloatingText(WIDTH//2, board_offset_y - 20, f"+{(100 * cleared_count) * combo}", (255, 255, 100), 40))
                            if combo > 1:
                                texts.append(FloatingText(WIDTH//2, board_offset_y - 60, f"COMBO x{combo}!", (255, 100, 255), 50, True))
                        else:
                            combo = 0
                        
                        if all(p.is_placed for p in pieces):
                            spawn_pieces()
                            
                        if is_game_over():
                            game_state = "GAME_OVER"
                            play_sound("exit.mp3")
                            if score > high_score:
                                high_score = score
                                config["high_score"] = high_score
                                save_config(config)
                    else:
                        play_sound("move.mp3", volume=0.5)

        elif game_state == "GAME_OVER":
            # Safety lock: Prevent accidental instant restarts (wait 30 frames)
            if action_down and game_over_timer > 30:
                board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                score = 0
                combo = 0
                game_state = "PLAYING"
                game_over_timer = 0
                spawn_pieces()

        # --- UPDATES ---
        for bp in bg_particles:
            bp["y"] += bp["vy"]
            if bp["y"] < -10: 
                bp["y"] = HEIGHT + 10
                bp["x"] = random.randint(0, WIDTH)

        if game_state == "PLAYING":
            for p in pieces: p.update(v_cursor_x, v_cursor_y, WIDTH, HEIGHT)
        elif game_state == "GAME_OVER":
            game_over_timer += 1

        for p in particles[:]:
            p.update()
            if p.life <= 0: particles.remove(p)
            
        for txt in texts[:]:
            txt.update()
            if txt.life <= 0: texts.remove(txt)

        # --- RENDERING ---
        screen.fill((15, 15, 25))
        
        for bp in bg_particles:
            pygame.draw.circle(screen, (40, 40, 60), (int(bp["x"]), int(bp["y"])), int(bp["s"]))

        ox, oy = 0, 0
        if shake_timer > 0:
            ox = random.randint(-shake_intensity, shake_intensity)
            oy = random.randint(-shake_intensity, shake_intensity)
            shake_timer -= 1

        # Board rendering
        pygame.draw.rect(screen, (20, 22, 30), (board_offset_x - 10 + ox, board_offset_y - 10 + oy, board_px_size + 20, board_px_size + 20), border_radius=12)

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cx = board_offset_x + c * CELL + ox
                cy = board_offset_y + r * CELL + oy
                screen.blit(empty_cell, (cx, cy))
                if board[r][c] is not None:
                    screen.blit(block_cache[board[r][c]], (cx, cy))

        # Hover Preview Logic
        if dragged_piece:
            bc = round((dragged_piece.x - board_offset_x) / CELL)
            br = round((dragged_piece.y - board_offset_y) / CELL)
            
            if -2 < br < BOARD_SIZE + 2 and -2 < bc < BOARD_SIZE + 2:
                valid = check_fit(dragged_piece.shape, br, bc)
                preview_col = (50, 255, 50, 100) if valid else (255, 50, 50, 100)
                
                for r in range(dragged_piece.rows):
                    for c in range(dragged_piece.cols):
                        if dragged_piece.shape[r][c]:
                            px = board_offset_x + (bc + c) * CELL + ox
                            py = board_offset_y + (br + r) * CELL + oy
                            s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                            pygame.draw.rect(s, preview_col, (0,0,CELL,CELL), border_radius=6)
                            screen.blit(s, (px, py))

        for p in pieces: p.draw(screen, ox, oy)
        for p in particles: p.draw(screen, ox, oy)
        for txt in texts: txt.draw(screen, ox, oy)

        # Virtual Controller Cursor
        if using_gamepad:
            pygame.draw.circle(screen, (255, 255, 255), (int(v_cursor_x), int(v_cursor_y)), 8)
            pygame.draw.circle(screen, (0, 0, 0), (int(v_cursor_x), int(v_cursor_y)), 8, 2)

        # HUD
        pygame.draw.rect(screen, (10, 12, 20), (0, 0, WIDTH, HUD_HEIGHT))
        pygame.draw.line(screen, (60, 60, 90), (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT), 2)
        
        score_lbl = font.render(f"SCORE: {score}", True, (255, 255, 255))
        hi_lbl = font.render(f"HIGH: {high_score}", True, (255, 200, 50))
        screen.blit(score_lbl, (30, 25))
        screen.blit(hi_lbl, (WIDTH - hi_lbl.get_width() - 30, 25))

        # --- GAME OVER SEQUENCE ---
        if game_state == "GAME_OVER":
            darken = min(200, game_over_timer * 4)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 5, 10, darken))
            screen.blit(overlay, (0, 0))
            
            if game_over_timer > 30:
                y_pos = HEIGHT//2 - 60
                if score >= high_score and score > 0:
                    t1 = title_font.render("NEW HIGH SCORE!", True, (255, 215, 0))
                    for _ in range(2): particles.append(Particle(random.randint(0,WIDTH), random.randint(0,HEIGHT), (255, 215, 0)))
                else:
                    t1 = title_font.render("NO MOVES LEFT", True, (255, 100, 100))
                
                t2 = font.render(f"FINAL SCORE: {score}", True, (255, 255, 255))
                t3 = font.render("CLICK OR PRESS ENTER TO RESTART", True, (150, 150, 150))
                
                screen.blit(t1, (WIDTH//2 - t1.get_width()//2, y_pos))
                screen.blit(t2, (WIDTH//2 - t2.get_width()//2, y_pos + 70))
                if (game_over_timer // 30) % 2 == 0:
                    screen.blit(t3, (WIDTH//2 - t3.get_width()//2, y_pos + 130))

        pygame.display.flip()

if __name__ == "__main__":
    pygame.init()
    main(pygame.display.set_mode((1000, 650), pygame.RESIZABLE))