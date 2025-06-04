import pygame
import sys
import math
import socket
import threading
import json

pygame.init()

LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 120 
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Pong Servidor (Jogador 1)")
relogio = pygame.time.Clock()

PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AMARELO = (253, 249, 0)
VERMELHO = (230, 41, 55)
CINZA_CLARO = (200, 200, 200)

try:
    caminho_fonte = pygame.font.get_default_font()
    fonte_media = pygame.font.Font(caminho_fonte, 40)
    fonte_pequena = pygame.font.Font(caminho_fonte, 20)
    fonte_grande = pygame.font.Font(caminho_fonte, 30)
except pygame.error:
    fonte_media = pygame.font.SysFont(None, 50)
    fonte_pequena = pygame.font.SysFont(None, 30)
    fonte_grande = pygame.font.SysFont(None, 40)

LARGURA_RAQUETE = 20
ALTURA_RAQUETE = 100
RAIO_BOLA = 10
VEL_JOGADOR = 5.0
VEL_BOLA_X = -6.0 
FATOR_VEL_BOLA_Y = 5.0 
PONTOS_VITORIA = 5

jogador1 = pygame.Rect(LARGURA_TELA - LARGURA_RAQUETE - 50, ALTURA_TELA // 2 - ALTURA_RAQUETE // 2, LARGURA_RAQUETE, ALTURA_RAQUETE)
jogador2 = pygame.Rect(50, ALTURA_TELA // 2 - ALTURA_RAQUETE // 2, LARGURA_RAQUETE, ALTURA_RAQUETE)

pos_bola = [0.0, 0.0] 
vel_bola = [VEL_BOLA_X, 0.0]

pontos1 = 0 
pontos2 = 0 
jogo_iniciado = False
jogo_finalizado = False
aguardando_cliente = True

IP_SERVIDOR = '0.0.0.0'
PORTA_SERVIDOR = 12345
cliente_conexao = None
cliente_endereco = None

pos_y_jogador2 = float(jogador2.y)
trava_jogador2 = threading.Lock()

def reiniciar_bola():
    global jogo_iniciado, pos_bola, vel_bola
    jogo_iniciado = False
    pos_bola[0] = jogador1.left - RAIO_BOLA - 5
    pos_bola[1] = jogador1.centery
    vel_bola[0] = VEL_BOLA_X
    vel_bola[1] = 0.0

def reiniciar_jogo():
    global pontos1, pontos2, jogo_finalizado, jogador1, jogador2
    pontos1 = 0
    pontos2 = 0
    jogo_finalizado = False
    jogador1.y = ALTURA_TELA // 2 - ALTURA_RAQUETE // 2
    with trava_jogador2:
        pos_y_jogador2 = ALTURA_TELA // 2 - ALTURA_RAQUETE // 2
        jogador2.y = pos_y_jogador2
    reiniciar_bola()

def desenhar_texto(texto, fonte, cor, superficie, x, y, centralizar=False):
    obj_texto = fonte.render(texto, True, cor)
    ret_texto = obj_texto.get_rect()
    if centralizar:
        ret_texto.center = (x, y)
    else:
        ret_texto.topleft = (x, y)
    superficie.blit(obj_texto, ret_texto)

reiniciar_jogo()

def lidar_com_cliente(conexao, endereco):
    global pos_y_jogador2, cliente_conexao, cliente_endereco, aguardando_cliente
    print(f"Cliente {endereco} conectado.")
    cliente_conexao = conexao
    cliente_endereco = endereco
    aguardando_cliente = False
    conexao.settimeout(0.1)
    buffer_recebido = b""

    try:
        while True:
            try:
                dados = conexao.recv(1024)
                if not dados:
                    break
                buffer_recebido += dados
                while b'\n' in buffer_recebido:
                    msg, buffer_recebido = buffer_recebido.split(b'\n', 1)
                    dados_cliente = json.loads(msg.decode('utf-8').strip())
                    y_recebido = dados_cliente.get('player2_y')
                    if isinstance(y_recebido, (int, float)):
                        with trava_jogador2:
                            pos_y_jogador2 = float(y_recebido)
            except socket.timeout:
                pass
            except json.JSONDecodeError:
                pass
            except (socket.error, UnicodeDecodeError):
                break
            except ConnectionResetError:
                break
            pygame.time.wait(1)
    finally:
        print(f"Desconectando cliente {endereco}.")
        conexao.close()
        cliente_conexao = None
        cliente_endereco = None
        aguardando_cliente = True

servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor_socket.setblocking(False)
try:
    servidor_socket.bind((IP_SERVIDOR, PORTA_SERVIDOR))
    servidor_socket.listen(1)
    print(f"Servidor ouvindo em {IP_SERVIDOR}:{PORTA_SERVIDOR}")
except socket.error as e:
    pygame.quit()
    sys.exit()

thread_cliente = None
rodando = True

while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.KEYDOWN:
            if not jogo_iniciado and not jogo_finalizado and cliente_conexao and evento.key == pygame.K_SPACE:
                jogo_iniciado = True
            if jogo_finalizado and evento.key == pygame.K_RETURN:
                reiniciar_jogo()

    if aguardando_cliente:
        try:
            conexao_temp, endereco_temp = servidor_socket.accept()
            if thread_cliente and thread_cliente.is_alive():
                if cliente_conexao:
                    try: cliente_conexao.shutdown(socket.SHUT_RDWR)
                    except socket.error: pass
                    cliente_conexao.close()
                thread_cliente.join(timeout=0.1)

            thread_cliente = threading.Thread(target=lidar_com_cliente, args=(conexao_temp, endereco_temp))
            thread_cliente.daemon = True
            thread_cliente.start()
        except BlockingIOError:
            pass
        except socket.error:
            pass

    with trava_jogador2:
        alvo_y = pos_y_jogador2
    jogador2.y = max(0, min(alvo_y, ALTURA_TELA - ALTURA_RAQUETE))

    if not jogo_finalizado and cliente_conexao:
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_UP] and jogador1.top > 0:
            jogador1.y -= VEL_JOGADOR
        if teclas[pygame.K_DOWN] and jogador1.bottom < ALTURA_TELA:
            jogador1.y += VEL_JOGADOR

        if not jogo_iniciado:
            pos_bola[0] = jogador1.left - RAIO_BOLA - 5
            pos_bola[1] = jogador1.centery
        else:
            pos_bola[0] += vel_bola[0]
            pos_bola[1] += vel_bola[1]

            bola_ret = pygame.Rect(pos_bola[0] - RAIO_BOLA, pos_bola[1] - RAIO_BOLA, RAIO_BOLA * 2, RAIO_BOLA * 2)

            if pos_bola[1] - RAIO_BOLA <= 0 or pos_bola[1] + RAIO_BOLA >= ALTURA_TELA:
                vel_bola[1] *= -1

            if bola_ret.colliderect(jogador1) and vel_bola[0] > 0:
                rel_pos = (pos_bola[1] - jogador1.centery) / (ALTURA_RAQUETE / 2)
                vel_bola[0] *= -1
                vel_bola[1] = max(-1, min(1, rel_pos)) * FATOR_VEL_BOLA_Y

            if bola_ret.colliderect(jogador2) and vel_bola[0] < 0:
                rel_pos = (pos_bola[1] - jogador2.centery) / (ALTURA_RAQUETE / 2)
                vel_bola[0] *= -1
                vel_bola[1] = max(-1, min(1, rel_pos)) * FATOR_VEL_BOLA_Y

            if pos_bola[0] + RAIO_BOLA < 0:
                pontos1 += 1
                reiniciar_bola()
            elif pos_bola[0] - RAIO_BOLA > LARGURA_TELA:
                pontos2 += 1
                reiniciar_bola()

            if pontos1 >= PONTOS_VITORIA or pontos2 >= PONTOS_VITORIA:
                jogo_finalizado = True
                jogo_iniciado = False

    if cliente_conexao:
        estado = {
            "ball_x": pos_bola[0], "ball_y": pos_bola[1],
            "player1_y": jogador1.y, "player2_y": jogador2.y,
            "score1": pontos1, "score2": pontos2,
            "game_started": jogo_iniciado, "game_over": jogo_finalizado
        }
        try:
            msg = json.dumps(estado) + '\n'
            cliente_conexao.sendall(msg.encode('utf-8'))
        except socket.error as e:
            pass

    tela.fill(PRETO)
    pygame.draw.rect(tela, BRANCO, jogador1)
    pygame.draw.rect(tela, BRANCO, jogador2)
    pygame.draw.circle(tela, BRANCO, (int(pos_bola[0]), int(pos_bola[1])), RAIO_BOLA)

    desenhar_texto(str(pontos2), fonte_media, BRANCO, tela, LARGURA_TELA // 4, 20, centralizar=True)
    desenhar_texto(str(pontos1), fonte_media, BRANCO, tela, LARGURA_TELA * 3 // 4, 20, centralizar=True)

    if aguardando_cliente and not cliente_conexao:
        desenhar_texto("AGUARDANDO CLIENTE (JOGADOR 2)...", fonte_pequena, AMARELO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2, centralizar=True)
    elif not jogo_iniciado and not jogo_finalizado:
        desenhar_texto("PRESSIONE ESPAÇO PARA LANÇAR (JOGADOR 1)", fonte_pequena, AMARELO, tela, LARGURA_TELA // 2, ALTURA_TELA - 50, centralizar=True)

    if jogo_finalizado:
        vencedor = "JOGADOR 1 VENCEU!" if pontos1 >= PONTOS_VITORIA else "JOGADOR 2 VENCEU!"
        desenhar_texto(vencedor, fonte_grande, VERMELHO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2 - 50, centralizar=True)
        desenhar_texto("PRESSIONE ENTER PARA REINICIAR", fonte_pequena, CINZA_CLARO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2 + 20, centralizar=True)

    pygame.display.flip()
    relogio.tick(FPS)

print("Encerrando servidor...")
if cliente_conexao:
    try: cliente_conexao.shutdown(socket.SHUT_RDWR)
    except socket.error: pass
    cliente_conexao.close()
if thread_cliente and thread_cliente.is_alive():
    thread_cliente.join(timeout=0.5)
servidor_socket.close()
pygame.quit()
sys.exit()
