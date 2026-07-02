# EDUcador

Tutor virtual offline-first para ensino medio brasileiro com validacao cruzada entre modelos.

## O que e o EDUcador?

Um assistente educacional que roda localmente no seu computador, sem depender de internet. Ele usa:

- **Gemma 3 4B** como tutor (gera respostas)
- **Phi-4-mini** como validador (revisa antes de enviar)
- **Qwen3-8B** como fallback (problemas mais complexos)
- **llama3.2-vision** como OCR (leitura de imagens de questoes)

A validacao cruzada entre modelos diferentes e mais robusta que self-check, pois cada modelo tem vieses distintos.

## Interface

O EDUcador possui duas formas de uso:

### Modo Chat (Streamlit) — **recomendado**
```bash
streamlit run interface.py
# ou (inicia automaticamente)
python run.py
```
Interface visual com:
- Chat interativo com historico
- Upload de imagem com OCR (tire foto da questao)
- Seletor de materia e nivel de dificuldade
- Metricas de cada resposta (tempo, iteracoes, RAG)

### Modo Terminal
```bash
python -c "from src.core.pipeline import run_pipeline; print(run_pipeline('2x+5=17', verbose=True).final_response)"
```

## Modelos Necessarios (via Ollama)

```bash
ollama pull gemma3:4b
ollama pull phi4-mini
ollama pull qwen3:8b
ollama pull llama3.2-vision  # opcional (para OCR)
```

Ou baixe tudo automaticamente:
```bash
python scripts/download_models.py
```

## Como Usar

### 1. Instale as dependencias
```bash
pip install -r requirements.txt
```

### 2. Inicie o Ollama
```bash
ollama serve
```

### 3. Rode o EDUcador
```bash
# Interface grafica (recomendado)
python run.py

# Modo terminal
python -m streamlit run interface.py

# Pergunta unica pelo terminal antigo
echo "qual a formula de Bhaskara?" | python run.py
```

## Estrutura do Projeto

```
EDUcador/
├── src/
│   ├── core/              # Pipeline, Tutor, Validador
│   │   ├── pipeline.py    # Orquestracao tutor -> validador -> fallback
│   │   ├── tutor.py       # Chamadas Gemma 3 4B com scaffolding
│   │   └── validator.py   # Validacao Phi-4-mini com fallback estrutural
│   ├── rag/
│   │   └── simple_rag.py  # Recuperacao por tags + BM25 (zero ML)
│   ├── memory/
│   │   └── history.py     # Historico do aluno serializavel
│   └── utils/
│       └── ollama_client.py
├── interface.py            # Dashboard Streamlit com chat + OCR
├── run.py                  # Entrypoint com verificacao automatica
├── data/
│   └── corpus.jsonl        # 10 exemplos (Mat, Fis, Quim, Bio)
├── tests/                  # Testes unitarios (10/10)
├── config/
│   └── settings.py         # Configuracoes centralizadas
├── scripts/
│   ├── download_models.py  # Download dos modelos para empacotamento
│   ├── setup.bat           # Setup inicial (Windows)
│   ├── setup.sh            # Setup inicial (Linux/Mac)
│   └── verify_ollama.bat   # Verificacao do ambiente
├── models/                 # Modelos Ollama (para embutir no instalador)
├── assets/                 # Recursos visuais
├── EDUcador.spec           # Configuracao PyInstaller
├── installer.iss           # Script Inno Setup para instalador
└── requirements.txt        # Dependencias Python
```

## Como Funciona

1. **Aluno** faz uma pergunta (texto ou imagem via OCR)
2. **RAG** recupera exemplos relevantes do corpus por tags
3. **Tutor (Gemma 3 4B)** gera uma resposta com scaffolding adequado
4. **Validador (Phi-4-mini)** revisa a resposta com 4 criterios:
   - Correcao matematica
   - Didatica
   - Ausencia de alucinacao
   - Adequacao ao nivel
5. Se aprovada -> resposta e enviada ao aluno
6. Se precisa revisao -> tutor reescreve com feedback (max 2 vezes)
7. Se rejeitada -> fallback para Qwen3-8B
8. **Memoria** armazena o historico para contexto em perguntas seguintes

## OCR (Reconhecimento de Imagem)

O EDUcador pode ler questoes de fotos usando **llama3.2-vision**:

1. Clique no seletor de arquivos na interface
2. Selecione uma foto da questao (PNG/JPG)
3. O modelo transcreve o texto e equacoes em LaTeX
4. O pipeline processa automaticamente o texto extraido

## RAG por Tags

O sistema usa um corpus de exemplos (`data/corpus.jsonl`) com tags por materia:

```json
{"id": 1, "assunto": "Equacao do 1o Grau", "tags": ["equacao_1grau"], ...}
```

A recuperacao e feita por correspondencia de tags + BM25 simplificado - **zero dependencias de ML**.

## Testes

```bash
# Suite completa
python tests/run_all_tests.py

# Individuais
python -m tests.test_rag
python -m tests.test_memory
python -m tests.test_pipeline  # requer Ollama rodando
```

## Build do Instalador

Para gerar um executavel Windows autonoma:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Baixar modelos (requer Ollama e ~7.5 GB)
python scripts/download_models.py

# 3. Build PyInstaller
pyinstaller EDUcador.spec
# Gera: dist/EDUcador/EDUcador.exe

# 4. Compilar instalador Inno Setup
# Abrir installer.iss no Inno Setup e compilar
# Gera: Output/EDUcador_Setup.exe (~7.6 GB)
```

## Configuracao

Edite `config/settings.py` para ajustar modelos, temperatura e limites.

```python
ModelConfig.tutor_model = "gemma3:4b"       # Modelo do tutor
ModelConfig.validator_model = "phi4-mini"    # Modelo validador
ModelConfig.fallback_model = "qwen3:8b"      # Modelo fallback
PipelineConfig.max_revisions = 2             # Max revisoes do validador
```

## Requisitos

- **Minimo:** Python 3.8+, 8 GB RAM, 10 GB disco
- **Recomendado:** 16 GB RAM, SSD
- Ollama instalado (https://ollama.com/)
- Modelos: ~7.5 GB espaco em disco

## Solucao de Problemas

**Erro: ConnectionRefusedError** -> Ollama nao esta rodando: `ollama serve`

**Erro: Modelo nao encontrado** -> Baixe o modelo: `ollama pull gemma3:4b`

**Resposta em loop de revisoes** -> Aumente `max_revisions` no `PipelineConfig` ou ajuste o prompt do validador

**OCR nao funciona** -> Verifique se llama3.2-vision esta instalado: `ollama pull llama3.2-vision`

## Distribuicao

O instalador final pode ser distribuido por:
- Google Drive / OneDrive (link direto)
- Torrent (para arquivos grandes ~7.6 GB)
- Servidor HTTP local

## Licenca

MIT
