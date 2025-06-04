import pygame
import sys
import socket
import json
import time

pygame.init()

LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 120 
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Pong Cliente (Jogador 2)")
relogio = pygame.time.Clock()

PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AMARELO = (253, 249, 0)
VERMELHO = (230, 41, 55)
CINZA_CLARO = (200, 200, 200)

try:
    CAMINHO_FONTE_PADRAO = pygame.font.get_default_font()
    fonte_media = pygame.font.Font(CAMINHO_FONTE_PADRAO, 40)
    fonte_pequena = pygame.font.Font(CAMINHO_FONTE_PADRAO, 20)
    fonte_grande = pygame.font.Font(CAMINHO_FONTE_PADRAO, 30)
except pygame.error:
    print("Fonte padrão não encontrada.")
    fonte_media = pygame.font.SysFont(None, 50)
    fonte_pequena = pygame.font.SysFont(None, 30)
    fonte_grande = pygame.font.SysFont(None, 40)

LARGURA_RAQUETE = 20
ALTURA_RAQUETE = 100
RAIO_BOLA = 10
VELOCIDADE_JOGADOR = 5.0 
PONTOS_PARA_VENCER = 5

ret_jogador1 = pygame.Rect(LARGURA_TELA - LARGURA_RAQUETE - 50, ALTURA_TELA // 2 - ALTURA_RAQUETE // 2, LARGURA_RAQUETE, ALTURA_RAQUETE)
ret_jogador2 = pygame.Rect(50, ALTURA_TELA // 2 - ALTURA_RAQUETE // 2, LARGURA_RAQUETE, ALTURA_RAQUETE)
pos_bola = [LARGURA_TELA / 2, ALTURA_TELA / 2] 

pontos1 = 0
pontos2 = 0
jogo_iniciado = False
jogo_encerrado = False

IP_SERVIDOR = '127.0.0.1'  
PORTA_SERVIDOR = 12345
socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conectado = False
buffer_recebido = b""

def desenhar_texto(texto, fonte, cor, superficie, x, y, centralizado=False):
    obj_texto = fonte.render(texto, True, cor)
    ret_texto = obj_texto.get_rect()
    if centralizado:
        ret_texto.center = (x, y)
    else:
        ret_texto.topleft = (x, y)
    superficie.blit(obj_texto, ret_texto)

def conectar_ao_servidor():
    global conectado, socket_cliente
    try:
        desenhar_texto("Conectando ao servidor...", fonte_pequena, AMARELO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2, centralizado=True)
        pygame.display.flip()
        print(f"Tentando conectar ao servidor em {IP_SERVIDOR}:{PORTA_SERVIDOR}...")
        socket_cliente.connect((IP_SERVIDOR, PORTA_SERVIDOR))
        socket_cliente.settimeout(0.1)
        conectado = True
        print("Conectado ao servidor!")
        return True
    except socket.error as e:
        print(f"Erro ao conectar: {e}")
        return False

if not conectar_ao_servidor():
    em_execucao = False
    tela.fill(PRETO)
    desenhar_texto("FALHA AO CONECTAR AO SERVIDOR.", fonte_pequena, VERMELHO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2, centralizado=True)
    desenhar_texto("Verifique se o servidor está em execução.", fonte_pequena, VERMELHO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2 + 30, centralizado=True)
    pygame.display.flip()
    time.sleep(3)
else:
    em_execucao = True

while em_execucao:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            em_execucao = False

    pos_y_atual_jogador2 = ret_jogador2.y 
    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_w] and ret_jogador2.top > 0:
        pos_y_atual_jogador2 -= VELOCIDADE_JOGADOR
    if teclas[pygame.K_s] and ret_jogador2.bottom < ALTURA_TELA:
        pos_y_atual_jogador2 += VELOCIDADE_JOGADOR
    pos_y_atual_jogador2 = max(0, min(pos_y_atual_jogador2, ALTURA_TELA - ALTURA_RAQUETE))

    if conectado:
        dados_envio = {"player2_y": pos_y_atual_jogador2}
        try:
            mensagem = json.dumps(dados_envio) + '\n'
            socket_cliente.sendall(mensagem.encode('utf-8'))
        except socket.error as e:
            print(f"Erro ao enviar: {e}")
            em_execucao = False 
            break

        try:
            pacote = socket_cliente.recv(2048)
            if not pacote:
                print("Servidor desconectado.")
                em_execucao = False
                break
            buffer_recebido += pacote

            while b'\n' in buffer_recebido:
                dados_brutos, buffer_recebido = buffer_recebido.split(b'\n', 1)
                dados_str = dados_brutos.decode('utf-8').strip()

                if not dados_str:
                    continue
                
                estado = json.loads(dados_str)
                
                pos_bola[0] = estado.get("ball_x", pos_bola[0])
                pos_bola[1] = estado.get("ball_y", pos_bola[1])
                ret_jogador1.y = estado.get("player1_y", ret_jogador1.y)
                ret_jogador2.y = estado.get("player2_y", ret_jogador2.y) 
                pontos1 = estado.get("score1", pontos1)
                pontos2 = estado.get("score2", pontos2)
                jogo_iniciado = estado.get("game_started", jogo_iniciado)
                jogo_encerrado = estado.get("game_over", jogo_encerrado)

        except socket.timeout:
            pass 
        except json.JSONDecodeError as e:
            print(f"Erro JSON: {e}. Dados: '{dados_str[:100]}'")
            pass
        except (socket.error, UnicodeDecodeError) as e:
            print(f"Erro de conexão: {e}")
            em_execucao = False
            break
        except ConnectionResetError:
            print("Conexão resetada.")
            em_execucao = False
            break

    tela.fill(PRETO)
    pygame.draw.rect(tela, BRANCO, ret_jogador1) 
    pygame.draw.rect(tela, BRANCO, ret_jogador2) 
    pygame.draw.circle(tela, BRANCO, (int(pos_bola[0]), int(pos_bola[1])), RAIO_BOLA)

    desenhar_texto(str(pontos2), fonte_media, BRANCO, tela, LARGURA_TELA // 4, 20, centralizado=True)
    desenhar_texto(str(pontos1), fonte_media, BRANCO, tela, LARGURA_TELA * 3 // 4, 20, centralizado=True)

    if conectado and not jogo_iniciado and not jogo_encerrado:
        desenhar_texto("AGUARDANDO PLAYER 1 (SERVIDOR) INICIAR", fonte_pequena, AMARELO, tela, LARGURA_TELA // 2, ALTURA_TELA - 50, centralizado=True)
    
    if jogo_encerrado:
        texto_vitoria = "FIM DE JOGO" 
        if pontos1 >= PONTOS_PARA_VENCER: 
            texto_vitoria = "PLAYER 1 VENCEU!"
        elif pontos2 >= PONTOS_PARA_VENCER: 
            texto_vitoria = "PLAYER 2 VENCEU!"
        
        desenhar_texto(texto_vitoria, fonte_grande, VERMELHO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2 - 50, centralizado=True)
        desenhar_texto("AGUARDANDO REINÍCIO PELO SERVIDOR", fonte_pequena, CINZA_CLARO, tela, LARGURA_TELA // 2, ALTURA_TELA // 2 + 20, centralizado=True)

    pygame.display.flip()
    relogio.tick(FPS)

print("Encerrando cliente...")
if conectado and socket_cliente:
    try:
        socket_cliente.shutdown(socket.SHUT_RDWR)
    except socket.error:
        pass 
    socket_cliente.close()
pygame.quit()
sys.exit()
