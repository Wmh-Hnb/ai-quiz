import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.gemini import load_settings, save_settings, GLM_BASE_URL, DEEPSEEK_BASE_URL
from utils.ui import inject_custom_css
import requests

st.set_page_config(page_title="设置", page_icon="⚙️", layout="wide")
inject_custom_css()

st.title("⚙️ 模型与 API 设置")
st.markdown("在这里配置 AI 供应商、API Key 与模型")
st.markdown("---")

settings = load_settings()

with st.container():
    col_prov, col_act = st.columns([2, 1])
    with col_prov:
        provider_options = ["gemini", "glm", "nvidia", "deepseek"]
        current_provider = settings.get("provider", "gemini")
        provider_index = provider_options.index(current_provider) if current_provider in provider_options else 0
        
        provider = st.radio(
            "选择首选 AI 供应商",
            provider_options,
            index=provider_index,
            horizontal=True
        )
    with col_act:
        st.markdown("")
        st.markdown("") 
        save_btn = st.button("💾 保存所有设置", type="primary", use_container_width=True)

st.markdown("---")

tab_gemini, tab_glm, tab_nvidia, tab_deepseek = st.tabs(["Gemini 配置", "GLM 配置", "NVIDIA 配置", "DeepSeek 配置"])

with tab_gemini:
    col1, col2 = st.columns(2)
    with col1:
        gemini_api_key = st.text_input(
            "API Key",
            type="password",
            value=settings.get("gemini", {}).get("api_key", ""),
            placeholder="输入 Gemini API Key"
        )
    with col2:
        gemini_model = st.text_input(
            "模型名称",
            value=settings.get("gemini", {}).get("model", "gemini-2.5-flash"),
            placeholder="例如：gemini-2.5-flash"
        )
    st.caption("获取 Key: [Google AI Studio](https://aistudio.google.com/)")

with tab_glm:
    col1, col2 = st.columns(2)
    with col1:
        glm_api_key = st.text_input(
            "API Key",
            type="password",
            value=settings.get("glm", {}).get("api_key", ""),
            placeholder="粘贴完整的 API Key"
        )
    with col2:
        glm_model = st.selectbox(
            "模型选择",
            ["glm-4.7"],
            index=0
        )
    st.caption("获取 Key: [智谱 AI](https://open.bigmodel.cn/)")
    
    if st.button("测试 GLM 连接", key="test_glm"):
        api_key = (glm_api_key or "").strip()
        if not api_key:
            st.error("请先填写 GLM API Key")
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": glm_model,
                    "messages": [{"role": "user", "content": "你好"}],
                    "stream": False
                }
                with st.spinner("连接中..."):
                    resp = requests.post(
                        f"{GLM_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=10
                    )
                if resp.ok:
                    st.success("✅ 连接成功")
                else:
                    st.error(f"❌ 失败: {resp.status_code}")
            except Exception as e:
                st.error(f"❌ 错误: {str(e)}")

with tab_nvidia:
    col1, col2 = st.columns(2)
    with col1:
        nv_api_key = st.text_input(
            "API Key",
            type="password",
            value=settings.get("nvidia", {}).get("api_key", ""),
            placeholder="nvapi-..."
        )
    with col2:
        nv_model = st.selectbox(
            "模型选择",
            ["z-ai/glm4.7", "minimaxai/minimax-m2.1"],
            index=["z-ai/glm4.7", "minimaxai/minimax-m2.1"].index(
                settings.get("nvidia", {}).get("model", "z-ai/glm4.7")
            ) if settings.get("nvidia", {}).get("model", "z-ai/glm4.7") in ["z-ai/glm4.7", "minimaxai/minimax-m2.1"] else 0
        )
    st.caption("获取 Key: [NVIDIA NIM](https://build.nvidia.com/)")
    
    if st.button("测试 NVIDIA 连接", key="test_nvidia"):
        api_key = (nv_api_key or "").strip()
        if not api_key:
            st.error("请先填写 NVIDIA API Key")
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": nv_model,
                    "messages": [{"role": "user", "content": "你好"}],
                    "stream": False
                }
                with st.spinner("连接中..."):
                    resp = requests.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=10
                    )
                if resp.ok:
                    st.success("✅ 连接成功")
                else:
                    st.error(f"❌ 失败: {resp.status_code}")
            except Exception as e:
                st.error(f"❌ 错误: {str(e)}")

with tab_deepseek:
    col1, col2 = st.columns(2)
    with col1:
        ds_api_key = st.text_input(
            "API Key",
            type="password",
            value=settings.get("deepseek", {}).get("api_key", ""),
            placeholder="sk-..."
        )
    with col2:
        ds_model = st.selectbox(
            "模型选择",
            ["deepseek-chat", "deepseek-reasoner"],
            index=0
        )
    st.caption("获取 Key: [DeepSeek Platform](https://platform.deepseek.com/)")

    if st.button("测试 DeepSeek 连接", key="test_deepseek"):
        api_key = (ds_api_key or "").strip()
        if not api_key:
            st.error("请先填写 DeepSeek API Key")
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": ds_model,
                    "messages": [{"role": "user", "content": "你好"}],
                    "stream": False
                }
                with st.spinner("连接中..."):
                    resp = requests.post(
                        f"{DEEPSEEK_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=10
                    )
                if resp.ok:
                    st.success("✅ 连接成功")
                else:
                    st.error(f"❌ 失败: {resp.status_code} {resp.text[:200]}")
            except Exception as e:
                st.error(f"❌ 错误: {str(e)}")

if save_btn:
    new_settings = {
        "provider": provider,
        "gemini": {
            "api_key": (gemini_api_key or "").strip(),
            "model": (gemini_model or "").strip() or "gemini-2.5-flash"
        },
        "glm": {
            "api_key": (glm_api_key or "").strip(),
            "model": glm_model or "glm-4.7"
        },
        "nvidia": {
            "api_key": (nv_api_key or "").strip(),
            "model": nv_model or "z-ai/glm4.7"
        },
        "deepseek": {
            "api_key": (ds_api_key or "").strip(),
            "model": ds_model or "deepseek-chat"
        }
    }
    save_settings(new_settings)
    st.success("✅ 设置已保存，下次启动自动加载")
