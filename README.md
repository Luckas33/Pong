# Pong Multiplayer com Sockets em Python 🥅

## Descrição 📝
Este é um projeto clássico do jogo Pong implementado em Python usando a biblioteca Pygame para os gráficos e a biblioteca `socket` para a funcionalidade multiplayer em rede. O jogo permite que dois jogadores joguem Pong em máquinas diferentes (ou na mesma máquina para teste), com um atuando como servidor e o outro como cliente.

O servidor é autoritativo, gerenciando o estado do jogo, a física da bola e a pontuação. O cliente envia suas entradas de controle e recebe o estado atualizado do jogo para renderização.

## Funcionalidades ✨
* Jogabilidade clássica do Pong para dois jogadores.
* Arquitetura cliente-servidor usando sockets TCP.
* Player 1 (controlado pelo servidor) usa as teclas de seta Cima/Baixo.
* Player 2 (controlado pelo cliente) usa as teclas W/S.
* O servidor inicia a bola com a tecla Espaço.
* Contagem de pontuação até um limite para determinar o vencedor.
* Mensagens de status do jogo (aguardando jogador, início, fim de jogo).
* Possibilidade de jogar localmente (servidor e cliente na mesma máquina) ou pela internet (requer configuração de rede).

## Tecnologias Utilizadas 🛠️
* **Python 3:** Linguagem de programação principal.
* **Pygame:** Biblioteca para desenvolvimento de jogos 2D (gráficos, som, entrada).
* **Socket:** Módulo nativo do Python para programação de rede (comunicação TCP/IP).
* **JSON:** Para serializar e desserializar os dados do estado do jogo transmitidos pela rede.
* **Threading:** Usado no servidor para lidar com a comunicação do cliente de forma não bloqueante.

## Configuração do Ambiente ⚙️
1.  **Python 3:** Certifique-se de ter o Python 3 instalado. Você pode baixá-lo em [python.org](https://www.python.org/).
2.  **Pygame:** Instale a biblioteca Pygame. Abra seu terminal ou prompt de comando e digite:
    ```bash
    pip install pygame
    ```

## Como Executar o Jogo 🚀

Você precisará de dois terminais ou prompts de comando para executar o servidor e o cliente separadamente.

### 1. Rodando o Servidor (`Servidor.py`)
* Abra um terminal.
* Navegue até a pasta onde o arquivo `Servidor.py` está localizado.
* Execute o script do servidor:
    ```bash
    python Servidor.py
    ```
* O servidor iniciará e exibirá uma mensagem como "Servidor escutando em 0.0.0.0:12345". Uma janela do Pygame para o servidor também será aberta, mostrando "AGUARDANDO CLIENTE (PLAYER 2)...".

### 2. Rodando o Cliente (`Cliente.py`)
* Abra um **segundo** terminal.
* Navegue até a pasta onde o arquivo `Cliente.py` está localizado.
* Execute o script do cliente:
    ```bash
    python Cliente.py
    ```

#### Jogando Localmente (na mesma máquina)
* No `Cliente.py`, a variável `SERVER_IP` deve estar definida como `'127.0.0.1'`.
    ```python
    # Em Cliente.py
    SERVER_IP = '127.0.0.1' 
    SERVER_PORT = 12345 
    ```
* Após o servidor ser iniciado, execute o cliente. Ele deve se conectar automaticamente.

#### Jogando pela Internet (com um amigo em outra casa)
Para que um amigo em outra casa se conecte ao seu servidor, algumas etapas adicionais são necessárias **para quem está hospedando o servidor**:

1.  **Descubra seu IP Público:** Pesquise "qual é o meu IP" no Google. Este é o endereço que seu amigo usará.
2.  **Configure o Redirecionamento de Portas (Port Forwarding):**
    * Acesse as configurações do seu roteador.
    * Crie uma regra para redirecionar o tráfego da porta `12345` (ou a porta definida em `SERVER_PORT`) para o endereço IP privado da máquina que está rodando o `Servidor.py`. O protocolo é **TCP**.
    * Este passo é crucial para permitir que conexões externas cheguem ao seu computador.
3.  **Configure seu Firewall:** Certifique-se de que o firewall do seu computador (e possivelmente do roteador) permite conexões de entrada na porta `12345` para o script Python ou `Servidor.py`.

**Para o seu amigo (o cliente):**
* Ele precisará editar o arquivo `Cliente.py` e alterar a variável `SERVER_IP` para o **seu endereço IP público** que você obteve no passo 1.
    ```python
    # Em Cliente.py (na máquina do seu amigo)
    SERVER_IP = 'SEU_IP_PUBLICO_AQUI' 
    ```

### Início do Jogo
* Após o cliente se conectar, o Player 1 (na janela do servidor) pressiona a tecla **ESPAÇO** para iniciar a bola.

## Como Jogar 🎮
* **Player 1 (Servidor - paddle da direita):**
    * Seta para Cima: Mover para cima
    * Seta para Baixo: Mover para baixo
    * Espaço: Lançar a bola (quando o jogo está esperando para iniciar)
* **Player 2 (Cliente - paddle da esquerda):**
    * W: Mover para cima
    * S: Mover para baixo
* **Objetivo:** Rebater a bola para que o oponente não consiga alcançá-la. O primeiro a atingir `WINNING_SCORE` (atualmente 5) pontos vence.
* **Reiniciar:** Após o fim do jogo, o Player 1 (servidor) pode pressionar **ENTER** para reiniciar a partida.

## Estrutura dos Arquivos 📁
* `Servidor.py`: Contém a lógica do servidor do jogo, controla o Player 1 e a física do jogo.
* `Cliente.py`: Contém a lógica do cliente do jogo, controla o Player 2 e renderiza o estado recebido do servidor.
