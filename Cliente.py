import pygame
import sys
import socket
import json
import time

# ... (Mantém as seções de Inicialização, Configurações de Tela, Cores, Fontes, Configurações do Jogo, Objetos, Estado) ...
# (Vou omitir as seções que não mudam para economizar espaço, mas elas devem permanecer no seu código)
# --- Inicialização do Pygame ---
pygame.init()

# --- Configurações da Tela ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 120 
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong Cliente (Player 2)")
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
except pygame.error:
    print("Aviso: Fonte padrão não encontrada. Usando fonte do sistema.")
    font_medium = pygame.font.SysFont(None, 50)
    font_small = pygame.font.SysFont(None, 30)
    font_large = pygame.font.SysFont(None, 40)

# --- Configurações Visuais e de Jogo ---
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 100
BALL_RADIUS = 10
PLAYER_SPEED = 5.0 
WINNING_SCORE = 5

# --- Objetos do Jogo ---
player1_rect = pygame.Rect(SCREEN_WIDTH - PADDLE_WIDTH - 50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
player2_rect = pygame.Rect(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)

ball_pos = [SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2] 

# --- Estado do Jogo ---
score1 = 0
score2 = 0
game_started_from_server = False
game_over_from_server = False

# --- Configurações de Rede ---
SERVER_IP = '127.0.0.1'  
SERVER_PORT = 12345
client_socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected_to_server = False
receive_buffer_client = b"" # Buffer para dados recebidos do servidor

# --- Funções Auxiliares ---
def draw_text(text, font, color, surface, x, y, center=False):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def connect_to_server():
    global connected_to_server, client_socket_obj
    try:
        draw_text("Conectando ao servidor...", font_small, YELLOW, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
        pygame.display.flip()
        print(f"Tentando conectar ao servidor em {SERVER_IP}:{SERVER_PORT}...")
        client_socket_obj.connect((SERVER_IP, SERVER_PORT))
        client_socket_obj.settimeout(0.1) # Timeout para recv
        connected_to_server = True
        print("Conectado ao servidor!")
        return True
    except socket.error as e:
        print(f"Falha ao conectar ao servidor: {e}")
        return False

# --- Loop Principal do Cliente ---
if not connect_to_server():
    running = False
    screen.fill(BLACK)
    draw_text("FALHA AO CONECTAR AO SERVIDOR.", font_small, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
    draw_text("Verifique se o servidor está em execução.", font_small, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, center=True)
    pygame.display.flip()
    time.sleep(3)
else:
    running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_player2_y = player2_rect.y 
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and player2_rect.top > 0:
        current_player2_y -= PLAYER_SPEED
    if keys[pygame.K_s] and player2_rect.bottom < SCREEN_HEIGHT:
        current_player2_y += PLAYER_SPEED
    current_player2_y = max(0, min(current_player2_y, SCREEN_HEIGHT - PADDLE_HEIGHT))
    # A posição visual de player2_rect.y será atualizada pelo servidor.
    # Guardamos current_player2_y para enviar.

    if connected_to_server:
        client_input_data = {"player2_y": current_player2_y}
        try:
            message_to_send = json.dumps(client_input_data) + '\n' 
            client_socket_obj.sendall(message_to_send.encode('utf-8'))
        except socket.error as e:
            print(f"Erro ao enviar dados para o servidor: {e}")
            running = False 
            break

        try:
            data_chunk = client_socket_obj.recv(2048)
            if not data_chunk:
                print("Servidor desconectou (recv retornou vazio/EOF).")
                running = False
                break
            receive_buffer_client += data_chunk

            while b'\n' in receive_buffer_client:
                message_bytes, receive_buffer_client = receive_buffer_client.split(b'\n', 1)
                server_data_str = message_bytes.decode('utf-8').strip()

                if not server_data_str:
                    continue
                
                # print(f"CLIENTE DEBUG: Processing message from server: '{server_data_str}'")
                server_state = json.loads(server_data_str)
                
                ball_pos[0] = server_state.get("ball_x", ball_pos[0])
                ball_pos[1] = server_state.get("ball_y", ball_pos[1])
                player1_rect.y = server_state.get("player1_y", player1_rect.y)
                player2_rect.y = server_state.get("player2_y", player2_rect.y) 
                score1 = server_state.get("score1", score1)
                score2 = server_state.get("score2", score2)
                game_started_from_server = server_state.get("game_started", game_started_from_server)
                game_over_from_server = server_state.get("game_over", game_over_from_server)

        except socket.timeout:
            pass 
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON do servidor: {e}. Dados problemáticos: '{server_data_str[:100]}'")
            # Limpar o buffer pode ser uma boa ideia aqui para evitar erros repetidos com os mesmos dados
            # receive_buffer_client = b"" # Ou apenas a parte que causou erro
            pass # Tenta continuar
        except (socket.error, UnicodeDecodeError) as e:
            print(f"Erro de socket/decodificação ao receber do servidor: {e}")
            running = False
            break
        except ConnectionResetError:
            print("Conexão com o servidor foi resetada.")
            running = False
            break

    # --- Desenho ---
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, player1_rect) 
    pygame.draw.rect(screen, WHITE, player2_rect) 
    pygame.draw.circle(screen, WHITE, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

    draw_text(str(score2), font_medium, WHITE, screen, SCREEN_WIDTH // 4, 20, center=True)
    draw_text(str(score1), font_medium, WHITE, screen, SCREEN_WIDTH * 3 // 4, 20, center=True)

    if not connected_to_server:
        pass 
    elif not game_started_from_server and not game_over_from_server:
        draw_text("AGUARDANDO PLAYER 1 (SERVIDOR) INICIAR", font_small, YELLOW, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, center=True)
    
    if game_over_from_server:
        winner_text = "FIM DE JOGO" 
        if score1 >= WINNING_SCORE: 
            winner_text = "PLAYER 1 VENCEU!"
        elif score2 >= WINNING_SCORE: 
            winner_text = "PLAYER 2 VENCEU!"
        
        draw_text(winner_text, font_large, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, center=True)
        draw_text("AGUARDANDO REINÍCIO PELO SERVIDOR", font_small, LIGHTGRAY, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)

    pygame.display.flip()
    clock.tick(FPS)

# --- Fim do Jogo ---
print("Encerrando cliente...")
if connected_to_server and client_socket_obj:
    try:
        client_socket_obj.shutdown(socket.SHUT_RDWR) 
    except socket.error:
        pass 
    client_socket_obj.close()
pygame.quit()
sys.exit()