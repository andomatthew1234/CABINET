import pygame
import math

def draw_effect(screen, rect, ticks):
    """Draws a sliding, jumping, and rotating Geometry Dash cube."""
    screen.set_clip(rect)
    
    # Timing and positioning
    loop_timeline = ticks % 120
    progress = loop_timeline / 120.0  # 0.0 to 1.0
    
    # Move horizontally across the card
    start_x = rect.left - 50
    end_x = rect.right + 50
    current_x = start_x + (end_x - start_x) * progress
    
    # Calculate a simple jump arc using sine
    jump_arc = abs(math.sin(progress * math.pi * 4)) # 4 jumps per cycle
    base_y = rect.bottom - 40
    current_y = base_y - (jump_arc * 40)
    
    # Rotate while in the air, snap when on ground
    if jump_arc > 0.05:
        angle = (ticks * -6) % 360
    else:
        angle = 0
        
    # Render the cube on a temporary surface to handle rotation
    cube_size = 30
    temp_surf = pygame.Surface((cube_size * 2, cube_size * 2), pygame.SRCALPHA)
    
    # Inner and outer cube colors
    pygame.draw.rect(temp_surf, (0, 255, 255), (cube_size//2, cube_size//2, cube_size, cube_size))
    pygame.draw.rect(temp_surf, (255, 255, 255), (cube_size//2, cube_size//2, cube_size, cube_size), 3)
    
    # Rotate
    rotated_cube = pygame.transform.rotate(temp_surf, angle)
    cube_rect = rotated_cube.get_rect(center=(int(current_x), int(current_y)))
    
    # Draw floor line
    pygame.draw.line(screen, (255, 255, 255), (rect.left, base_y + 15), (rect.right, base_y + 15), 2)
    
    # Composite onto launcher
    screen.blit(rotated_cube, cube_rect.topleft)
    
    screen.set_clip(None)