import pygame
import math

def draw_effect(screen, rect, ticks):
    """Draws an aggressive pulsing hazard warning."""
    screen.set_clip(rect)
    
    center_x = rect.right - 60
    center_y = rect.centery
    
    # Aggressive pulsing math
    pulse_cycle = ticks % 30
    pulse_scale = math.sin(pulse_cycle / 30.0 * math.pi)
    alpha = int(100 + (155 * pulse_scale))
    radius = 30 + (pulse_scale * 5)
    
    temp_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
    
    # Draw hazard backdrop
    pygame.draw.circle(temp_surf, (255, 0, 0, alpha), (50, 50), radius)
    pygame.draw.circle(temp_surf, (50, 0, 0, 255), (50, 50), radius - 5)
    
    # Draw exclamation mark
    pygame.draw.rect(temp_surf, (255, 0, 0, alpha), (46, 25, 8, 30))
    pygame.draw.circle(temp_surf, (255, 0, 0, alpha), (50, 65), 5)
    
    screen.blit(temp_surf, (center_x - 50, center_y - 50))
    screen.set_clip(None)