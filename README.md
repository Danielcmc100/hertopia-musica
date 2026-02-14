# Hertopia Musica (Architecture 2.0)

Ferramentas para rodar múltiplas instâncias do Heartopia com isolamento total de input e janela. Cada jogo roda em seu próprio display virtual, permitindo que você use o PC normalmente enquanto os bots tocam música em background.

## Arquitetura

O projeto utiliza uma combinação de tecnologias para garantir que o input musical vá *apenas* para o jogo, sem interferir no seu uso do computador:

1.  **Xephyr:** Cria um servidor X11 aninhado (uma janela que age como um monitor separado).
2.  **Openbox:** Um gerenciador de janelas leve que roda *dentro* do Xephyr para garantir que o jogo mantenha o foco.
3.  **Input Bridge (`input_bridge.py`):** Um script Python customizado que lê eventos de um teclado virtual (`evdev`) e os injeta diretamente na janela do jogo usando o protocolo XTest, garantindo que o input funcione mesmo se a janela do Xephyr estiver em segundo plano.

## Pré-requisitos

1.  **Python 3.13+** e [uv](https://github.com/astral-sh/uv).
2.  **Dependências de Sistema:**
    ```bash
    sudo apt install xserver-xephyr openbox xdotool
    ```
3.  **Permissões de Input (Configuração Única):**
    Para criar teclados virtuais:
    ```bash
    sudo cp 99-hertopia-ignore.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules && sudo udevadm trigger
    # Adicione seu usuário ao grupo input se necessário
    sudo usermod -aG input $USER
    ```

## Como Usar

### 1. Iniciar uma Instância Isolada

Execute o `launcher.sh`. Ele fará tudo automaticamente: criar o dispositivo virtual, abrir o Xephyr, iniciar o Openbox, o Input Bridge e o jogo.

```bash
./launcher.sh
```

- Uma janela preta (Xephyr) abrirá.
- O jogo iniciará dentro dela.
- O terminal mostrará o `DEVICE_PATH` (ex: `/dev/input/event24`).

**Performance:**
O launcher já vem configurado para:
- Resolução **800x600** (para economizar GPU em múltiplas instâncias).
- **60 FPS** fixos.
- **OpenGL (WINED3D)** forçado, pois o Xephyr não suporta Vulkan bem.
- **Host Cursor**, para o mouse não ter lag.

### 2. Tocar Música

Em outro terminal, envie os comandos MIDI para o dispositivo criado:

```bash
# Exemplo para Bateria
uv run run_music.py --device-path /dev/input/event24 --layout drums musicas/bateria.mid

# Exemplo para Guitarra
uv run run_music.py --device-path /dev/input/event24 --layout guitar musicas/guitarra.mid
```

*(O input funcionará mesmo se você minimizar a janela do Xephyr ou estiver usando outro programa!)*

### 3. Múltiplas Instâncias

Basta rodar `./launcher.sh` novamente em outro terminal. Ele criará um novo display (`:101`, `:102`...) e um novo device (`/dev/input/event25`...) automaticamente.

## Solução de Problemas

- **Jogo crasha ao abrir:** Verifique se o `Xephyr` suporta OpenGL no seu sistema. O launcher usa `PROTON_USE_WINED3D=1` para mitigar isso.
- **Input não funciona em background:** O `openbox` deve estar rodando dentro do Xephyr. Se fechou, o foco pode ser perdido. O launcher cuida disso.
- **Permissão negada no `/dev/input`:** Rode `ls -l /dev/input/event*` e verifique se seu usuário tem acesso (grupo `input`). Reinicie a sessão após adicionar o grupo.
