import streamlit as st
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import Question, add_questions_batch
from utils.gemini import parse_questions_from_file, parse_questions_from_text, generate_questions
from utils.ui import inject_custom_css

st.set_page_config(page_title="导入题库", page_icon="📥", layout="wide")

inject_custom_css()

st.title("📥 导入题库")
st.markdown("轻量导入题库，保持版面聚焦与清晰层级")

tab1, tab2, tab3 = st.tabs(["📄 文件导入", "📝 文本导入", "🤖 AI 生成"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 📤 上传文件")
        st.markdown("""
        **支持格式：**
        - PDF 文档
        - Word (.docx)
        - 图片 (PNG/JPG)
        
        AI 将自动提取文本并识别题目。
        """)
    
    with col2:
        uploaded_file = st.file_uploader(
            "拖拽文件到此处",
            type=["pdf", "docx", "png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )
    
    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()
        file_bytes = uploaded_file.read()
        
        st.success(f"✅ 文件已就绪：**{uploaded_file.name}** ({len(file_bytes) / 1024:.1f} KB)")
        
        col_act1, col_act2 = st.columns([1, 3])
        with col_act1:
            if st.button("开始解析", key="parse_file", type="primary", use_container_width=True):
                with st.spinner("AI 正在深度分析文档结构..."):
                    result = parse_questions_from_file(file_bytes, file_type)
                
                if "error" in result:
                    st.error(f"解析失败：{result['error']}")
                    if "raw" in result:
                        with st.expander("查看调试信息"):
                            st.code(result["raw"])
                else:
                    questions = result.get("questions", [])
                    st.session_state["parsed_questions"] = questions
                    st.success(f"成功识别 {len(questions)} 道题目！")


with tab2:
    st.markdown("### 粘贴题目文本")
    
    text_input = st.text_area(
        "输入题目内容",
        height=400,
        placeholder="""示例：
1. 犬瘟热是由什么引起的？
A. 细菌
B. 病毒
答案：B

二、简答题
简述狂犬病的临床症状。""",
        label_visibility="collapsed"
    )
    
    col_t1, col_t2 = st.columns([1, 4])
    with col_t1:
        if text_input and st.button("解析文本", key="parse_text", type="primary", use_container_width=True):
            with st.spinner("AI 正在阅读文本..."):
                result = parse_questions_from_text(text_input)
            
            if "error" in result:
                st.error(f"解析失败：{result['error']}")
            else:
                questions = result.get("questions", [])
                st.session_state["parsed_questions"] = questions
                st.success(f"成功识别 {len(questions)} 道题目！")

with tab3:
    st.markdown("### AI 智能出题")
    
    with st.container():
        keywords = st.text_input(
            "核心知识点 / 主题",
            placeholder="例如：犬瘟热、兽医传染病学、细胞生物学...",
            help="输入您想要生成题目的主题或具体知识点"
        )
        
        st.markdown("#### 题目配置")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            num_single = st.number_input("单选题", min_value=0, max_value=20, value=3)
        with col2:
            num_multi = st.number_input("多选题", min_value=0, max_value=20, value=2)
        with col3:
            num_definition = st.number_input("名词解释", min_value=0, max_value=10, value=2)
        with col4:
            num_short = st.number_input("简答题", min_value=0, max_value=10, value=2)
        with col3:
            num_judge = st.number_input("判断题", min_value=0, max_value=20, value=3)
        with col4:
            num_fill = st.number_input("填空题", min_value=0, max_value=20, value=2)

        col5, col6, col7, col8 = st.columns(4)

        with col5:
            num_definition = st.number_input("名词解释", min_value=0, max_value=10, value=2)
        with col6:
            num_short = st.number_input("简答题", min_value=0, max_value=10, value=2)
        with col7:
            num_essay = st.number_input("论述题", min_value=0, max_value=5, value=1)
        with col8:
            num_case = st.number_input("病例分析题", min_value=0, max_value=5, value=1)
    
    st.markdown("")
    if keywords:
        if st.button("立即生成", key="generate", type="primary", use_container_width=True):

            requirements = {
                "名词解释": num_definition,
                "单选题": num_single,
                "多选题": num_multi,
                "填空题": num_fill,
                "简答题": num_short,
                "论述题": num_essay,
                "判断题": num_judge,
                "病例分析题": num_case
            }
            
            total = sum(requirements.values())
            if total == 0:
                st.warning("⚠️ 请至少选择一种题型")
            else:
                with st.spinner(f"AI 正在根据 '{keywords}' 生成 {total} 道题目..."):
                    result = generate_questions(keywords, requirements)
                
                if "error" in result:
                    st.error(f"生成失败：{result['error']}")
                else:
                    questions = result.get("questions", [])
                    st.session_state["parsed_questions"] = questions
                    st.success(f"成功生成 {len(questions)} 道题目！")

st.markdown("---")

if "parsed_questions" in st.session_state and st.session_state["parsed_questions"]:
    questions = st.session_state["parsed_questions"]
    
    st.markdown("### 识别结果预览")
    
    type_counts = {}
    for q in questions:
        q_type = q.get("type", "未知")
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
    
    cols = st.columns(8)
    type_names = ["名词解释", "单选题", "多选题", "填空题", "简答题", "论述题", "判断题", "病例分析题"]
    for i, t in enumerate(type_names):
        with cols[i % 8]:
            count = type_counts.get(t, 0)
            st.caption(f"**{t}**: {count}")
    
    st.markdown("### 题目详情")
    
    for i, q in enumerate(questions):
        q_content = q.get('content', '')
        q_type = q.get('type', '未知')
        preview_text = q_content[:40] + "..." if len(q_content) > 40 else q_content
        
        with st.expander(f"#{i+1} [{q_type}] {preview_text}", expanded=False):
            st.markdown(f"**题目内容：**\n\n{q_content}")
            
            options = q.get("options", [])
            if options:
                st.markdown("---")
                st.markdown("**选项：**")
                for opt in options:
                    st.markdown(f"- {opt}")
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**答案：** `{q.get('answer', '无')}`")
                st.markdown(f"**难度：** {'⭐' * q.get('difficulty', 1)}")
            with c2:
                st.markdown(f"**分类：** {q.get('category', '未分类')}")
                st.markdown(f"**关键词：** {', '.join(q.get('keywords', []))}")
                
            if q.get('explanation'):
                st.info(f"💡 **解析：** {q.get('explanation')}")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("确认入库", type="primary", use_container_width=True):
            question_objects = []
            for q in questions:
                question_objects.append(Question(
                    type=q.get("type", ""),
                    content=q.get("content", ""),
                    options=json.dumps(q.get("options", []), ensure_ascii=False),
                    answer=q.get("answer", ""),
                    keywords=",".join(q.get("keywords", [])),
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", 1),
                    category=q.get("category", "")
                ))
            
            count = add_questions_batch(question_objects)
            st.success(f"成功导入 {count} 道题目到题库！")
            st.session_state["parsed_questions"] = []
            st.rerun()
    
    with col2:
        if st.button("清空预览", use_container_width=True):
            st.session_state["parsed_questions"] = []
            st.rerun()
