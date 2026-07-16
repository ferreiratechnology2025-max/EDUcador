import streamlit as st
import requests
import base64
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.learning.engine import create_engine, LearningEngine
from config.settings import EngineConfig

st.set_page_config(
    page_title="EDUcador - Seu Professor Particular",
    page_icon=":material/school:",
    layout="centered",
    initial_sidebar_state="expanded"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "engine" not in st.session_state:
    cfg = EngineConfig()
    st.session_state.engine = create_engine(cfg.engine)

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

    if st.session_state.engine.get_session_info("default").get("engine") == "current_pipeline":
        st.success("Motor Atual (Pipeline Clássico)")
    else:
        st.info("Motor Pedagógico (Experimental)")

    if st.button("Limpar Conversa"):
        st.session_state.messages = []
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
                        response = st.session_state.engine.process(
                            user_input=extracted_text,
                            session_id="default",
                        )
                        st.markdown(response.message)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response.message,
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
                response = st.session_state.engine.process(
                    user_input=student_input,
                    session_id="default",
                )
                st.markdown(response.message)

                meta = response.metadata or {}
                col1, col2, col3 = st.columns(3)
                with col1:
                    if "time_s" in meta:
                        st.caption(f"Tempo: {meta['time_s']}s")
                with col2:
                    if "iterations" in meta:
                        st.caption(f"Iteracoes: {meta['iterations']}")
                with col3:
                    if meta.get("rag_used"):
                        st.caption("RAG utilizado")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.message,
                })
            except Exception as e:
                st.error(f"Erro: {e}")
