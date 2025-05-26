import pygame
import sys
import random
import math
from pygame import mixer

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# Game states
WELCOME = 0
PLAYING = 1
GAME_OVER = 2
RULES = 3
SHOP = 4
NAME_ENTRY = 5
PAUSED = 6
CREDITS = 7  # New state for credits screen
game_state = WELCOME

# Game variables
clock = pygame.time.Clock()
FPS = 60
previous_state = WELCOME  # To remember state before pausing
# Player variables
player_size = 50
player_x = WIDTH // 2 - player_size // 2
player_y = HEIGHT - 2 * player_size
player_speed = 5
player_health = 100
player_max_health = 100
player_credits = 0
player_score = 0
player_fire_rate = 0.5  # Seconds between shots
player_last_shot = 0
player_damage = 10
player_bullet_speed = 10
player_name = "Player"  # Default player name
auto_fire = False       # Auto-fire mode toggle

# Ship customization and upgrades
ship_color = BLUE
available_colors = {
    "Blue": BLUE,
    "Red": RED,
    "Green": GREEN,
    "Yellow": YELLOW,
    "Purple": PURPLE,
    "Cyan": CYAN
}
purchased_colors = ["Blue"]  # Start with blue

# Upgrades available in shop
upgrades = {
    "Health +20": {"cost": 50, "effect": "health", "value": 20},
    "Speed +1": {"cost": 30, "effect": "speed", "value": 1},
    "Fire Rate +10%": {"cost": 40, "effect": "fire_rate", "value": 0.1},
    "Damage +5": {"cost": 45, "effect": "damage", "value": 5},
    "Bullet Speed +2": {"cost": 35, "effect": "bullet_speed", "value": 2}
}

# Lists to store game objects
bullets = []
asteroids = []
enemies = []
loots = []
explosions = []

# High scores
high_scores = []
try:
    with open("high_scores.txt", "r") as file:
        for line in file:
            # Extract just the score part (before the dash if it exists)
            score_part = line.strip().split(' - ')[0]
            high_scores.append(int(score_part))
except FileNotFoundError:
    high_scores = [0, 0, 0, 0, 0]  # Default high scores
# Difficulty scaling
difficulty = 1.0
difficulty_increase_rate = 0.05
next_difficulty_increase = 1000  # Score needed for next difficulty increase

# Screen shake variables
shake_intensity = 0
shake_decay = 0.9
shake_offset = [0, 0]

# Asteroid variables
asteroid_spawn_rate = 1.0  # Seconds between asteroid spawns
last_asteroid_spawn = 0
asteroid_min_speed = 2
asteroid_max_speed = 5
asteroid_sizes = [15, 30, 45]  # Small, medium, large

# Enemy variables
enemy_spawn_rate = 5.0  # Seconds between enemy spawns
last_enemy_spawn = 0
enemy_types = [
    {"size": 40, "speed": 2, "health": 30, "damage": 10, "score": 50, "color": RED},
    {"size": 35, "speed": 3, "health": 20, "damage": 15, "score": 75, "color": PURPLE},
    {"size": 30, "speed": 4, "health": 15, "damage": 20, "score": 100, "color": ORANGE}
]

# Reset player position after screen resize
def reset_player_position():
    global player_x, player_y
    player_x = WIDTH // 2 - player_size // 2
    player_y = HEIGHT - 2 * player_size
def update_game():
    global player_x, player_y, player_health, game_state, last_asteroid_spawn, last_enemy_spawn, difficulty, player_score, next_difficulty_increase, auto_fire
    current_time = pygame.time.get_ticks() / 1000  # Convert to seconds
    
    # Player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < WIDTH - player_size:
        player_x += player_speed
    if keys[pygame.K_UP] and player_y > 0:
        player_y -= player_speed
    if keys[pygame.K_DOWN] and player_y < HEIGHT - player_size:
        player_y += player_speed
    
    # Shooting - either manual or auto
    if auto_fire or (keys[pygame.K_SPACE] and current_time - player_last_shot > player_fire_rate):
        if current_time - player_last_shot > player_fire_rate:
            shoot_bullet()
    
    # Spawn asteroids
    if current_time - last_asteroid_spawn > asteroid_spawn_rate / difficulty:
        spawn_asteroid()
        last_asteroid_spawn = current_time
    
    # Spawn enemies
    if current_time - last_enemy_spawn > enemy_spawn_rate / difficulty:
        spawn_enemy()
        last_enemy_spawn = current_time
    
    # Update game objects
    update_asteroids()
    update_bullets()
    update_enemies()
    update_loots()
    
    # Check collisions
    check_collisions()
    
    # Update difficulty
    if player_score >= next_difficulty_increase:
        difficulty += difficulty_increase_rate
        next_difficulty_increase += 1000
    
    # Check if player is dead
    if player_health <= 0:
        game_state = GAME_OVER
        save_high_score()
def shoot_bullet():
    global player_last_shot
    player_last_shot = pygame.time.get_ticks() / 1000
    bullet = {
        'x': player_x + player_size // 2 - 2,
        'y': player_y,
        'speed': player_bullet_speed,
        'damage': player_damage,
        'width': 4,
        'height': 10
    }
    bullets.append(bullet)
    # Add sound effect here later

def spawn_asteroid():
    size_index = random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2], k=1)[0]
    size = asteroid_sizes[size_index]
    asteroid = {
        'x': random.randint(0, WIDTH - size),
        'y': -size,
        'size': size,
        'speed': random.uniform(asteroid_min_speed, asteroid_max_speed),
        'rotation': 0,
        'rotation_speed': random.uniform(-3, 3),
        'health': size // 5
    }
    asteroids.append(asteroid)

def spawn_enemy():
    # Choose enemy type based on difficulty
    weights = [max(0, 1 - difficulty/5), min(1, difficulty/3), min(0.5, difficulty/10)]
    enemy_index = random.choices(range(len(enemy_types)), weights=weights, k=1)[0]
    enemy_type = enemy_types[enemy_index]
    
    enemy = {
        'x': random.randint(0, WIDTH - enemy_type["size"]),
        'y': -enemy_type["size"],
        'size': enemy_type["size"],
        'speed': enemy_type["speed"],
        'health': enemy_type["health"] * difficulty,
        'damage': enemy_type["damage"],
        'score': enemy_type["score"],
        'color': enemy_type["color"],
        'last_shot': 0,
        'fire_rate': 2.0 / difficulty  # Seconds between shots
    }
    enemies.append(enemy)
def update_asteroids():
    for asteroid in asteroids[:]:
        asteroid['y'] += asteroid['speed']
        asteroid['rotation'] += asteroid['rotation_speed']
        
        # Remove if off screen
        if asteroid['y'] > HEIGHT:
            asteroids.remove(asteroid)

def update_bullets():
    for bullet in bullets[:]:
        bullet['y'] -= bullet['speed']
        
        # Remove if off screen
        if bullet['y'] < 0:
            bullets.remove(bullet)

def update_enemies():
    current_time = pygame.time.get_ticks() / 1000
    
    for enemy in enemies[:]:
        # Move enemy
        enemy['y'] += enemy['speed']
        
        # Enemy shooting
        if current_time - enemy['last_shot'] > enemy['fire_rate']:
            enemy_bullet = {
                'x': enemy['x'] + enemy['size'] // 2 - 2,
                'y': enemy['y'] + enemy['size'],
                'speed': -5,  # Negative because it goes down
                'damage': enemy['damage'],
                'width': 4,
                'height': 10,
                'enemy': True  # Flag to identify enemy bullets
            }
            bullets.append(enemy_bullet)
            enemy['last_shot'] = current_time
        
        # Remove if off screen
        if enemy['y'] > HEIGHT:
            enemies.remove(enemy)

def update_loots():
    global player_health, player_credits, player_max_health, player_score
    
    for loot in loots[:]:
        loot['y'] += loot['speed']
        
        # Remove if off screen
        if loot['y'] > HEIGHT:
            loots.remove(loot)
            continue
        
        # Check collision with player
        if (player_x < loot['x'] + loot['width'] and
            player_x + player_size > loot['x'] and
            player_y < loot['y'] + loot['height'] and
            player_y + player_size > loot['y']):
            
            # Apply loot effect
            if loot['type'] == 'health':
                player_health = min(player_health + loot['value'], player_max_health)
            else:  # credits
                player_credits += loot['value']
                player_score += 10  # Add 10 points when collecting credits
            
            # Remove loot
            loots.remove(loot)
def check_collisions():
    global player_health, player_score, player_credits, shake_intensity
    
    # Check bullet-asteroid collisions
    for bullet in bullets[:]:
        # Skip enemy bullets
        if bullet.get('enemy', False):
            continue
            
        for asteroid in asteroids[:]:
            if (bullet['x'] < asteroid['x'] + asteroid['size'] and
                bullet['x'] + bullet['width'] > asteroid['x'] and
                bullet['y'] < asteroid['y'] + asteroid['size'] and
                bullet['y'] + bullet['height'] > asteroid['y']):
                
                # Damage asteroid
                asteroid['health'] -= bullet['damage']
                
                # Remove bullet
                if bullet in bullets:
                    bullets.remove(bullet)
                
                # If asteroid destroyed
                if asteroid['health'] <= 0:
                    player_score += asteroid['size']
                    
                    # Chance to drop loot
                    if random.random() < 0.3:
                        spawn_loot(asteroid['x'], asteroid['y'])
                    
                    # Remove asteroid
                    asteroids.remove(asteroid)
                    
                    # Add explosion effect
                    trigger_screen_shake(asteroid['size'] / 10)
                break
    
    # Check bullet-enemy collisions
    for bullet in bullets[:]:
        # Skip enemy bullets
        if bullet.get('enemy', False):
            continue
            
        for enemy in enemies[:]:
            if (bullet['x'] < enemy['x'] + enemy['size'] and
                bullet['x'] + bullet['width'] > enemy['x'] and
                bullet['y'] < enemy['y'] + enemy['size'] and
                bullet['y'] + bullet['height'] > enemy['y']):
                
                # Damage enemy
                enemy['health'] -= bullet['damage']
                
                # Remove bullet
                if bullet in bullets:
                    bullets.remove(bullet)
                
                # If enemy destroyed
                if enemy['health'] <= 0:
                    player_score += enemy['score']
                    player_credits += enemy['score'] // 10
                    
                    # Chance to drop loot
                    if random.random() < 0.5:
                        spawn_loot(enemy['x'], enemy['y'])
                    
                    # Remove enemy
                    enemies.remove(enemy)
                    
                    # Add explosion effect
                    trigger_screen_shake(5)
                break
    # Check enemy bullet-player collisions
    for bullet in bullets[:]:
        if not bullet.get('enemy', False):
            continue
            
        if (player_x < bullet['x'] + bullet['width'] and
            player_x + player_size > bullet['x'] and
            player_y < bullet['y'] + bullet['height'] and
            player_y + player_size > bullet['y']):
            
            # Player takes damage
            player_health -= bullet['damage']
            
            # Remove bullet
            bullets.remove(bullet)
            
            # Screen shake effect
            trigger_screen_shake(bullet['damage'] / 2)
    
    # Check player-asteroid collisions
    for asteroid in asteroids[:]:
        # Simple circle collision
        distance = math.sqrt((player_x + player_size/2 - asteroid['x'] - asteroid['size']/2)**2 + 
                            (player_y + player_size/2 - asteroid['y'] - asteroid['size']/2)**2)
        
        if distance < (player_size/2 + asteroid['size']/2):
            # Player takes damage based on asteroid size
            damage = asteroid['size'] // 5
            player_health -= damage
            
            # Remove asteroid
            asteroids.remove(asteroid)
            
            # Screen shake effect
            trigger_screen_shake(damage)
    
    # Check player-enemy collisions
    for enemy in enemies[:]:
        # Simple circle collision
        distance = math.sqrt((player_x + player_size/2 - enemy['x'] - enemy['size']/2)**2 + 
                            (player_y + player_size/2 - enemy['y'] - enemy['size']/2)**2)
        
        if distance < (player_size/2 + enemy['size']/2):
            # Player takes damage
            player_health -= enemy['damage']
            
            # Remove enemy
            enemies.remove(enemy)
            
            # Screen shake effect
            trigger_screen_shake(enemy['damage'] / 2)
def spawn_loot(x, y):
    loot_type = random.choices(['health', 'credits'], weights=[0.3, 0.7], k=1)[0]
    value = 0
    
    if loot_type == 'health':
        value = random.randint(5, 20)
        color = GREEN
    else:  # credits
        value = random.randint(5, 15)
        color = YELLOW
    
    loot = {
        'x': x,
        'y': y,
        'width': 15,
        'height': 15,
        'speed': 2,
        'type': loot_type,
        'value': value,
        'color': color
    }
    loots.append(loot)
    
    # Add points to score when a loot is spawned
    global player_score
    player_score += 5  # Add 5 points when loot is spawned

def save_high_score():
    global player_score, high_scores, player_name
    
    if player_score > min(high_scores):
        high_scores.append(player_score)
        high_scores.sort(reverse=True)
        high_scores = high_scores[:5]  # Keep only top 5
        
        # Save to file with player name
        with open("high_scores.txt", "w") as file:
            for score in high_scores:
                file.write(f"{score} - {player_name if score == player_score else 'Unknown'}\n")

def trigger_screen_shake(intensity=10):
    global shake_intensity
    shake_intensity = intensity
def draw_game():
    global shake_offset, auto_fire
    
    # Draw stars in background
    for _ in range(20):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(1, 3)
        pygame.draw.circle(screen, WHITE, (x, y), size)
    
    # Draw asteroids
    for asteroid in asteroids:
        pygame.draw.circle(screen, WHITE, 
                          (int(asteroid['x'] + asteroid['size']/2 + shake_offset[0]), 
                           int(asteroid['y'] + asteroid['size']/2 + shake_offset[1])), 
                          asteroid['size']//2)
    
    # Draw enemies
    for enemy in enemies:
        pygame.draw.rect(screen, enemy['color'], 
                        (enemy['x'] + shake_offset[0], 
                         enemy['y'] + shake_offset[1], 
                         enemy['size'], enemy['size']))
    
    # Draw bullets
    for bullet in bullets:
        color = RED if bullet.get('enemy', False) else YELLOW
        pygame.draw.rect(screen, color, 
                        (bullet['x'] + shake_offset[0], 
                         bullet['y'] + shake_offset[1], 
                         bullet['width'], bullet['height']))
    
    # Draw loots
    for loot in loots:
        pygame.draw.rect(screen, loot['color'], 
                        (loot['x'] + shake_offset[0], 
                         loot['y'] + shake_offset[1], 
                         loot['width'], loot['height']))
    
    # Draw player ship (simple triangle for now)
    points = [
        (player_x + player_size//2 + shake_offset[0], player_y + shake_offset[1]),
        (player_x + shake_offset[0], player_y + player_size + shake_offset[1]),
        (player_x + player_size + shake_offset[0], player_y + player_size + shake_offset[1])
    ]
    pygame.draw.polygon(screen, ship_color, points)
    
    # Draw player name at top
    font_small = pygame.font.Font(None, 24)
    player_name_text = font_small.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 10))
    
    # Draw UI elements
    draw_health_bar()
    draw_score()
    draw_credits()
    draw_difficulty()
    # Draw auto-fire status
    font_small = pygame.font.Font(None, 20)
    auto_fire_text = font_small.render(f"Auto-Fire: {'ON' if auto_fire else 'OFF'} (Press F to toggle)", True, 
                                      GREEN if auto_fire else WHITE)
    screen.blit(auto_fire_text, (10, HEIGHT - 30))
    
    # Draw pause hint - more prominent now
    font_medium = pygame.font.Font(None, 24)
    pause_hint = font_medium.render("Press P to Pause Game", True, YELLOW)
    
    # Create a semi-transparent background for the hint
    hint_bg = pygame.Surface((pause_hint.get_width() + 20, pause_hint.get_height() + 10), pygame.SRCALPHA)
    hint_bg.fill((0, 0, 0, 150))  # Semi-transparent black
    
    # Position at the top center of the screen
    hint_x = WIDTH//2 - hint_bg.get_width()//2
    hint_y = 35
    
    # Draw the background and text
    screen.blit(hint_bg, (hint_x, hint_y))
    screen.blit(pause_hint, (hint_x + 10, hint_y + 5))

def draw_health_bar():
    bar_width = 200
    bar_height = 20
    fill_width = (player_health / player_max_health) * bar_width
    
    pygame.draw.rect(screen, RED, (10, 40, bar_width, bar_height), 2)
    pygame.draw.rect(screen, RED, (10, 40, fill_width, bar_height))
    
    font = pygame.font.Font(None, 24)
    health_text = font.render(f"Health: {int(player_health)}/{player_max_health}", True, WHITE)
    screen.blit(health_text, (220, 40))

def draw_score():
    font = pygame.font.Font(None, 24)
    score_text = font.render(f"Score: {player_score}", True, WHITE)
    screen.blit(score_text, (10, 70))

def draw_credits():
    font = pygame.font.Font(None, 24)
    credits_text = font.render(f"Credits: {player_credits}", True, YELLOW)
    screen.blit(credits_text, (10, 100))

def draw_difficulty():
    font = pygame.font.Font(None, 24)
    difficulty_text = font.render(f"Difficulty: {difficulty:.1f}x", True, ORANGE)
    screen.blit(difficulty_text, (WIDTH - 150, 40))
def draw_welcome_screen():
    # Title
    font_large = pygame.font.Font(None, 72)
    title = font_large.render("SPACE SHOOTER", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
    
    # Player name at top
    font_small = pygame.font.Font(None, 24)
    player_name_text = font_small.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 20))
    
    # Instructions
    font_medium = pygame.font.Font(None, 36)
    start_text = font_medium.render("Press ENTER to Start", True, WHITE)
    rules_text = font_medium.render("Press R for Rules", True, WHITE)
    shop_text = font_medium.render("Press S for Shop", True, WHITE)
    name_text = font_medium.render("Press N to Change Name", True, WHITE)
    credits_text = font_medium.render("Press C for Credits", True, WHITE)
    
    screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT//2 - 50))
    screen.blit(rules_text, (WIDTH//2 - rules_text.get_width()//2, HEIGHT//2))
    screen.blit(shop_text, (WIDTH//2 - shop_text.get_width()//2, HEIGHT//2 + 50))
    screen.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT//2 + 100))
    screen.blit(credits_text, (WIDTH//2 - credits_text.get_width()//2, HEIGHT//2 + 150))
    
    # Game tips
    font_small = pygame.font.Font(None, 24)
    tip_text = font_small.render("TIP: Press P during gameplay to pause and access the shop!", True, GREEN)
    tip_text2 = font_small.render("TIP: Press F during gameplay to toggle auto-fire mode!", True, GREEN)
    screen.blit(tip_text, (WIDTH//2 - tip_text.get_width()//2, HEIGHT - 60))
    screen.blit(tip_text2, (WIDTH//2 - tip_text2.get_width()//2, HEIGHT - 30))
    
    # High scores
    high_score_title = font_small.render("HIGH SCORES", True, YELLOW)
    screen.blit(high_score_title, (WIDTH - 200, 50))
    
    # Try to read player names from high_scores.txt
    try:
        with open("high_scores.txt", "r") as file:
            score_lines = file.readlines()
            
        for i, (score, line) in enumerate(zip(high_scores, score_lines[:5])):
            # Display score with player name if available
            score_text = font_small.render(f"{i+1}. {line.strip()}", True, WHITE)
            screen.blit(score_text, (WIDTH - 200, 80 + i * 25))
    except:
        # Fallback to just showing scores
        for i, score in enumerate(high_scores):
            score_text = font_small.render(f"{i+1}. {score}", True, WHITE)
            screen.blit(score_text, (WIDTH - 200, 80 + i * 25))
def draw_rules_screen():
    font_title = pygame.font.Font(None, 48)
    font_text = pygame.font.Font(None, 24)
    
    # Player name at top
    player_name_text = font_text.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 20))
    
    title = font_title.render("GAME RULES", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    rules = [
        "- Use ARROW KEYS to move your ship",
        "- Press SPACE to shoot",
        "- Press F to toggle auto-fire mode",
        "- Avoid or destroy asteroids",
        "- Defeat enemies to earn credits",
        "- Collect power-ups to enhance your ship",
        "- Green items restore health",
        "- Yellow items give credits",
        "- Press P to pause the game and access the shop",
        "- Visit the shop to upgrade your ship",
        "- Survive as long as possible to achieve high score",
        "",
        "Press ESC to return to main menu"
    ]
    
    for i, rule in enumerate(rules):
        rule_text = font_text.render(rule, True, WHITE)
        screen.blit(rule_text, (WIDTH//4, 120 + i * 35))

def draw_game_over_screen():
    font_large = pygame.font.Font(None, 72)
    font_medium = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)
    
    # Player name at top
    player_name_text = font_small.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 20))
    
    game_over_text = font_large.render("GAME OVER", True, RED)
    score_text = font_medium.render(f"Final Score: {player_score}", True, WHITE)
    player_text = font_medium.render(f"Player: {player_name}", True, GREEN)
    credits_text = font_medium.render(f"Credits Earned: {player_credits}", True, YELLOW)
    restart_text = font_medium.render("Press ENTER to Play Again", True, WHITE)
    menu_text = font_medium.render("Press ESC for Main Menu", True, WHITE)
    
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//3 - 50))
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 50))
    screen.blit(player_text, (WIDTH//2 - player_text.get_width()//2, HEIGHT//2))
    screen.blit(credits_text, (WIDTH//2 - credits_text.get_width()//2, HEIGHT//2 + 50))
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 100))
    screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 150))
def draw_credits_screen():
    font_title = pygame.font.Font(None, 48)
    font_text = pygame.font.Font(None, 24)
    font_medium = pygame.font.Font(None, 36)
    
    # Player name at top
    player_name_text = font_text.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 20))
    
    title = font_title.render("CREDITS", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    # Game credits
    credits = [
        "SPACE SHOOTER",
        "",
        "Game Design and Programming:",
        "Krishna Bahadur",
        "",
        "Graphics and Sound:",
        "Open Source Assets",
        "",
        "Special Thanks:",
        "The Pygame Community",
        "All Open Source Contributors",
        "",
        "© 2025 Space Shooter Game",
        "",
        "Press ESC to return to previous screen"
    ]
    
    for i, line in enumerate(credits):
        if i == 0:  # Title line
            credit_text = font_medium.render(line, True, YELLOW)
            screen.blit(credit_text, (WIDTH//2 - credit_text.get_width()//2, 120 + i * 30))
        elif i == 3 or i == 6 or i == 9 or i == 10:  # Names
            credit_text = font_text.render(line, True, GREEN)
            screen.blit(credit_text, (WIDTH//2 - credit_text.get_width()//2, 120 + i * 30))
        elif i == 12:  # Copyright
            credit_text = font_text.render(line, True, CYAN)
            screen.blit(credit_text, (WIDTH//2 - credit_text.get_width()//2, 120 + i * 30))
        elif i == 14:  # Return instruction
            credit_text = font_text.render(line, True, WHITE)
            screen.blit(credit_text, (WIDTH//2 - credit_text.get_width()//2, HEIGHT - 50))
        else:
            credit_text = font_text.render(line, True, WHITE)
            screen.blit(credit_text, (WIDTH//2 - credit_text.get_width()//2, 120 + i * 30))
def handle_shop():
    global player_credits, player_health, player_max_health, player_speed, player_fire_rate, player_damage, player_bullet_speed, ship_color, game_state, previous_state
    
    font_title = pygame.font.Font(None, 48)
    font_text = pygame.font.Font(None, 24)
    
    # Player name at top
    player_name_text = font_text.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 20))
    
    title = font_title.render("SHIP SHOP", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))
    
    credits_text = font_text.render(f"Credits: {player_credits}", True, YELLOW)
    screen.blit(credits_text, (WIDTH//2 - credits_text.get_width()//2, 100))
    
    # Handle mouse input for shop
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]
    
    # Draw upgrades
    y_pos = 150
    for i, (upgrade_name, upgrade_info) in enumerate(upgrades.items()):
        upgrade_rect = pygame.Rect(WIDTH//4, y_pos, WIDTH//2, 40)
        
        # Highlight if mouse is over
        if upgrade_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (50, 50, 50), upgrade_rect)
            if mouse_clicked:
                # Try to purchase
                if player_credits >= upgrade_info["cost"]:
                    player_credits -= upgrade_info["cost"]
                    apply_upgrade(upgrade_info["effect"], upgrade_info["value"])
        else:
            pygame.draw.rect(screen, (30, 30, 30), upgrade_rect)
        
        # Draw upgrade info
        upgrade_text = font_text.render(f"{upgrade_name} - {upgrade_info['cost']} credits", True, WHITE)
        screen.blit(upgrade_text, (WIDTH//4 + 10, y_pos + 10))
        
        y_pos += 50
    
    # Draw ship colors
    y_pos = 150
    for i, (color_name, color_value) in enumerate(available_colors.items()):
        color_rect = pygame.Rect(WIDTH*3//4 + 50, y_pos, 30, 30)
        pygame.draw.rect(screen, color_value, color_rect)
        
        # Check if color is purchased
        if color_name in purchased_colors:
            color_text = font_text.render(f"{color_name} (Owned)", True, WHITE)
            
            # Highlight if this is the current color
            if color_value == ship_color:
                pygame.draw.rect(screen, WHITE, color_rect, 2)
                
            # Allow selection if owned
            if color_rect.collidepoint(mouse_pos) and mouse_clicked:
                ship_color = color_value
        else:
            color_text = font_text.render(f"{color_name} - 25 credits", True, WHITE)
            
            # Allow purchase
            if color_rect.collidepoint(mouse_pos) and mouse_clicked:
                if player_credits >= 25:
                    player_credits -= 25
                    purchased_colors.append(color_name)
                    ship_color = color_value
        
        screen.blit(color_text, (WIDTH*3//4 - 100, y_pos + 5))
        y_pos += 40
    
    # Back button
    if previous_state == PAUSED:
        back_text = font_text.render("Press ESC to return to game", True, WHITE)
    else:
        back_text = font_text.render("Press ESC to return to main menu", True, WHITE)
    screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, HEIGHT - 50))
def apply_upgrade(effect, value):
    global player_max_health, player_health, player_speed, player_fire_rate, player_damage, player_bullet_speed
    
    if effect == "health":
        player_max_health += value
        player_health += value
    elif effect == "speed":
        player_speed += value
    elif effect == "fire_rate":
        player_fire_rate = max(0.1, player_fire_rate * (1 - value))
    elif effect == "damage":
        player_damage += value
    elif effect == "bullet_speed":
        player_bullet_speed += value

def draw_name_entry_screen():
    global player_name
    
    # Title
    font_large = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 24)
    
    # Player name at top
    player_name_text = font_small.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 20))
    
    title = font_large.render("ENTER YOUR NAME", True, GREEN)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
    
    # Current name
    font_medium = pygame.font.Font(None, 36)
    name_text = font_medium.render(f"New Name: {player_name}", True, WHITE)
    screen.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT//2))
    
    # Instructions
    instructions = [
        "Type your name using keyboard",
        "Press ENTER when finished",
        "Press ESC to cancel",
        "Backspace to delete characters"
    ]
    
    for i, instruction in enumerate(instructions):
        text = font_small.render(instruction, True, YELLOW)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 50 + i * 30))

def handle_name_entry(event):
    global player_name, game_state
    
    if event.key == pygame.K_RETURN:
        # Save name and return to welcome screen
        game_state = WELCOME
    elif event.key == pygame.K_ESCAPE:
        # Cancel and return to welcome screen
        game_state = WELCOME
    elif event.key == pygame.K_BACKSPACE:
        # Delete last character
        player_name = player_name[:-1]
    elif len(player_name) < 15:  # Limit name length
        # Add character to name
        if event.unicode.isalnum() or event.unicode in [' ', '_', '-']:
            player_name += event.unicode
def draw_pause_menu():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with alpha
    screen.blit(overlay, (0, 0))
    
    font_large = pygame.font.Font(None, 72)
    font_medium = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)
    
    # Player name at top
    player_name_text = font_small.render(f"Current Player: {player_name}", True, GREEN)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, 20))
    
    pause_text = font_large.render("GAME PAUSED", True, YELLOW)
    resume_text = font_medium.render("Press P to Resume", True, WHITE)
    shop_text = font_medium.render("Press S for Shop", True, WHITE)
    credits_text = font_medium.render("Press C for Credits", True, WHITE)
    menu_text = font_medium.render("Press ESC for Main Menu", True, WHITE)
    player_credits_text = font_medium.render(f"Current Credits: {player_credits}", True, YELLOW)
    
    screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//3))
    screen.blit(resume_text, (WIDTH//2 - resume_text.get_width()//2, HEIGHT//2 - 50))
    screen.blit(shop_text, (WIDTH//2 - shop_text.get_width()//2, HEIGHT//2))
    screen.blit(credits_text, (WIDTH//2 - credits_text.get_width()//2, HEIGHT//2 + 50))
    screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 100))
    screen.blit(player_credits_text, (WIDTH//2 - player_credits_text.get_width()//2, HEIGHT//2 + 150))

def reset_game():
    global player_x, player_y, player_health, player_score, bullets, asteroids, enemies, loots, difficulty, auto_fire
    player_x = WIDTH // 2 - player_size // 2
    player_y = HEIGHT - 2 * player_size
    player_health = player_max_health
    player_score = 0
    difficulty = 1.0
    auto_fire = False  # Reset auto-fire to off when starting a new game
    bullets = []
    asteroids = []
    enemies = []
    loots = []
def main():
    # Declare global variables
    global game_state, player_x, player_y, player_health, player_credits, player_score, player_name
    global shake_intensity, shake_offset, shake_decay, previous_state, auto_fire, screen, WIDTH, HEIGHT
    
    running = True
    previous_state = WELCOME  # To remember state before pausing
    
    # Show initial pause hint
    show_initial_pause_hint = True
    pause_hint_timer = 0
    
    while running:
        # Apply screen shake if active
        if shake_intensity > 0.5:
            shake_offset[0] = random.uniform(-shake_intensity, shake_intensity)
            shake_offset[1] = random.uniform(-shake_intensity, shake_intensity)
            shake_intensity *= shake_decay
        else:
            shake_offset[0] = 0
            shake_offset[1] = 0
            shake_intensity = 0
            
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle window resize events
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.size
                screen = pygame.display.set_mode((WIDTH, HEIGHT))
                reset_player_position()
            
            if event.type == pygame.KEYDOWN:
                if game_state == NAME_ENTRY:
                    handle_name_entry(event)
                elif game_state == WELCOME:
                    if event.key == pygame.K_RETURN:
                        reset_game()
                        game_state = PLAYING
                        # Show pause hint when starting a new game
                        show_initial_pause_hint = True
                        pause_hint_timer = pygame.time.get_ticks()
                    elif event.key == pygame.K_r:
                        game_state = RULES
                    elif event.key == pygame.K_s:
                        previous_state = WELCOME
                        game_state = SHOP
                    elif event.key == pygame.K_n:
                        game_state = NAME_ENTRY
                    elif event.key == pygame.K_c:
                        previous_state = WELCOME
                        game_state = CREDITS
                elif game_state == GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        reset_game()
                        game_state = PLAYING
                        # Show pause hint when starting a new game
                        show_initial_pause_hint = True
                        pause_hint_timer = pygame.time.get_ticks()
                    elif event.key == pygame.K_ESCAPE:
                        game_state = WELCOME
                elif game_state == RULES and event.key == pygame.K_ESCAPE:
                    game_state = WELCOME
                elif game_state == CREDITS and event.key == pygame.K_ESCAPE:
                    game_state = previous_state
                elif game_state == PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        game_state = WELCOME
                    elif event.key == pygame.K_p:
                        previous_state = PLAYING  # Store current state
                        game_state = PAUSED
                    elif event.key == pygame.K_f:
                        # Toggle auto-fire mode
                        auto_fire = not auto_fire
                    elif event.key == pygame.K_c:
                        previous_state = PLAYING  # Store current state
                        game_state = CREDITS
                elif game_state == PAUSED:
                    if event.key == pygame.K_p:
                        game_state = PLAYING  # Force to PLAYING state
                    elif event.key == pygame.K_s:
                        previous_state = PAUSED
                        game_state = SHOP
                    elif event.key == pygame.K_c:
                        previous_state = PAUSED
                        game_state = CREDITS
                    elif event.key == pygame.K_ESCAPE:
                        game_state = WELCOME
                elif game_state == SHOP and event.key == pygame.K_ESCAPE:
                    if previous_state == PAUSED:
                        game_state = PAUSED
                    else:
                        game_state = WELCOME
        # Clear screen
        screen.fill(BLACK)
        
        # Handle different game states
        if game_state == WELCOME:
            draw_welcome_screen()
        elif game_state == PLAYING:
            update_game()
            draw_game()
            
            # Show initial pause hint overlay for the first few seconds of gameplay
            if show_initial_pause_hint and pygame.time.get_ticks() - pause_hint_timer < 3000:  # Show for 3 seconds
                # Semi-transparent overlay
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 100))  # Black with alpha
                screen.blit(overlay, (0, 0))
                
                # Draw pause hint
                font_large = pygame.font.Font(None, 48)
                font_medium = pygame.font.Font(None, 36)
                
                hint_title = font_large.render("GAME TIP", True, YELLOW)
                hint_text = font_medium.render("Press P to pause the game", True, WHITE)
                hint_text2 = font_medium.render("Press F to toggle auto-fire mode", True, GREEN)
                hint_text3 = font_medium.render("Press C to view credits during gameplay", True, YELLOW)
                
                screen.blit(hint_title, (WIDTH//2 - hint_title.get_width()//2, HEIGHT//3 - 50))
                screen.blit(hint_text, (WIDTH//2 - hint_text.get_width()//2, HEIGHT//2 - 50))
                screen.blit(hint_text2, (WIDTH//2 - hint_text2.get_width()//2, HEIGHT//2))
                screen.blit(hint_text3, (WIDTH//2 - hint_text3.get_width()//2, HEIGHT//2 + 50))
            elif show_initial_pause_hint:
                show_initial_pause_hint = False
                
        elif game_state == GAME_OVER:
            draw_game_over_screen()
        elif game_state == RULES:
            draw_rules_screen()
        elif game_state == SHOP:
            handle_shop()
        elif game_state == NAME_ENTRY:
            draw_name_entry_screen()
        elif game_state == CREDITS:
            draw_credits_screen()
        elif game_state == PAUSED:
            # Draw the game in the background
            draw_game()
            # Draw pause menu on top
            draw_pause_menu()
        
        pygame.display.update()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

# Start the game
if __name__ == "__main__":
    main()
