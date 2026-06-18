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
        # Navigate up from games/water_sort/game.py to the root /music/ directory
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

LIQUID_COLORS = [(255,0,0), (0,0,255), (0,255,0), (255,255,0), (255,165,0), (128,0,128)]

def generate_level(num_full):
    tubes = [[c, c, c, c] for c in range(num_full)] + [[], []]
    for _ in range(num_full * 20):
        src = random.randint(0, len(tubes)-1)
        dst = random.randint(0, len(tubes)-1)
        if src != dst and len(tubes[src]) > 0 and len(tubes[dst]) < 4:
            tubes[dst].append(tubes[src].pop())
    return tubes

def main(screen):
    # Ensure mixer is initialized and play the Water Sort soundtrack
    pygame.mixer.init()
    play_sound("water_sort.mp3", loop=-1, volume=0.5)

    width, height = screen.get_size()
    pygame.display.set_caption("Water Sort")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 28, bold=True)
    small_font = pygame.font.SysFont("Courier New", 20, bold=True)

    config = load_config()
    high_score = config.get("high_score", 0)
    level_score = 0

    num_colors = 3
    tubes = generate_level(num_colors)
    selected = None
    level_complete = False

    TUBE_W, TUBE_H = 60, 200
    GAP = 40

    def check_win():
        for t in tubes:
            if len(t) > 0 and (len(t) < 4 or len(set(t)) != 1): return False
        return True

    def interact_tube(i):
        nonlocal selected, level_complete
        if selected is None:
            if len(tubes[i]) > 0: 
                selected = i
                play_sound("move.mp3") # Play move sound on selection
        else:
            if selected != i and len(tubes[i]) < 4:
                src_color = tubes[selected][-1]
                if len(tubes[i]) == 0 or tubes[i][-1] == src_color:
                    # Move all matching contiguous blocks instantly
                    while len(tubes[selected]) > 0 and tubes[selected][-1] == src_color and len(tubes[i]) < 4:
                        tubes[i].append(tubes[selected].pop())
                    play_sound("launch.mp3") # Play launch sound on successful pour
                else:
                    play_sound("move.mp3") # Play move sound on invalid pour/deselect
            else:
                play_sound("move.mp3") # Play move sound on deselecting same tube
            selected = None
            
        if check_win(): 
            level_complete = True

    running = True
    while running:
        screen.fill((30, 30, 40))
        
        start_x = (width - (len(tubes) * TUBE_W + (len(tubes)-1) * GAP)) // 2
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                play_sound("exit.mp3")
                pygame.time.wait(200)
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    play_sound("exit.mp3")
                    pygame.time.wait(200) # Give the exit sound a moment to play
                    running = False
                
                # Keyboard Controls (1-9)
                if pygame.K_1 <= event.key <= pygame.K_9 and not level_complete:
                    idx = event.key - pygame.K_1
                    if idx < len(tubes):
                        interact_tube(idx)

                if event.key == pygame.K_r and not level_complete:
                    play_sound("launch.mp3")
                    tubes = generate_level(num_colors)
                    selected = None
                    
                if event.key == pygame.K_RETURN and level_complete:
                    play_sound("launch.mp3")
                    level_score += 1
                    if level_score > high_score:
                        high_score = level_score
                        config["high_score"] = high_score
                        save_config(config)
                    num_colors = min(6, 3 + level_score // 2)
                    tubes = generate_level(num_colors)
                    level_complete = False

            # Mouse Controls
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not level_complete:
                mx, my = event.pos
                for i in range(len(tubes)):
                    tx = start_x + i * (TUBE_W + GAP)
                    ty = height // 2 - TUBE_H // 2
                    if tx <= mx <= tx + TUBE_W and ty <= my <= ty + TUBE_H:
                        interact_tube(i)
                        break

        # Draw UI
        screen.blit(font.render(f"SOLVED: {level_score}  HI: {high_score}", True, (255,255,255)), (20, 20))
        screen.blit(font.render("Use numbers 1-9 or Click to pour. 'R' to shuffle.", True, (150,150,150)), (20, 60))

        # Draw Tubes
        for i, t in enumerate(tubes):
            tx = start_x + i * (TUBE_W + GAP)
            ty = height // 2 - TUBE_H // 2
            
            # Highlight selected
            if selected == i: 
                pygame.draw.rect(screen, (255, 255, 255), (tx-5, ty-5, TUBE_W+10, TUBE_H+10), 3, border_radius=8)

            # Draw liquids
            segment_h = TUBE_H // 4
            for j, color_idx in enumerate(t):
                pygame.draw.rect(screen, LIQUID_COLORS[color_idx], (tx, ty + TUBE_H - (j+1)*segment_h, TUBE_W, segment_h))

            # Draw Glass Outline
            pygame.draw.rect(screen, (200, 200, 200), (tx, ty, TUBE_W, TUBE_H), 3, border_bottom_left_radius=10, border_bottom_right_radius=10)

            # Draw Tube Number
            num_surf = small_font.render(str(i + 1), True, (100, 100, 150))
            screen.blit(num_surf, (tx + TUBE_W//2 - num_surf.get_width()//2, ty + TUBE_H + 15))

        if level_complete:
            win_txt = font.render("PUZZLE SOLVED! PRESS ENTER FOR NEXT", True, (50, 255, 50))
            screen.blit(win_txt, (width//2 - win_txt.get_width()//2, height//2 + 150))

        pygame.display.flip()
        clock.tick(60)