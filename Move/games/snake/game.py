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
        # Navigate up from games/snake/game.py to the root /music/ directory
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
    # Ensure mixer is initialized and play the Snake soundtrack
    pygame.mixer.init()
    play_sound("snake.mp3", loop=-1, volume=0.5)

    width, height = screen.get_size()
    pygame.display.set_caption("Toxic Snake")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier New", 30, bold=True)

    config = load_config()
    high_score = config.get("high_score", 0)

    CELL = 25
    cols, rows = width // CELL, height // CELL

    def spawn_food(snake, obstacles):
        while True:
            pos = (random.randint(0, cols-1), random.randint(0, rows-1))
            if pos not in snake and pos not in obstacles: return pos

    snake = [(cols//2, rows//2)]
    dx, dy = 1, 0
    food = spawn_food(snake, [])
    obstacles = []
    score = 0
    game_over = False

    # Timers to control speed
    move_delay = 100
    last_move = pygame.time.get_ticks()

    running = True
    while running:
        screen.fill((15, 20, 15))
        
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
                    snake = [(cols//2, rows//2)]
                    dx, dy = 1, 0
                    obstacles = []
                    score = 0
                    food = spawn_food(snake, obstacles)
                    game_over = False
                if not game_over:
                    moved = False
                    if event.key in (pygame.K_UP, pygame.K_w) and dy != 1: 
                        dx, dy = 0, -1
                        moved = True
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and dy != -1: 
                        dx, dy = 0, 1
                        moved = True
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and dx != 1: 
                        dx, dy = -1, 0
                        moved = True
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and dx != -1: 
                        dx, dy = 1, 0
                        moved = True
                        
                    if moved:
                        play_sound("move.mp3")

        now = pygame.time.get_ticks()
        if not game_over and now - last_move > move_delay:
            last_move = now
            head_x, head_y = snake[0][0] + dx, snake[0][1] + dy
            new_head = (head_x, head_y)

            # Collisions
            if (head_x < 0 or head_x >= cols or head_y < 0 or head_y >= rows or 
                new_head in snake or new_head in obstacles):
                game_over = True
                if score > high_score:
                    high_score = score
                    config["high_score"] = high_score
                    save_config(config)
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    play_sound("launch.mp3") # Use launch sound as a reward for eating
                    score += 1
                    move_delay = max(40, 100 - (score * 2)) # Speed up
                    if score % 5 == 0:
                        obstacles.append(spawn_food(snake, obstacles)) # Spawn poison
                    food = spawn_food(snake, obstacles)
                else:
                    snake.pop()

        # Draw Grid Background (subtle)
        for x in range(0, width, CELL): pygame.draw.line(screen, (30, 35, 30), (x, 0), (x, height))
        for y in range(0, height, CELL): pygame.draw.line(screen, (30, 35, 30), (0, y), (width, y))

        # Draw Obstacles (Purple)
        for obs in obstacles:
            pygame.draw.rect(screen, (150, 0, 200), (obs[0]*CELL, obs[1]*CELL, CELL, CELL), border_radius=4)

        # Draw Food (Red)
        pygame.draw.rect(screen, (255, 50, 50), (food[0]*CELL, food[1]*CELL, CELL, CELL), border_radius=10)

        # Draw Snake (Green)
        for i, segment in enumerate(snake):
            color = (50, 255, 50) if i == 0 else (0, 180, 0)
            pygame.draw.rect(screen, color, (segment[0]*CELL, segment[1]*CELL, CELL, CELL), border_radius=4)

        # UI
        ui_text = font.render(f"SCORE: {score}  HI: {high_score}", True, (255, 255, 255))
        screen.blit(ui_text, (10, 10))

        if game_over:
            go_text = font.render("CRASHED! PRESS ENTER TO RESTART", True, (255, 50, 50))
            screen.blit(go_text, (width//2 - go_text.get_width()//2, height//2))

        pygame.display.flip()
        clock.tick(60)