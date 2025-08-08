import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from simulation.world import World

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    world = World()
    pygame.display.set_caption("Evolution Simulation")

    
    running = True
    while running:
        screen.fill((0, 255, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                world.log_file.close()
                running = False
        
        world.update()
        world.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()
    
if __name__ == "__main__":
    main()