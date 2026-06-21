import pygame
import math

def draw_effect(screen, rect, ticks):
    """Draws a pulsing synthwave sun and scrolling horizon grid."""
    
    # 1. Protect layout canvas with clipping mask
    screen.set_clip(rect)
    
    # Anchors
    center_x = rect.right - 80
    center_y = rect.centery - 10
    
    # 2. Draw Glowing Synthwave Sun
    sun_radius = 45
    pulse = math.sin(ticks * 0.05) * 5
    sun_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
    
    # Outer Glow
    pygame.draw.circle(sun_surf, (255, 50, 150, 50), (60, 60), sun_radius + pulse + 10)
    # Core Sun
    pygame.draw.circle(sun_surf, (255, 200, 50, 255), (60, 60), sun_radius)
    
    # Cut Outrun-style grid lines into the sun
    # THE FIX: Create an invisible "eraser" surface and blit it to cut the transparent lines
    for i in range(5):
        line_y = 70 + (i * 10)
        thickness = 2 + (i * 2)
        
        eraser = pygame.Surface((120, thickness), pygame.SRCALPHA)
        eraser.fill((0, 0, 0, 0)) # Fill with absolute transparency
        
        # BLEND_RGBA_MIN forces the overlapping sun pixels to become transparent
        sun_surf.blit(eraser, (0, line_y), special_flags=pygame.BLEND_RGBA_MIN)
        
    screen.blit(sun_surf, (center_x - 60, center_y - 60))

    # 3. Draw Scrolling Horizon Grid (Perspective Floor)
    grid_y_start = center_y + 35
    grid_height = rect.bottom - grid_y_start
    
    # Move horizontal lines down simulating forward movement
    speed = (ticks * 2) % 20
    
    # Horizontal grid lines
    for i in range(1, 6):
        # Exponential spacing to simulate depth (i ** 2)
        y_offset = int((i ** 2) * 1.5) + speed
        if y_offset < grid_height:
            pygame.draw.line(screen, (0, 255, 255), (rect.left, grid_y_start + y_offset), (rect.right, grid_y_start + y_offset), 2)
            
    # Vertical perspective lines spreading outward
    for i in range(-5, 6):
        x_bottom = center_x + (i * 40)
        pygame.draw.line(screen, (0, 150, 255), (center_x, grid_y_start), (x_bottom, rect.bottom), 1)

    # 4. Release clip to preserve master launcher frame stack
    screen.set_clip(None)