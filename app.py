import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from utils.db import init_db, get_question_stats
from utils.gemini import check_api_key, load_settings, get_provider_with_key
from utils.ui import inject_custom_css, render_header

init_db()

st.set_page_config(
    page_title="动物医学 AI 刷题系统",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()
render_header("动物医学 AI 刷题系统", "🐾")

st.sidebar.title("📚 功能导航")
st.sidebar.markdown("---")

settings = load_settings()
selected_provider = settings.get("provider", "gemini")
provider = get_provider_with_key(selected_provider)

provider_labels = {
    "gemini": "Gemini",
    "glm": "GLM",
    "nvidia": "NVIDIA",
    "deepseek": "DeepSeek"
}

if not provider:
    st.error("⚠️ 未检测到可用的 API Key，请在设置页填写任意一个")
else:
    if provider != selected_provider:
        st.info(f"当前未配置 {provider_labels.get(selected_provider, selected_provider)} Key，已自动使用 {provider_labels.get(provider, provider)}")
    with st.spinner("检查 API 连接..."):
        api_ok = check_api_key()

    if api_ok:
        st.sidebar.success("✅ API 连接正常")
    else:
        st.sidebar.error("❌ API 连接失败")

st.markdown("---")

stats = get_question_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div class="stat-number">{stats['total']}</div>
        <div class="stat-label">题目总数</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    type_count = len(stats['by_type'])
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <div class="stat-number">{type_count}</div>
        <div class="stat-label">题型种类</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    cat_count = len(stats['by_category'])
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div class="stat-number">{cat_count}</div>
        <div class="stat-label">学科分类</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
        <div class="stat-number">8</div>
        <div class="stat-label">支持题型</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### 🎯 功能快速入口")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/1_导入题库.py", label="📥 **导入题库**", use_container_width=True)
    st.caption("支持多种格式，AI 自动识别")

with col2:
    st.page_link("pages/2_刷题模式.py", label="📝 **刷题模式**", use_container_width=True)
    st.caption("随机抽题，AI 智能判题")

with col3:
    st.page_link("pages/3_考试模式.py", label="📋 **考试模式**", use_container_width=True)
    st.caption("全真模拟，自动评分")
    
with col4:
    st.page_link("pages/4_题库管理.py", label="🤖 **题库管理**", use_container_width=True)
    st.caption("管理题目，AI 智能出题")

if stats['by_type']:
    st.markdown("### 📊 题库概览")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**按题型**")
        for q_type, count in stats['by_type'].items():
            st.progress(count / max(stats['total'], 1), text=f"{q_type}: {count}")
    
    with col2:
        if stats['by_category']:
            st.markdown("**按学科**")
            for category, count in list(stats['by_category'].items())[:5]:
                st.progress(count / max(stats['total'], 1), text=f"{category}: {count}")

st.markdown("""
<div style="text-align: center; color: #94a3b8; padding: 1rem; font-size: 0.8rem; border-top: 1px solid #e2e8f0; margin-top: 2rem;">
    <p>💡 使用左侧导航栏开启学习之旅 | Powered by Google Gemini</p>
</div>
""", unsafe_allow_html=True)
