
import streamlit as st
import sys
import os
from io import StringIO

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.agents.orchestrator import Orchestrator

# Initialize Orchestrator
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

# Page Config
st.set_page_config(page_title="Willog AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 Willog Intelligent Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Helper Function to Process Message ---
def process_message(prompt):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get response from Orchestrator
    with st.chat_message("assistant"):
        with st.spinner("데이터 분석 중..."):
            try:
                # Redirect stdout to capture logs
                old_stdout = sys.stdout
                sys.stdout = mystdout = StringIO()
                
                # Run Orchestrator
                response_text = st.session_state.orchestrator.run(prompt)
                
                # Restore stdout
                sys.stdout = old_stdout
                debug_logs = mystdout.getvalue()
                
                st.markdown(response_text)
                
                # Show debug logs in expander
                with st.expander("🔍 디버그 로그 확인"):
                    st.code(debug_logs)
                    
            except Exception as e:
                response_text = f"오류가 발생했습니다: {str(e)}"
                st.error(response_text)
                # Restore stdout in case of error
                sys.stdout = old_stdout
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_text})


# --- Suggested Questions ---
st.markdown("### 💡 추천 질문")
col1, col2, col3 = st.columns(3)

if col1.button("📉 상하이(CNSHG)행 물량은?", use_container_width=True):
    process_message("상하이(CNSHG)행 총 운송 물량 알려줘")

if col2.button("🌡️ 오사카(JPOSA)행 온도 이탈 분석", use_container_width=True):
    process_message("최근 오사카(JPOSA)행 운송 건들의 온도 관리 현황을 요약해줘")

if col3.button("💥 주요 구간별 충격 발생 현황", use_container_width=True):
    process_message("운송 구간별로 충격이 많이 발생하는 목적지 상위 3곳 알려줘")

st.markdown("---")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("물류 데이터에 대해 무엇이든 물어보세요..."):
    process_message(prompt)

# Sidebar
with st.sidebar:
    st.header("설정")
    if st.button("🗑️ 대화 기록 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.markdown("**Version**: 0.2.0")
    st.markdown("**Model**: gemini-2.5-flash")
    st.markdown("**Region**: asia-northeast3")
