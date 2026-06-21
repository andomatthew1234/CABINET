import pygame

def draw_effect(screen, rect, ticks):
    screen.set_clip(rect)
    
    grid_size = 5
    cell_s = 14
    grid_w = grid_size * cell_s
    grid_x = rect.right - grid_w - 30
    grid_y = rect.centery - (grid_w // 2)
    
    # Draw empty background grid
    for r in range(grid_size):
        for c in range(grid_size):
            pygame.draw.rect(screen, (30, 30, 40), (grid_x + c*cell_s, grid_y + r*cell_s, cell_s-1, cell_s-1), border_radius=2)
            
    t = ticks % 120
    
    shape = [(0,0), (0,1), (0,2), (1,2)] # An inverted 'L' shape
    color = (0, 255, 150)
    
    if t < 50:
        # Hovering/dropping phase
        offset_y = -30 + (t / 50.0) * 30
        for r, c in shape:
            pygame.draw.rect(screen, color, (grid_x + c*cell_s, grid_y + r*cell_s + offset_y, cell_s-1, cell_s-1), border_radius=2)
    elif t < 90:
        # Snapped in place
        for r, c in shape:
            pygame.draw.rect(screen, color, (grid_x + c*cell_s, grid_y + r*cell_s, cell_s-1, cell_s-1), border_radius=2)
        
        # Flash the cleared line
        if (t // 5) % 2 == 0:
            for c in range(grid_size):
                pygame.draw.rect(screen, (255, 255, 255), (grid_x + c*cell_s, grid_y + 2*cell_s, cell_s-1, cell_s-1), border_radius=2)
    else:
        # Cleared state (bottom block of the L is gone)
        for r, c in [(0,0), (0,1), (0,2)]:
            pygame.draw.rect(screen, color, (grid_x + c*cell_s, grid_y + r*cell_s, cell_s-1, cell_s-1), border_radius=2)

    screen.set_clip(None)