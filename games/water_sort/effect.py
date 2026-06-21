import pygame

def draw_effect(screen, rect, ticks):
    for thick in range(3, 0, -1):
        hue = (ticks * 3 + thick * 20) % 360
        color = pygame.Color(0)
        color.hsva = (hue, 100, 100, 100)
        pygame.draw.rect(screen, color, rect.inflate(thick * 2, thick * 2), width=1, border_radius=8 + thick)