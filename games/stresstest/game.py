import pygame
import multiprocessing
import math
import collections
import time

# Attempt to load psutil for live hardware graphing
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

pygame.init()

# --- THE WORKER PAYLOAD ---
def cpu_burner(stop_event):
    """Infinite loop of heavy floating-point exponentiation."""
    while not stop_event.is_set():
        v = 1.0000001
        for _ in range(100000):
            v **= 1.0000001

def main(*args):
    if args and isinstance(args[0], pygame.Surface):
        screen = args[0]
    else:
        screen = pygame.display.set_mode((1000, 650))
        
    pygame.display.set_caption("System Stress Test")
    clock = pygame.time.Clock()
    
    # Fonts
    font_title = pygame.font.SysFont("Courier New", 50, bold=True)
    font_large = pygame.font.SysFont("Courier New", 36, bold=True)
    font_small = pygame.font.SysFont("Courier New", 20, bold=True)

    # --- Setup Variables ---
    state = "CONFIRM" # States: CONFIRM, SPAWNING, RUNNING, COOLDOWN
    PROCESS_COUNT = 128
    
    stop_event = multiprocessing.Event()
    processes = []
    
    # Graphing data
    cpu_history = collections.deque([0]*100, maxlen=100)
    last_graph_update = time.time()
    
    running = True
    ticks = 0

    while running:
        ticks += 1
        mx, my = pygame.mouse.get_pos()
        clicked = False
        
        # --- Event Loop ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == "RUNNING":
                        state = "COOLDOWN"
                    else:
                        running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True

        # --- Update Telemetry ---
        if HAS_PSUTIL and time.time() - last_graph_update > 0.1:
            cpu_history.append(psutil.cpu_percent())
            last_graph_update = time.time()

        # --- Draw Logic by State ---
        if state == "CONFIRM":
            screen.fill((15, 15, 20))
            
            title = font_title.render("WARNING: MAXIMUM LOAD TEST", True, (255, 50, 50))
            screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 100))
            
            warn_txt = font_small.render(f"This will spawn {PROCESS_COUNT} parallel threads to redline your CPU.", True, (200, 200, 200))
            screen.blit(warn_txt, (screen.get_width()//2 - warn_txt.get_width()//2, 180))
            
            # Start Button
            btn_w, btn_h = 300, 60
            start_rect = pygame.Rect(screen.get_width()//2 - btn_w//2, 350, btn_w, btn_h)
            
            hover = start_rect.collidepoint(mx, my)
            btn_color = (255, 0, 0) if hover else (150, 0, 0)
            
            pygame.draw.rect(screen, btn_color, start_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 100, 100), start_rect, width=3, border_radius=8)
            
            start_txt = font_large.render("START STRESS", True, (255, 255, 255))
            screen.blit(start_txt, (start_rect.centerx - start_txt.get_width()//2, start_rect.centery - start_txt.get_height()//2))
            
            if hover and clicked:
                state = "SPAWNING"
                
        elif state == "SPAWNING":
            # Force a render update before the GIL freezes to spawn processes
            screen.fill((50, 0, 0))
            spawn_txt = font_title.render(f"IGNITING {PROCESS_COUNT} THREADS...", True, (255, 255, 0))
            screen.blit(spawn_txt, (screen.get_width()//2 - spawn_txt.get_width()//2, screen.get_height()//2))
            pygame.display.flip()
            
            for _ in range(PROCESS_COUNT):
                p = multiprocessing.Process(target=cpu_burner, args=(stop_event,))
                p.daemon = True
                p.start()
                processes.append(p)
                
            state = "RUNNING"
            
        elif state == "RUNNING":
            # Aggressive pulsing background
            bg_red = int(20 + abs(math.sin(ticks * 0.1)) * 40)
            screen.fill((bg_red, 0, 0))
            
            header = font_large.render("SYSTEM STRESS TEST ACTIVE", True, (255, 255, 255))
            screen.blit(header, (screen.get_width()//2 - header.get_width()//2, 30))
            
            # --- Draw CPU Graph ---
            graph_rect = pygame.Rect(100, 120, 800, 300)
            pygame.draw.rect(screen, (10, 10, 15), graph_rect)
            pygame.draw.rect(screen, (0, 255, 255), graph_rect, width=2)
            
            if HAS_PSUTIL:
                # Draw grid lines
                for i in range(1, 4):
                    y_line = graph_rect.bottom - (i * 0.25 * graph_rect.height)
                    pygame.draw.line(screen, (40, 40, 50), (graph_rect.left, y_line), (graph_rect.right, y_line))
                
                # Draw data line
                points = []
                for i, val in enumerate(cpu_history):
                    x = graph_rect.left + (i * (graph_rect.width / max(1, len(cpu_history)-1)))
                    y = graph_rect.bottom - (val / 100.0 * graph_rect.height)
                    points.append((x, y))
                
                if len(points) > 1:
                    pygame.draw.lines(screen, (0, 255, 100), False, points, 3)
                    
                # Current Load Text
                current_load = cpu_history[-1]
                load_txt = font_large.render(f"CPU LOAD: {current_load}%", True, (0, 255, 100))
                screen.blit(load_txt, (100, 430))
            else:
                err_txt = font_small.render("pip install psutil to view live graph.", True, (150, 150, 150))
                screen.blit(err_txt, (graph_rect.centerx - err_txt.get_width()//2, graph_rect.centery))

            threads_txt = font_small.render(f"ACTIVE THREADS: {PROCESS_COUNT}", True, (255, 150, 150))
            screen.blit(threads_txt, (screen.get_width() - 300, 440))
            
            # --- Stop Button ---
            btn_w, btn_h = 400, 60
            stop_rect = pygame.Rect(screen.get_width()//2 - btn_w//2, 530, btn_w, btn_h)
            
            hover = stop_rect.collidepoint(mx, my)
            btn_color = (255, 255, 0) if hover else (200, 200, 0)
            
            pygame.draw.rect(screen, btn_color, stop_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), stop_rect, width=3, border_radius=8)
            
            stop_txt = font_large.render("STOP ALL STRESS TEST", True, (0, 0, 0))
            screen.blit(stop_txt, (stop_rect.centerx - stop_txt.get_width()//2, stop_rect.centery - stop_txt.get_height()//2))
            
            if hover and clicked:
                state = "COOLDOWN"
                
        elif state == "COOLDOWN":
            screen.fill((0, 20, 0))
            cool_txt = font_title.render("COOLING DOWN...", True, (0, 255, 100))
            term_txt = font_small.render("Terminating background processes.", True, (200, 255, 200))
            screen.blit(cool_txt, (screen.get_width()//2 - cool_txt.get_width()//2, screen.get_height()//2 - 30))
            screen.blit(term_txt, (screen.get_width()//2 - term_txt.get_width()//2, screen.get_height()//2 + 30))
            pygame.display.flip()
            
            stop_event.set()
            for p in processes:
                p.join()
                
            running = False # Exit back to launcher

        # Only flip if we aren't bypassing the event loop in spawning/cooldown
        if state not in ["SPAWNING", "COOLDOWN"]:
            pygame.display.flip()
        
        clock.tick(60)

    # Backup cleanup in case of hard exit
    stop_event.set()
    for p in processes:
        if p.is_alive():
            p.join()

    if not args:
        pygame.quit()

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    main()