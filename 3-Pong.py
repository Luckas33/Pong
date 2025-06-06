import pygame
import sys
import math # Para a lógica de ricochete da bola

# Inicializa Pygame
pygame.init()

# --- Configurações da Tela ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 120  # O Pong.c original usava 120 FPS, podemos ajustar se necessário
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong em Pygame")
clock = pygame.time.Clock()

# --- Cores ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (253, 249, 0)
RED = (230, 41, 55)
LIGHTGRAY = (200, 200, 200)

# --- Fontes ---
try:
    FONT_DEFAULT_PATH = pygame.font.get_default_font()
    font_medium = pygame.font.Font(FONT_DEFAULT_PATH, 40)
    font_small = pygame.font.Font(FONT_DEFAULT_PATH, 20)
    font_large = pygame.font.Font(FONT_DEFAULT_PATH, 30)
except pygame.error: # Fallback se a fonte padrão não puder ser carregada
    print("Aviso: Fonte padrão não encontrada. Usando fonte do sistema (pode variar).")
    font_medium = pygame.font.SysFont(None, 50) # Tamanho ajustado para SysFont
    font_small = pygame.font.SysFont(None, 30)
    font_large = pygame.font.SysFont(None, 40)


# --- Configurações do Jogo ---
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 100
BALL_RADIUS = 10
PLAYER_SPEED = 5.0
BALL_INITIAL_SPEED_X = -6.0 # Negativo para ir para a esquerda
BALL_SPEED_Y_FACTOR = 5.0 # Fator para o ricochete vertical
WINNING_SCORE = 5

# --- Objetos do Jogo ---
# Player 1 (Direita)
player1_rect = pygame.Rect(SCREEN_WIDTH - PADDLE_WIDTH - 50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
# Player 2 (Esquerda)
player2_rect = pygame.Rect(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)

ball_pos = [0.0, 0.0] # [x, y] - será definido em reset_ball
ball_vel = [BALL_INITIAL_SPEED_X, 0.0] # [vx, vy]

# --- Estado do Jogo ---
score1 = 0 # Player 1 (Direita)
score2 = 0 # Player 2 (Esquerda)
game_started = False
game_over = False

# --- Funções Auxiliares ---
def reset_ball(player1_paddle_y):
    """Reseta a posição e velocidade da bola, geralmente após um ponto."""
    global game_started, ball_pos, ball_vel
    game_started = False
    ball_pos[0] = player1_rect.left - BALL_RADIUS - 5 # Um pouco à esquerda do paddle direito
    ball_pos[1] = player1_paddle_y + PADDLE_HEIGHT / 2
    ball_vel[0] = BALL_INITIAL_SPEED_X
    ball_vel[1] = 0.0

def reset_game_full():
    """Reseta o jogo completamente, incluindo scores."""
    global score1, score2, game_over, player1_rect, player2_rect
    score1 = 0
    score2 = 0
    game_over = False
    player1_rect.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
    player2_rect.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
    reset_ball(player1_rect.y)

def draw_text(text, font, color, surface, x, y, center=False):
    """Desenha texto na tela."""
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

# Inicializa a bola na primeira vez
reset_ball(player1_rect.y)

# --- Loop Principal do Jogo ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if not game_started and not game_over and event.key == pygame.K_SPACE:
                game_started = True
            if game_over and event.key == pygame.K_RETURN:
                reset_game_full()

    if not game_over:
        # --- Movimento dos Players ---
        keys = pygame.key.get_pressed()
        # Player 1 (Direita) - Teclas Cima/Baixo
        if keys[pygame.K_UP] and player1_rect.top > 0:
            player1_rect.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN] and player1_rect.bottom < SCREEN_HEIGHT:
            player1_rect.y += PLAYER_SPEED
        
        # Player 2 (Esquerda) - Teclas W/S
        if keys[pygame.K_w] and player2_rect.top > 0:
            player2_rect.y -= PLAYER_SPEED
        if keys[pygame.K_s] and player2_rect.bottom < SCREEN_HEIGHT:
            player2_rect.y += PLAYER_SPEED

        # --- Lógica do Jogo ---
        if not game_started:
            # Bola segue o paddle do Player 1 (Direita) antes do lançamento
            ball_pos[0] = player1_rect.left - BALL_RADIUS - 5 
            ball_pos[1] = player1_rect.centery
        else:
            # Movimento da Bola
            ball_pos[0] += ball_vel[0]
            ball_pos[1] += ball_vel[1]

            ball_rect = pygame.Rect(ball_pos[0] - BALL_RADIUS, ball_pos[1] - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)

            # Colisão da Bola com as Bordas Superior/Inferior
            if ball_pos[1] - BALL_RADIUS <= 0 or ball_pos[1] + BALL_RADIUS >= SCREEN_HEIGHT:
                ball_vel[1] *= -1

            # Colisão da Bola com os Paddles
            # Player 1 (Direita)
            if ball_rect.colliderect(player1_rect) and ball_vel[0] > 0: # Bola indo para a direita
                hit_pos_rel = (ball_pos[1] - player1_rect.centery) / (PADDLE_HEIGHT / 2)
                ball_vel[0] *= -1
                ball_vel[1] = hit_pos_rel * BALL_SPEED_Y_FACTOR
            
            # Player 2 (Esquerda)
            if ball_rect.colliderect(player2_rect) and ball_vel[0] < 0: # Bola indo para a esquerda
                hit_pos_rel = (ball_pos[1] - player2_rect.centery) / (PADDLE_HEIGHT / 2)
                ball_vel[0] *= -1
                ball_vel[1] = hit_pos_rel * BALL_SPEED_Y_FACTOR
            
            # Pontuação e Reset da Bola
            if ball_pos[0] + BALL_RADIUS < 0: # Bola passou pela esquerda (Ponto para Player 1 - Direita)
                score1 += 1
                reset_ball(player1_rect.y)
            elif ball_pos[0] - BALL_RADIUS > SCREEN_WIDTH: # Bola passou pela direita (Ponto para Player 2 - Esquerda)
                score2 += 1
                reset_ball(player1_rect.y)
            
            # Verificar Game Over
            if score1 >= WINNING_SCORE or score2 >= WINNING_SCORE:
                game_over = True
                game_started = False # Para não continuar movendo a bola


    # --- Desenho ---
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, player1_rect)
    pygame.draw.rect(screen, WHITE, player2_rect)
    pygame.draw.circle(screen, WHITE, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

    # Linha divisória (opcional, para estética)
    # pygame.draw.line(screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 2)

    # Placar
    draw_text(str(score2), font_medium, WHITE, screen, SCREEN_WIDTH // 4, 20, center=True) # Player 2 (Esquerda)
    draw_text(str(score1), font_medium, WHITE, screen, SCREEN_WIDTH * 3 // 4, 20, center=True) # Player 1 (Direita)

    if not game_started and not game_over:
        draw_text("PRESSIONE ESPAÇO PARA LANÇAR", font_small, YELLOW, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, center=True)
    
    if game_over:
        winner_text = ""
        if score1 >= WINNING_SCORE:
            winner_text = "PLAYER 1 VENCEU!"
        else:
            winner_text = "PLAYER 2 VENCEU!"
        draw_text(winner_text, font_large, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, center=True)
        draw_text("PRESSIONE ENTER PARA REINICIAR", font_small, LIGHTGRAY, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)

    pygame.display.flip()
    clock.tick(FPS)

# --- Fim do Jogo ---
pygame.quit()
sys.exit()