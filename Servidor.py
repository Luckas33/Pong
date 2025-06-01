import pygame
import sys
import math
import socket
import threading
import json

# ... (Mantém as seções de Inicialização, Configurações de Tela, Cores, Fontes, Configurações do Jogo, Objetos, Estado) ...
# (Vou omitir as seções que não mudam para economizar espaço, mas elas devem permanecer no seu código)
# --- Inicialização do Pygame ---
pygame.init()

# --- Configurações da Tela ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 120 
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong Servidor (Player 1)")
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

# --- Configurações do Jogo ---
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 100
BALL_RADIUS = 10
PLAYER_SPEED = 5.0
BALL_INITIAL_SPEED_X = -6.0 
BALL_SPEED_Y_FACTOR = 5.0 
WINNING_SCORE = 5

# --- Objetos do Jogo ---
player1_rect = pygame.Rect(SCREEN_WIDTH - PADDLE_WIDTH - 50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
player2_rect = pygame.Rect(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)

ball_pos = [0.0, 0.0] 
ball_vel = [BALL_INITIAL_SPEED_X, 0.0]

# --- Estado do Jogo ---
score1 = 0 
score2 = 0 
game_started = False
game_over = False
waiting_for_client = True

# --- Configurações de Rede ---
SERVER_HOST = '0.0.0.0' 
SERVER_PORT = 12345
g_client_socket_conn = None 
g_client_address = None

player2_y_from_client = float(player2_rect.y) 
player2_data_lock = threading.Lock()

# --- Funções Auxiliares do Jogo ---
def reset_ball():
    global game_started, ball_pos, ball_vel
    game_started = False
    ball_pos[0] = player1_rect.left - BALL_RADIUS - 5 
    ball_pos[1] = player1_rect.centery
    ball_vel[0] = BALL_INITIAL_SPEED_X 
    ball_vel[1] = 0.0

def reset_game_full():
    global score1, score2, game_over, player1_rect, player2_rect
    score1 = 0
    score2 = 0
    game_over = False
    player1_rect.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
    with player2_data_lock: 
        player2_y_from_client = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
        player2_rect.y = player2_y_from_client
    reset_ball()

def draw_text(text, font, color, surface, x, y, center=False):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

reset_game_full()

# --- Lógica de Rede (Thread do Cliente) ---
def handle_client_communication(conn, addr):
    global player2_y_from_client, g_client_socket_conn, g_client_address, waiting_for_client
    print(f"Cliente {addr} conectado.")
    g_client_socket_conn = conn 
    g_client_address = addr
    waiting_for_client = False 

    conn.settimeout(0.1) # Timeout para conn.recv()
    receive_buffer = b""

    try:
        while True:
            try:
                data_chunk = conn.recv(1024)
                if not data_chunk:
                    print(f"Cliente {addr} desconectou (recv retornou vazio/EOF).")
                    break
                receive_buffer += data_chunk

                # Processar todas as mensagens completas no buffer
                while b'\n' in receive_buffer:
                    message_bytes, receive_buffer = receive_buffer.split(b'\n', 1)
                    client_data_str = message_bytes.decode('utf-8').strip()
                    
                    if not client_data_str:
                        continue
                    
                    # print(f"SERVER DEBUG: Processing message from client: '{client_data_str}'")
                    client_data = json.loads(client_data_str)
                    received_y = client_data.get('player2_y')

                    if isinstance(received_y, (int, float)):
                        with player2_data_lock:
                            player2_y_from_client = float(received_y)
                    
            except socket.timeout:
                # Normal se nenhum dado chegar dentro do timeout, o loop continua
                pass
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON do cliente {addr}: {e}. Dados problemáticos: '{client_data_str[:100]}'")
                # Limpar buffer ou parte dele pode ser necessário se o JSON estiver corrompido
                # Para simplificar, podemos quebrar se a decodificação falhar consistentemente.
                # No entanto, se o split acima estiver correto, isso deve ser raro.
                # Se uma mensagem parcial foi decodificada, receive_buffer pode conter o resto.
                # Vamos tentar continuar, mas se isso causar loops de erro, quebrar é mais seguro.
                # Se o split falhou em achar \n e o buffer cresce demais, pode ser um problema.
                # Por ora, vamos assumir que o split funciona ou o erro de JSON é fatal para a msg.
                # Se client_data_str ainda estiver definido e causou o erro, o buffer já foi splitado.
                # Se o erro foi em message_bytes.decode, então o split já ocorreu.
                pass # Tenta continuar, mas pode ser melhor quebrar se os erros persistirem
            except (socket.error, UnicodeDecodeError) as e: # socket.error é OSError
                print(f"Erro de socket/decodificação ao receber do cliente {addr}: {e}")
                break 
            except ConnectionResetError:
                print(f"Cliente {addr} resetou a conexão.")
                break
            
            pygame.time.wait(1) 

    except Exception as e:
        print(f"Erro inesperado na thread do cliente {addr}: {e}")
    finally:
        print(f"Fechando conexão com o cliente {addr}.")
        conn.close()
        g_client_socket_conn = None 
        g_client_address = None
        waiting_for_client = True 

# ... (Mantém a seção de Configuração do Socket do Servidor) ...
server_socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_socket_obj.settimeout(1.0) # Timeout para accept
server_socket_obj.setblocking(False) # Mudar para não bloqueante para o loop principal não travar no accept
try:
    server_socket_obj.bind((SERVER_HOST, SERVER_PORT))
    server_socket_obj.listen(1)
    print(f"Servidor escutando em {SERVER_HOST}:{SERVER_PORT}")
except socket.error as e:
    print(f"Erro ao iniciar o servidor: {e}")
    pygame.quit()
    sys.exit()

client_handler_thread = None


# --- Loop Principal do Servidor ---
# ... (O loop principal permanece o mesmo, mas a forma como aceita e envia dados será ajustada)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if not game_started and not game_over and g_client_socket_conn and event.key == pygame.K_SPACE: # Precisa de cliente conectado
                game_started = True
            if game_over and event.key == pygame.K_RETURN:
                reset_game_full()

    # --- Aceitar conexão do cliente (não bloqueante) ---
    if waiting_for_client:
        try:
            conn_temp, addr_temp = server_socket_obj.accept() # Tenta aceitar
            # conn_temp.settimeout(0.1) # Definido na thread agora
            
            if client_handler_thread and client_handler_thread.is_alive():
                if g_client_socket_conn: 
                    try: g_client_socket_conn.shutdown(socket.SHUT_RDWR)
                    except socket.error: pass
                    g_client_socket_conn.close()
                client_handler_thread.join(timeout=0.1)

            client_handler_thread = threading.Thread(target=handle_client_communication, args=(conn_temp, addr_temp))
            client_handler_thread.daemon = True 
            client_handler_thread.start()
            # waiting_for_client é setado para False dentro da thread handle_client_communication
        except BlockingIOError: # Esperado se o socket do servidor for não bloqueante e não houver conexões
            pass 
        except socket.error as e: # Outros erros de socket no accept
            print(f"Erro ao aceitar conexão: {e}")
            pass


    with player2_data_lock:
        target_p2_y = player2_y_from_client
    player2_rect.y = target_p2_y
    player2_rect.y = max(0, min(player2_rect.y, SCREEN_HEIGHT - PADDLE_HEIGHT))


    if not game_over and g_client_socket_conn: # Só atualiza e move a bola se o cliente estiver conectado
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and player1_rect.top > 0:
            player1_rect.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN] and player1_rect.bottom < SCREEN_HEIGHT:
            player1_rect.y += PLAYER_SPEED
        
        if not game_started:
            ball_pos[0] = player1_rect.left - BALL_RADIUS - 5 
            ball_pos[1] = player1_rect.centery
        else:
            ball_pos[0] += ball_vel[0]
            ball_pos[1] += ball_vel[1]

            ball_visual_rect = pygame.Rect(ball_pos[0] - BALL_RADIUS, ball_pos[1] - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)

            if ball_pos[1] - BALL_RADIUS <= 0 or ball_pos[1] + BALL_RADIUS >= SCREEN_HEIGHT:
                ball_vel[1] *= -1
            
            if ball_visual_rect.colliderect(player1_rect) and ball_vel[0] > 0:
                hit_pos_rel = (ball_pos[1] - player1_rect.centery) / (PADDLE_HEIGHT / 2)
                ball_vel[0] *= -1
                ball_vel[1] = max(-1, min(1, hit_pos_rel)) * BALL_SPEED_Y_FACTOR
            
            if ball_visual_rect.colliderect(player2_rect) and ball_vel[0] < 0:
                hit_pos_rel = (ball_pos[1] - player2_rect.centery) / (PADDLE_HEIGHT / 2)
                ball_vel[0] *= -1
                ball_vel[1] = max(-1, min(1, hit_pos_rel)) * BALL_SPEED_Y_FACTOR

            if ball_pos[0] + BALL_RADIUS < 0: 
                score1 += 1
                reset_ball()
            elif ball_pos[0] - BALL_RADIUS > SCREEN_WIDTH:
                score2 += 1
                reset_ball()
            
            if score1 >= WINNING_SCORE or score2 >= WINNING_SCORE:
                game_over = True
                game_started = False

    # Enviar estado apenas se o cliente estiver conectado
    if g_client_socket_conn: # Não precisa mais de 'and not waiting_for_client' aqui se g_client_socket_conn é o indicador
        game_state = {
            "ball_x": ball_pos[0], "ball_y": ball_pos[1],
            "player1_y": player1_rect.y, "player2_y": player2_rect.y,
            "score1": score1, "score2": score2,
            "game_started": game_started, "game_over": game_over
        }
        try:
            message_to_send = json.dumps(game_state) + '\n' 
            g_client_socket_conn.sendall(message_to_send.encode('utf-8'))
        except socket.error as e:
            if e.errno not in [socket.errno.ECONNRESET, socket.errno.EPIPE, socket.errno.ECONNABORTED, socket.errno.ESHUTDOWN, socket.errno.ENOTCONN, socket.errno.EBADF]: # 10057 (ENOTCONN), 10009 (EBADF)
                 print(f"Erro ao enviar estado para o cliente (loop principal): {e} (errno: {e.errno})")
            # A thread do cliente deve lidar com o fechamento e setar g_client_socket_conn para None
    
    # --- Desenho ---
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, player1_rect)
    pygame.draw.rect(screen, WHITE, player2_rect)
    pygame.draw.circle(screen, WHITE, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

    draw_text(str(score2), font_medium, WHITE, screen, SCREEN_WIDTH // 4, 20, center=True)
    draw_text(str(score1), font_medium, WHITE, screen, SCREEN_WIDTH * 3 // 4, 20, center=True)

    if waiting_for_client and not g_client_socket_conn : # Mostra se nenhum cliente jamais se conectou ou se o anterior desconectou e estamos esperando um novo
        draw_text("AGUARDANDO CLIENTE (PLAYER 2)...", font_small, YELLOW, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
    elif not game_started and not game_over:
        draw_text("PRESSIONE ESPAÇO PARA LANÇAR (PLAYER 1)", font_small, YELLOW, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, center=True)
    
    if game_over:
        winner_text = "PLAYER 1 VENCEU!" if score1 >= WINNING_SCORE else "PLAYER 2 VENCEU!"
        draw_text(winner_text, font_large, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, center=True)
        draw_text("PRESSIONE ENTER PARA REINICIAR", font_small, LIGHTGRAY, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)

    pygame.display.flip()
    clock.tick(FPS)

# --- Fim do Jogo ---
print("Encerrando servidor...")
if g_client_socket_conn: 
    try: g_client_socket_conn.shutdown(socket.SHUT_RDWR)
    except socket.error: pass
    g_client_socket_conn.close()
if client_handler_thread and client_handler_thread.is_alive():
    client_handler_thread.join(timeout=0.5) 
server_socket_obj.close()
pygame.quit()
sys.exit()