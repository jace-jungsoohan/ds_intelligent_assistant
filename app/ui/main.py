
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
        border-radius: 8px; /* Less rounded */
        padding: 12px 20px;
        border: 1px solid #dfe1e5;
        font-size: 16px;
        box-shadow: none; 
        height: 50px; 
    }
    .stTextInput > div > div > input:focus {
        border-color: #4285f4;
        box-shadow: 0 1px 6px rgba(32, 33, 36, 0.28);
    }
    
    /* Search Button Styling */
    div[data-testid="column"] button {
        border-radius: 8px !important; /* Less rounded */
        height: 50px !important; 
        width: 50px !important;
        padding: 0 !important;
        border: 1px solid #dfe1e5 !important;
        background-color: #ffffff !important;
        font-size: 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
        margin-top: 28px !important; 
    }
    
    div[data-testid="column"] button:hover {
        background-color: #f8f9fa !important;
        border-color: #dfe1e5 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Hide input label gap to help alignment */
    .stTextInput > label {
        display: none;
    }

    /* Suggestion Buttons */
    .suggestion-btn > div > div > div > button {
        border-radius: 20px;
        border: 1px solid #e8eaed;
        background-color: #f8f9fa;
        color: #3c4043;
        font-size: 13px;
        padding: 6px 16px;
        margin: 4px 6px 4px 0px;
        height: auto;
        min-height: 2.2rem;
        white-space: normal;
        line-height: 1.4;
        text-align: left;
    }
    
    .title-text {
        text-align: center;
        font-size: 28px;
        color: #202124;
        margin-bottom: 5px; /* Reduced bottom margin */
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .subtitle-text {
        text-align: center;
        color: #5f6368;
        font-size: 15px;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- State Management ---
# --- Helper Functions (Cached for Performance) ---
@st.cache_resource
def get_orchestrator():
    return Orchestrator()

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = get_orchestrator()

# --- State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize widget_input if not present to avoid widget creation error
if "widget_input" not in st.session_state:
    st.session_state.widget_input = ""

if "query_input" not in st.session_state:
    st.session_state.query_input = ""

# --- Helper Functions ---
def process_message():
    """Callback for text input on_change or search button click"""
    # Sync query_input with widget_input (bound by key)
    if "widget_input" in st.session_state:
        st.session_state.query_input = st.session_state.widget_input
    
    prompt = st.session_state.query_input
    if not prompt:
        return
    
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
    # Clear both state variables to reset widget
    st.session_state.query_input = ""
    st.session_state.widget_input = "" 

def set_query_callback(text):
    """Callback for suggested question buttons"""
    # Directly update the widget state key
    st.session_state.widget_input = text
    st.session_state.query_input = text

# --- UI Layout ---
# Add top spacer to push search bar down
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

st.markdown("<div class='title-text'>Willog 무엇이든 물어보세요</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle-text'>물류 데이터 분석부터 리스크 예측까지 AI가 도와드릴게요</div>", unsafe_allow_html=True)

# --- Top Query Area ---
with st.container():
    c_l, c_input, c_btn, c_r = st.columns([1, 6, 0.5, 1])
    
    with c_input:
        # REMOVED 'value' arg to fix "widget created with default value" error.
        # Streamlit bi-directionally syncs with state via 'key'.
        st.text_input(
            "Search",
            placeholder="궁금한 내용을 입력해주세요...",
            label_visibility="collapsed",
            key="widget_input", 
            on_change=process_message
        )
    with c_btn:
        st.button("🔍", on_click=process_message, use_container_width=True)

    # --- Suggested Questions (3 Columns) ---
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
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

    st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
    
    # 3 columns layout
    for i in range(0, len(suggestions), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(suggestions):
                cols[j].button(
                    suggestions[i+j], 
                    key=f"sug_{i+j}", 
                    on_click=set_query_callback, 
                    args=(suggestions[i+j],), 
                    use_container_width=True
                )
            
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
