
import streamlit as st
import sys
import os
from io import StringIO

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.agents.orchestrator import Orchestrator

# --- Page Config & Styling ---
st.set_page_config(page_title="Willog AI Assistant", page_icon="🤖", layout="wide")

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    /* Input Box Styling */
    .stTextInput > div > div > input {
        border-radius: 30px;
        padding: 12px 20px;
        border: 1px solid #dfe1e5;
        font-size: 16px;
        box-shadow: 0 1px 6px 0 rgba(32, 33, 36, 0.28);
    }
    
    /* Search Button Styling (make it look integrated) */
    div[data-testid="column"] > div > div > div > div > button {
        border-radius: 50%;
        height: 48px;
        width: 48px;
        padding: 0;
        border: none;
        background-color: #f8f9fa;
        font-size: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* Suggestion Buttons: Smaller & Tighter */
    .suggestion-btn > div > div > div > button {
        border-radius: 15px;
        border: 1px solid #e8eaed;
        background-color: #f8f9fa;
        color: #5f6368;
        font-size: 12px; /* Smaller font */
        padding: 4px 12px; /* Tighter padding */
        margin: 2px; /* Tighter gap */
        height: auto;
        min-height: 2.5rem;
        white-space: normal;
        line-height: 1.3;
        text-align: left;
    }
    .suggestion-btn > div > div > div > button:hover {
        background-color: #e8f0fe;
        color: #1967d2;
        border-color: #d2e3fc;
    }
    
    .title-text {
        text-align: center;
        font-size: 22px;
        color: #202124;
        margin-bottom: 20px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# --- State Management ---
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "query_input" not in st.session_state:
    st.session_state.query_input = ""

# --- Helper Functions ---
def process_message():
    """Callback for text input on_change or search button click"""
    if "widget_input" in st.session_state:
        st.session_state.query_input = st.session_state.widget_input
    
    prompt = st.session_state.query_input
    if not prompt:
        return
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    
    try:
        with st.spinner("데이터를 분석하고 있습니다..."):
            response_text = st.session_state.orchestrator.run(prompt)
    except Exception as e:
        response_text = f"오류가 발생했습니다: {str(e)}"
    
    sys.stdout = old_stdout
    debug_logs = mystdout.getvalue()
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response_text,
        "debug": debug_logs
    })
    st.session_state.query_input = ""
    st.session_state.widget_input = "" 

def set_query_callback(text):
    """Callback for suggested question buttons"""
    st.session_state.query_input = text
    st.session_state.widget_input = text

# --- UI Header ---
st.markdown("<div class='title-text'>무슨 작업을 하고 계세요?</div>", unsafe_allow_html=True)

# --- Top Query Area ---
with st.container():
    # Use columns to align text input and button tightly
    c_spacer_l, c_input, c_btn, c_spacer_r = st.columns([1, 8, 1, 1])
    
    with c_input:
        st.text_input(
            "Search",
            value=st.session_state.get("widget_input", st.session_state.query_input),
            placeholder="물류 데이터를 검색해보세요...",
            label_visibility="collapsed",
            key="widget_input", 
            on_change=process_message
        )
    with c_btn:
        # Align button with input box manually via margin if needed, or rely on auto alignment
        # Adding a bit of top margin/padding to align with text input height
        st.markdown("""<style>div.stButton > button:first-child { margin-top: 0px; }</style>""", unsafe_allow_html=True) 
        st.button("🔍", on_click=process_message, use_container_width=True)

    # --- Suggested Questions (Refined & Tighter) ---
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # Meaningful, actionable questions based on Whitepaper Mart
    suggestions = [
        "📉 상하이(CNSHG)행 총 물량 및 파손율",
        "🔥 구간별 충격 리스크 히트맵 분석",
        "⚠️ 누적 충격 피로도 Top 5 운송 건",
        "🌡️ 오사카행 온도 이탈 평균 지속 시간",
        "📊 포장 타입별 파손율 및 안전 점수 비교",
        "🛳️ 해상 운송 중 5G 이상 충격 발생 비율",
        "📍 베트남 경로 습도 취약 구간 분석",
        "❄️ 영하 온도에서 발생한 충격 건수",
        "🏆 운송사별 배송 품질 벤치마킹",
        "🚨 최근 1주일 High Risk 등급 운송 건"
    ]

    # Use a container class for specific styling targeting if possible, 
    # but Streamlit CSS isolation is hard. We rely on the global CSS above.
    st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
    
    # 5 columns x 2 rows for tight layout
    for i in range(0, len(suggestions), 2):
        cols = st.columns(2)
        # Left col
        cols[0].button(suggestions[i], key=f"sug_{i}", on_click=set_query_callback, args=(suggestions[i],), use_container_width=True)
        # Right col
        if i+1 < len(suggestions):
            cols[1].button(suggestions[i+1], key=f"sug_{i+1}", on_click=set_query_callback, args=(suggestions[i+1],), use_container_width=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

# --- Results Area (Reversed Order) ---
if st.session_state.messages:
    # Display Newest FIRST
    for message in reversed(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("debug"):
                with st.expander("🔍 상세 로그 (Query & Debug)"):
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
