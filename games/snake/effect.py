import pygame

def draw_effect(screen, rect, ticks):
    perimeter = (rect.w * 2) + (rect.h * 2)
    s_pos = (ticks * 4) % perimeter
    def get_perimeter_pt(p):
        if p < rect.w: return rect.x + p, rect.y
        p -= rect.w
        if p < rect.h: return rect.right, rect.y + p
        p -= rect.h
        if p < rect.w: return rect.right - p, rect.bottom
        p -= rect.w
        return rect.x, rect.bottom - p
    for seg in range(4):
        pt = get_perimeter_pt((s_pos - (seg * 12)) % perimeter)
        pygame.draw.rect(screen, (0, 255, 100), (pt[0] - 4, pt[1] - 4, 8, 8), border_radius=2)