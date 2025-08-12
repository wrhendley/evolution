import pygame
import matplotlib.pyplot as plt
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
            if event.type == pygame.QUIT or world.creatures == []:
                # world.log_file.close()
                running = False
        
        world.update()
        world.draw(screen)
        
        pygame.display.flip()
        clock.tick(480)
        
    plot_data(world)
    pygame.quit()

def plot_data(world):
    frames = [entry[0] for entry in world.history]
    vision = [entry[1] for entry in world.history]
    speed = [entry[2] for entry in world.history]
    metabolism = [entry[3] for entry in world.history]
    total_food = [entry[4] for entry in world.history]
    total_population = [entry[5] for entry in world.history]

    fig, ax1 = plt.subplots()
    color1 = 'tab:blue'
    ax1.set_xlabel('Frame')
    ax1.set_ylabel('Average Vision', color=color1)
    ax1.plot(frames, vision, color=color1, label='Average Vision')
    ax1.tick_params(axis='y', labelcolor=color1)

    ax2 = ax1.twinx()
    color2 = 'tab:orange'
    ax2.set_ylabel('Average Speed', color=color2)
    ax2.plot(frames, speed, color=color2, label='Average Speed')
    ax2.tick_params(axis='y', labelcolor=color2)

    # Plot metabolism on a third axis
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    color3 = 'tab:purple'
    ax3.set_ylabel('Average Metabolism', color=color3)
    ax3.plot(frames, metabolism, color=color3, label='Average Metabolism', linestyle='solid')
    ax3.tick_params(axis='y', labelcolor=color3)

    # Plot total food and population on a fourth axis
    ax4 = ax1.twinx()
    ax4.spines['right'].set_position(('outward', 120))
    color4 = 'tab:green'
    color5 = 'tab:red'
    ax4.plot(frames, total_food, color=color4, label='Total Food')
    ax4.plot(frames, total_population, color=color5, label='Total Population')
    ax4.set_ylabel('Count', color='black')
    ax4.tick_params(axis='y', labelcolor='black')

    # Combine legends
    lines, labels = [], []
    for ax in [ax1, ax2, ax3, ax4]:
        line, label = ax.get_legend_handles_labels()
        lines += line
        labels += label
    ax1.legend(lines, labels, loc='upper left')

    fig.suptitle('Creature Genes and Population/Food Over Time')
    fig.tight_layout()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()