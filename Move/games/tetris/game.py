import pygame
import sys
import os
import json
import random

def load_config():
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(path, 'r') as f: return json.load(f)

def save_config(config):
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(path, 'w') as f: json.dump(config, f, indent=4)

# Audio Path Helper
def play_sound(filename, loop=0, volume=1.0):
    try:
        # Navigate up from games/tetris/game.py to the root /music/ directory
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

# Shapes defined as coordinate offsets
SHAPES = [
    [(-1,0), (0,0), (1,0), (2,0)], # I
    [(0,-1), (0,0), (1,0), (1,-1)], # O
    [(-1,0), (0,0), (0,-1), (1,-1)], # S
    [(-1,-1), (0,-1), (0,0), (1,0)], # Z
    [(-1,0), (0,0), (1,0), (0,-1)], # T
    [(-1,-1), (-1,0), (0,0), (1,0)], # L
    [(1,-1), (-1,0), (0,0), (1,0)]  # J
]
COLORS = [(0,255,255), (255,255,0), (0,255,0), (255,0,0), (128,0,128), (255,165,0), (0,0,255)]

def main(screen):
    # Ensure mixer is initialized and play the Tetris soundtrack
    pygame.mixer.init()
    play_sound("tetris.mp3", loop=-1, volume=0.5)

    width, height = screen.get_size()
    pygame.display.set_caption("Tetris Matrix")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier New", 24, bold=True)

    config = load_config()
    high_score = config.get("high_score", 0)

    BLOCK = 30
    COLS, ROWS = 10, 20
    grid_w, grid_h = COLS * BLOCK, ROWS * BLOCK
    offset_x, offset_y = (width - grid_w) // 2, (height - grid_h) // 2

    def new_piece():
        idx = random.randint(0, 6)
        return {"shape": list(SHAPES[idx]), "color": COLORS[idx], "x": COLS//2, "y": 1}

    grid = [[None]*COLS for _ in range(ROWS)]
    piece = new_piece()
    next_piece = new_piece()
    score = 0
    game_over = False

    fall_time = 0
    fall_speed = 500 # ms

    def valid_pos(p, dx=0, dy=0, shape=None):
        test_shape = shape if shape else p["shape"]
        for px, py in test_shape:
            x, y = p["x"] + px + dx, p["y"] + py + dy
            if x < 0 or x >= COLS or y >= ROWS or (y >= 0 and grid[y][x]): return False
        return True

    def rotate(p):
        rotated = [(-y, x) for x, y in p["shape"]]
        if valid_pos(p, shape=rotated): p["shape"] = rotated

    def lock_piece():
        nonlocal score, fall_speed, piece, next_piece, game_over, high_score
        for px, py in piece["shape"]:
            y = piece["y"] + py
            if y < 0: game_over = True
            else: grid[y][piece["x"] + px] = piece["color"]
        
        if game_over:
            if score > high_score:
                high_score = score
                config["high_score"] = high_score
                save_config(config)
            return

        # Clear lines
        cleared = 0
        for y in range(ROWS-1, -1, -1):
            if all(grid[y]):
                del grid[y]
                grid.insert(0, [None]*COLS)
                cleared += 1
        score += (cleared ** 2) * 100
        fall_speed = max(100, 500 - (score // 10))
        
        piece = next_piece
        next_piece = new_piece()
        if not valid_pos(piece): game_over = True

    def hard_drop():
        while valid_pos(piece, dy=1): piece["y"] += 1
        lock_piece()

    running = True
    while running:
        screen.fill((20, 20, 30))
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
                if event.key == pygame.K_RETURN and game_over:
                    play_sound("launch.mp3")
                    grid = [[None]*COLS for _ in range(ROWS)]
                    score = 0
                    fall_speed = 500
                    piece, next_piece = new_piece(), new_piece()
                    game_over = False
                if not game_over:
                    if event.key == pygame.K_LEFT and valid_pos(piece, dx=-1): 
                        piece["x"] -= 1
                        play_sound("move.mp3")
                    if event.key == pygame.K_RIGHT and valid_pos(piece, dx=1): 
                        piece["x"] += 1
                        play_sound("move.mp3")
                    if event.key == pygame.K_DOWN and valid_pos(piece, dy=1): 
                        piece["y"] += 1
                    if event.key == pygame.K_UP: 
                        rotate(piece)
                        play_sound("move.mp3")
                    if event.key == pygame.K_SPACE: 
                        hard_drop()
                        play_sound("launch.mp3")

        if not game_over:
            fall_time += dt
            if fall_time >= fall_speed:
                fall_time = 0
                if valid_pos(piece, dy=1): piece["y"] += 1
                else: lock_piece()

        # Draw Grid background
        pygame.draw.rect(screen, (10, 10, 15), (offset_x, offset_y, grid_w, grid_h))
        pygame.draw.rect(screen, (100, 100, 120), (offset_x, offset_y, grid_w, grid_h), 2)

        # Draw locked blocks
        for y in range(ROWS):
            for x in range(COLS):
                if grid[y][x]:
                    pygame.draw.rect(screen, grid[y][x], (offset_x + x*BLOCK, offset_y + y*BLOCK, BLOCK-1, BLOCK-1))

        # Draw Ghost Piece
        if not game_over:
            ghost_y = piece["y"]
            while valid_pos(piece, dy=ghost_y - piece["y"] + 1): ghost_y += 1
            for px, py in piece["shape"]:
                if piece["y"] + py >= 0:
                    pygame.draw.rect(screen, (50, 50, 50), (offset_x + (piece["x"]+px)*BLOCK, offset_y + (ghost_y+py)*BLOCK, BLOCK-1, BLOCK-1), 2)
            
            # Draw Active Piece
            for px, py in piece["shape"]:
                if piece["y"] + py >= 0:
                    pygame.draw.rect(screen, piece["color"], (offset_x + (piece["x"]+px)*BLOCK, offset_y + (piece["y"]+py)*BLOCK, BLOCK-1, BLOCK-1))

        # UI Context
        screen.blit(font.render(f"SCORE: {score}", True, (255, 255, 255)), (50, 50))
        screen.blit(font.render(f"HIGH: {high_score}", True, (200, 200, 200)), (50, 90))
        screen.blit(font.render("NEXT:", True, (255, 255, 255)), (width - 200, 50))
        
        # Draw Next Piece
        if not game_over:
            for px, py in next_piece["shape"]:
                pygame.draw.rect(screen, next_piece["color"], (width - 150 + px*BLOCK, 100 + py*BLOCK, BLOCK-1, BLOCK-1))

        if game_over:
            txt = font.render("GAME OVER - ENTER TO RESTART", True, (255, 50, 50))
            screen.blit(txt, (width//2 - txt.get_width()//2, height//2))

        pygame.display.flip()