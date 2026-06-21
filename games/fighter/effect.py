import pygame

def draw_effect(screen, rect, ticks):
    loop_t = ticks % 60
    progress = loop_t / 30.0 
    
    if progress <= 1.0:
        p1_x = rect.left + (rect.w * progress)
        pygame.draw.circle(screen, (0, 200, 255), (int(p1_x), rect.top), 6)
        pygame.draw.circle(screen, (255, 255, 255), (int(p1_x), rect.top), 3)
        
        p2_x = rect.right - (rect.w * progress)
        pygame.draw.circle(screen, (255, 100, 0), (int(p2_x), rect.bottom), 6)
        pygame.draw.circle(screen, (255, 255, 255), (int(p2_x), rect.bottom), 3)
    else:
        explosion_rad = int(max(0, (2.0 - progress) * 15))
        if explosion_rad > 0:
            pygame.draw.circle(screen, (255, 255, 255), (rect.right, rect.top), explosion_rad)
            pygame.draw.circle(screen, (255, 200, 0), (rect.right, rect.top), int(explosion_rad * 0.7))
            pygame.draw.circle(screen, (255, 255, 255), (rect.left, rect.bottom), explosion_rad)
            pygame.draw.circle(screen, (255, 200, 0), (rect.left, rect.bottom), int(explosion_rad * 0.7))