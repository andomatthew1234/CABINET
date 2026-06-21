
import pygame
import math

def draw_effect(screen, rect, ticks):
    screen.set_clip(rect)
    
    # Tiny Paddles
    pad_h = 20
    p1_y = rect.centery + math.sin(ticks * 0.1) * 15 - pad_h//2
    p2_y = rect.centery + math.cos(ticks * 0.1) * 15 - pad_h//2
    
    pygame.draw.rect(screen, (255, 255, 255), (rect.left + 15, p1_y, 4, pad_h))
    pygame.draw.rect(screen, (255, 255, 255), (rect.right - 19, p2_y, 4, pad_h))
    
    # Ball bouncing logic
    cycle = 120
    t = ticks % cycle
    if t < cycle // 2:
        bx = rect.left + 19 + (t / (cycle/2)) * (rect.width - 38)
    else:
        bx = rect.right - 19 - ((t - cycle/2) / (cycle/2)) * (rect.width - 38)
        
    by = rect.centery + math.sin(ticks * 0.05) * 15
    
    pygame.draw.rect(screen, (0, 240, 255), (int(bx) - 3, int(by) - 3, 6, 6))
    screen.set_clip(None)