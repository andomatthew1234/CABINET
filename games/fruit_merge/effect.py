import pygame
import math

def draw_effect(screen, rect, ticks):
    """Draws a bouncing, pulsing watermelon on the right side of the card."""
    # 1. Protect layout canvas with clipping mask
    screen.set_clip(rect)
    
    # 2. Establish anchoring anchors
    center_x = rect.right - 60
    
    # Calculate a bouncy sine wave for the Y position
    bounce_speed = 4
    bounce_height = 20
    y_offset = abs(math.sin(ticks / (60.0 / bounce_speed))) * bounce_height
    center_y = rect.centery + 10 - y_offset
    
    # Calculate a pulsing radius
    pulse_cycle = ticks % 120
    pulse_scale = math.sin(pulse_cycle / 120.0 * math.pi) * 3
    radius = 25 + pulse_scale
    
    # 3. Render using a workspace canvas for clean transparency
    temp_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
    
    # Draw Watermelon (Green outer, red inner)
    pygame.draw.circle(temp_surf, (34, 139, 34), (50, 50), radius) # Rind
    pygame.draw.circle(temp_surf, (255, 69, 0), (50, 50), radius - 4) # Flesh
    
    # Draw seeds
    pygame.draw.circle(temp_surf, (20, 20, 20), (45, 45), 2)
    pygame.draw.circle(temp_surf, (20, 20, 20), (55, 45), 2)
    pygame.draw.circle(temp_surf, (20, 20, 20), (50, 55), 2)
    
    # 4. Composite back onto launcher display matrix
    screen.blit(temp_surf, (center_x - 50, center_y - 50))
    
    # 5. Release clip to preserve master launcher frame stack
    screen.set_clip(None)