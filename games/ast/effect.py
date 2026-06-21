import pygame
import math

def draw_effect(screen, rect, ticks):
    screen.set_clip(rect)
    ship1_y = rect.centery + math.sin(ticks * 0.05) * 20
    ship2_y = rect.centery + math.cos(ticks * 0.07) * 20
    
    pygame.draw.polygon(screen, (0, 240, 255), [(rect.left + 15, ship1_y - 8), (rect.left + 35, ship1_y), (rect.left + 15, ship1_y + 8)])
    pygame.draw.polygon(screen, (255, 0, 127), [(rect.right - 15, ship2_y - 8), (rect.right - 35, ship2_y), (rect.right - 15, ship2_y + 8)])
    
    bullet_speed = 8
    b1_x = rect.left + 35 + ((ticks * bullet_speed) % (rect.width - 50))
    pygame.draw.line(screen, (0, 255, 100), (b1_x, ship1_y), (b1_x + 10, ship1_y), 2)
    
    b2_x = rect.right - 35 - (((ticks + 20) * (bullet_speed + 1)) % (rect.width - 50))
    pygame.draw.line(screen, (255, 200, 0), (b2_x, ship2_y), (b2_x - 10, ship2_y), 2)
    screen.set_clip(None)