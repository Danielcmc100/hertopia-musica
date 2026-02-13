# Hertopia Musica

Um script Python para converter arquivos MIDI em comandos de teclado para tocar música dentro do jogo (Hertopia).

## Pré-requisitos

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (Gerenciador de pacotes e projetos Python)

## Instalação

Este projeto utiliza o `uv` para gerenciamento de dependências. Não é necessário criar um ambiente virtual manualmente.

1. Clone o repositório (ou baixe os arquivos).
2. No diretório do projeto, as dependências serão instaladas automaticamente na primeira execução do `uv run`.

## Como Usar

### 1. Gerar um arquivo MIDI de teste (Opcional)

Se você não tiver um arquivo MIDI, pode gerar um simples (Escala de Dó Maior) para testar:

```bash
uv run generate_test_midi.py
```
Isso criará o arquivo `test.mid` na pasta do projeto.

### 2. Executar o Player

**Nota:** Como utilizamos drivers virtuais de teclado para evitar travamentos, é necessário rodar com `sudo`.

```bash
sudo uv run run_music.py <caminho_do_arquivo.mid>
```

**Exemplo:**
```bash
sudo uv run run_music.py test.mid
```

### Opções Adicionais

Você pode ajustar a execução com os seguintes argumentos:

- `--speed`: Ajusta a velocidade da reprodução. (Padrão: 1.0)
  - Exemplo (mais rápido): `uv run run_music.py test.mid --speed 1.5`
  - Exemplo (mais lento): `uv run run_music.py test.mid --speed 0.8`

- `--transpose`: Transpõe as notas em semitons. Útil para ajustar músicas para a escala do jogo (Dó Maior).
  - Exemplo (subir 2 semitons): `uv run run_music.py test.mid --transpose 2`
  - Exemplo (descer 1 oitava / 12 semitons): `uv run run_music.py test.mid --transpose -12`

- `--dry-run`: Modo de teste. Imprime as teclas no terminal em vez de pressioná-las.
  - Exemplo: `uv run run_music.py test.mid --dry-run`

### Mapeamento de Teclas

O script mapeia 3 oitavas da escala natural (teclas brancas do piano) para o teclado do jogo:

- **Oitava Baixa (C3 - B3):** Z, X, C, V, B, N, M
- **Oitava Média (C4 - B4):** A, S, D, F, G, H, J
- **Oitava Alta (C5 - B5):** Q, W, E, R, T, Y, U
- **Dó Mais Alto (C6):** I

Notas sustenidas/bemóis (teclas pretas) serão ignoradas a menos que você use `--transpose` para movê-las para uma nota natural.
