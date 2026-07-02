"""
Interface do EDUcador - Dashboard Streamlit.
"""

import streamlit as st
import requests
import base64
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.core.pipeline import run_pipeline
from src.rag.simple_rag import SimpleRAG
from src.memory.history import Memory
from config.settings import CORPUS_PATH

st.set_page_config(
    page_title="EDUcador - Seu Professor Particular",
    page_icon=":material/school:",
    layout="centered",
    initial_sidebar_state="expanded"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = Memory(max_size=10)
if "rag" not in st.session_state:
    try:
        if CORPUS_PATH.exists():
            st.session_state.rag = SimpleRAG(str(CORPUS_PATH))
        else:
            st.session_state.rag = None
            st.session_state.rag_error = f"Arquivo de corpus nao encontrado em {CORPUS_PATH}"
    except FileNotFoundError as e:
        st.session_state.rag = None
        st.session_state.rag_error = f"Arquivo de corpus nao encontrado: {e}"
    except Exception as e:
        st.session_state.rag = None
        st.session_state.rag_error = f"Erro ao carregar RAG: {type(e).__name__}: {e}"

with st.sidebar:
    st.title("Configuracoes")

    materia = st.selectbox(
        "Materia",
        ["Matematica", "Fisica", "Quimica", "Biologia", "Geral"],
        help="Selecione a materia para contexto adicional",
    )

    nivel = st.select_slider(
        "Nivel de Ajuda",
        options=[
            "Nivel 1 (Dica sutil)",
            "Nivel 2 (Passo-chave)",
            "Nivel 3 (Resolucao completa)",
        ],
        value="Nivel 2 (Passo-chave)",
        help="Quanto mais alto, mais detalhada a explicacao",
    )

    st.divider()

    if st.session_state.rag:
        st.success(f"RAG ativo ({len(st.session_state.rag.docs)} exemplos)")
    else:
        st.warning("RAG nao disponivel")
        if getattr(st.session_state, "rag_error", None):
            st.caption(st.session_state.rag_error)

    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.rerun()

    st.divider()
    st.caption("EDUcador v1.0 - Offline First")


def process_image(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode("utf-8")

        payload = {
            "model": "llama3.2-vision",
            "prompt": "Transcreva TODO o texto desta imagem de uma questao escolar. Se houver equacoes matematicas, formate-as em LaTeX puro entre $. Retorne APENAS o texto transcrito, sem comentarios adicionais.",
            "stream": False,
            "images": [base64_image],
        }

        response = requests.post(
            "http://localhost:11434/api/generate", json=payload, timeout=60
        )
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        st.error("Ollama nao esta rodando. Inicie com 'ollama serve'")
        return None
    except Exception as e:
        st.error(f"Erro ao processar imagem: {e}")
        return None


st.title("EDUcador")
st.caption("Seu professor particular offline-first")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

uploaded_file = st.file_uploader(
    "Tire foto da questao",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed",
)

if uploaded_file:
    with st.chat_message("user"):
        st.image(uploaded_file, width=300)

    with st.spinner("Lendo a imagem..."):
        extracted_text = process_image(uploaded_file)
        if extracted_text:
            st.session_state.messages.append({
                "role": "user",
                "content": f"[Imagem]\n\n{extracted_text}",
            })
            with st.chat_message("user"):
                st.markdown(extracted_text)

            with st.chat_message("assistant"):
                with st.spinner("Processando..."):
                    try:
                        result = run_pipeline(
                            student_input=extracted_text,
                            memory=st.session_state.memory,
                            rag=st.session_state.rag,
                            scaffolding_level=nivel,
                            subject=materia if materia != "Geral" else None,
                            verbose=False,
                        )
                        st.markdown(result.final_response)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result.final_response,
                        })
                    except Exception as e:
                        st.error(f"Erro ao processar: {e}")

if student_input := st.chat_input("Digite sua duvida..."):
    with st.chat_message("user"):
        st.markdown(student_input)
    st.session_state.messages.append({"role": "user", "content": student_input})

    with st.chat_message("assistant"):
        with st.spinner("Analisando sua pergunta..."):
            try:
                result = run_pipeline(
                    student_input=student_input,
                    memory=st.session_state.memory,
                    rag=st.session_state.rag,
                    scaffolding_level=nivel,
                    subject=materia if materia != "Geral" else None,
                    verbose=False,
                )
                st.markdown(result.final_response)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"Tempo: {result.total_time_s:.1f}s")
                with col2:
                    st.caption(f"Iteracoes: {result.iterations}")
                with col3:
                    if result.rag_used:
                        st.caption("RAG utilizado")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.final_response,
                })
            except Exception as e:
                st.error(f"Erro: {e}")
