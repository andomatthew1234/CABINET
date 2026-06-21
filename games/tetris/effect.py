import pygame

def draw_effect(screen, rect, ticks):
    screen.set_clip(rect)
    
    cycle = 100
    t = ticks % cycle
    
    # Drop from top to bottom
    drop_y = rect.top - 20 + (t / cycle) * (rect.height + 40)
    
    # Draw an animated neon 'T' piece dropping on the right side
    color = (200, 0, 255)
    blocks = [(0, 0), (-10, 0), (10, 0), (0, 10)]
    base_x = rect.right - 50
    
    for bx, by in blocks:
        pygame.draw.rect(screen, color, (base_x + bx, drop_y + by, 9, 9), border_radius=1)
        
    screen.set_clip(None)