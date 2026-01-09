
import streamlit as st
import sys
import os
from io import StringIO

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.agents.orchestrator import Orchestrator

# --- Page Config & Styling ---
st.set_page_config(page_title="Willog AI Assistant", page_icon="🤖", layout="wide")

# Custom CSS for the pill-shaped search bar and premium look
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 10px 25px;
        border: 1px solid #e0e0e0;
        font-size: 16px;
    }
    .stButton > button {
        border-radius: 20px;
        border: 1px solid #f0f0f0;
        background-color: #fcfcfc;
        color: #555;
    }
    .centered-text {
        text-align: center;
        margin-bottom: 30px;
        color: #333;
        font-weight: 600;
    }
    .search-container {
        max-width: 800px;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

# --- State Management ---
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = []

# This stores the text value for the input box
if "query_input" not in st.session_state:
    st.session_state.query_input = ""

# --- Helper Function ---
def process_message(prompt):
    if not prompt:
        return
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare stdout capture
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    
    try:
        # Run Orchestrator
        with st.spinner("데이터를 분석하고 있습니다..."):
            response_text = st.session_state.orchestrator.run(prompt)
    except Exception as e:
        response_text = f"오류가 발생했습니다: {str(e)}"
    
    # Restore stdout
    sys.stdout = old_stdout
    debug_logs = mystdout.getvalue()
    
    # Add assistant response
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response_text,
        "debug": debug_logs
    })
    # Clear the input for next time
    st.session_state.query_input = ""

def set_query(text):
    st.session_state.query_input = text

# --- UI Header ---
st.markdown("<h1 class='centered-text'>지금 무슨 생각을 하시나요?</h1>", unsafe_allow_html=True)

# --- Top Query Area ---
with st.container():
    # Search Bar Section
    col_l, col_m, col_r = st.columns([1, 4, 1])
    with col_m:
        # We use a form to handle submission but a separate input to handle 'value' updates from buttons
        user_text = st.text_input(
            "What's on your mind?",
            value=st.session_state.query_input,
            placeholder="무엇이든 물어보세요",
            label_visibility="collapsed",
            key="input_box"
        )
        
        c1, c2, c3 = st.columns([4, 1, 1])
        if c1.button("질문하기", type="primary", use_container_width=True):
            process_message(user_text)
            st.rerun()
            
    # --- Suggested Questions Section ---
    st.markdown("<p style='text-align: center; color: #888; margin-top: 20px;'>💡 추천 질문 (입력창에 자동 입력됩니다)</p>", unsafe_allow_html=True)
    
    # Arrange 5 buttons in 2 rows or a wrap
    s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)
    
    if s_col1.button("📉 상하이 물량", use_container_width=True):
        set_query("상하이(CNSHG)행 총 운송 물량 알려줘")
        st.rerun()
        
    if s_col2.button("🌡️ 오사카 온도", use_container_width=True):
        set_query("최근 오사카(JPOSA)행 운송 건들의 온도 관리 현황을 요약해줘")
        st.rerun()
        
    if s_col3.button("💥 구간별 충격", use_container_width=True):
        set_query("운송 구간별로 충격이 많이 발생하는 목적지 상위 3곳 알려줘")
        st.rerun()
        
    if s_col4.button("📍 이슈 지역", use_container_width=True):
        set_query("최근 1주일간 물류 이슈가 가장 빈번했던 목적지는 어디야?")
        st.rerun()
        
    if s_col5.button("📊 충격 비율", use_container_width=True):
        set_query("전체 운송 건 중 충격 알람이 발생한 비율을 분석해줘")
        st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- Results Area (Bottom) ---
if st.session_state.messages:
    # Display in normal order (Newest at bottom)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("debug"):
                with st.expander("🔍 디버그 로그 확인"):
                    st.code(message["debug"])

# --- Sidebar ---
with st.sidebar:
    st.header("설정")
    if st.button("🗑️ 대화 기록 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.query_input = ""
        st.rerun()
    st.markdown("---")
    st.markdown("**Version**: 0.4.0")
    st.markdown("**Model**: gemini-2.5-flash")
    st.markdown("**Connected**: BigQuery (Seoul)")
