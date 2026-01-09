
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
        padding: 15px 25px;
        border: 1px solid #dfe1e5;
        font-size: 16px;
        box-shadow: 0 1px 6px 0 rgba(32, 33, 36, 0.28);
    }
    .stTextInput > div > div > input:focus {
        border-color: #4285f4;
        box-shadow: 0 1px 6px 0 rgba(32, 33, 36, 0.28);
    }
    /* Suggestion Buttons as Text Pill style */
    .stButton > button {
        border-radius: 18px;
        border: 1px solid #dadce0;
        background-color: #f8f9fa;
        color: #3c4043;
        font-size: 14px;
        padding: 8px 16px;
        margin: 4px;
        height: auto;
        white-space: normal; /* Allow text wrap */
        line-height: 1.4;
        text-align: left; /* Text alignment */
    }
    .stButton > button:hover {
        background-color: #f1f3f4;
        border-color: #dadce0;
        color: #202124;
    }
    /* Hide the default "Press Enter to apply" text */
    .stDeployButton {display:none;}
    
    .title-text {
        text-align: center;
        font-size: 24px;
        color: #202124;
        margin-bottom: 30px;
        font-weight: 500;
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

# --- Helper Functions ---
def process_message():
    """Callback for text input on_change or search button click"""
    # 1. Get input from widget key if triggered by text input
    if "widget_input" in st.session_state:
        st.session_state.query_input = st.session_state.widget_input
    
    prompt = st.session_state.query_input
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
    # Clear input
    st.session_state.query_input = ""
    st.session_state.widget_input = ""  # Clear widget as well

def set_query_callback(text):
    """Callback for suggested question buttons"""
    st.session_state.query_input = text
    # Note: We don't auto-execute (process_message) here as requested, just fill the text.
    # To reflect this change in the widget, we update the widget key if it exists, or let value= take over.
    # However, st.text_input with key takes precedence. So we update the session state variable bound to the key?
    # No, 'value' arg works if key is not in state yet OR we update the key directly.
    st.session_state.widget_input = text

# --- UI Header ---
st.markdown("<div class='title-text'>무슨 작업을 하고 계세요?</div>", unsafe_allow_html=True)

# --- Top Query Area ---
with st.container():
    col_l, col_center, col_btn, col_r = st.columns([1, 6, 1, 1])
    with col_center:
        # Search Input
        # Use on_change for Enter key submission
        # Bind value to session state via 'key' is tricky when we want to update it programmatically.
        # Best way: Use a separate key ('widget_input') and default value from state.
        st.text_input(
            "Search",
            value=st.session_state.get("widget_input", st.session_state.query_input),
            placeholder="무엇이든 물어보세요",
            label_visibility="collapsed",
            key="widget_input", 
            on_change=process_message
        )

    with col_btn:
        # Search Button (Restored)
        # Use a callback to trigger processing
        # Need vertical alignment padding
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        st.button("🔍", on_click=process_message, use_container_width=True)

    with col_center:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # --- Suggested Questions (10 items) ---
        suggestions = [
            "상하이(CNSHG)행 총 운송 물량 알려줘",
            "오사카(JPOSA)행 운송 건들의 온도 관리 현황 요약해줘",
            "구간별 충격 상위 3곳 분석해줘 (히트맵)",
            "누적 충격 피로도가 높은 운송 건 Top 5 알려줘",
            "최근 1주일간 발생한 위험 등급(High Risk) 건 보여줘",
            "해상 운송 시 파손율이 높은 포장 타입은?",
            "베트남행 화물 중 습도 이탈이 잦은 구간은?",
            "영하 온도에서 5G 이상 충격 발생 건수는?",
            "운송사별 평균 이탈률과 안전 점수 비교해줘",
            "포장 타입 A와 B의 충격 흡수 성능 비교해줘"
        ]

        # Grid Layout
        s_cols = st.columns(2)
        for i, question in enumerate(suggestions):
            col_idx = i % 2
            # Use on_click callback to avoid StreamlitAPIException
            s_cols[col_idx].button(
                question, 
                key=f"suger_{i}", 
                use_container_width=True,
                on_click=set_query_callback,
                args=(question,)
            )

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
