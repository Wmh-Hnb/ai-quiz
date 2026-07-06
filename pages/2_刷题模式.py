import streamlit as st
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import (
    get_all_questions,
    get_random_questions,
    get_questions_by_type,
    save_practice_record,
    add_wrong_question,
    mark_question_mastered
)
from utils.gemini import grade_answer
from utils.ui import inject_custom_css

st.set_page_config(page_title="刷题模式", page_icon="📝", layout="wide")
inject_custom_css()

st.title("📝 刷题模式")
st.markdown("---")

if "practice_state" not in st.session_state:
    st.session_state.practice_state = {
        "started": False,
        "current_question": None,
        "answered": False,
        "result": None
    }

all_questions = get_all_questions()

if not all_questions:
    st.warning("⚠️ 题库为空，请先导入题目！")
    if st.button("前往导入题库"):
        st.switch_page("pages/1_导入题库.py")
else:
    with st.sidebar:
        st.markdown("### 🎯 筛选条件")
        
        question_types = ["全部"] + list(set(q.type for q in all_questions))
        selected_type = st.selectbox("题目类型", question_types, key="practice_filter_type")
        selected_type_value = selected_type or "全部"
        
        categories = ["全部"] + list(set(q.category for q in all_questions if q.category))
        selected_category = st.selectbox("学科分类", categories, key="practice_filter_category")
        selected_category_value = selected_category or "全部"
        
        difficulties = ["全部", "⭐ 简单", "⭐⭐ 中等", "⭐⭐⭐ 困难"]
        selected_difficulty = st.selectbox("难度等级", difficulties, key="practice_filter_difficulty")
        selected_difficulty_value = selected_difficulty or "全部"
        
        st.markdown("---")
        st.markdown(f"**可用题目：** {len(all_questions)} 道")
    
    if not st.session_state.practice_state["started"]:
        st.markdown("### 开始刷题")
        
        col_mode, col_space = st.columns([1, 2])
        with col_mode:
            mode = st.radio("模式选择", ["刷题模式", "背题模式"], horizontal=True)
        
        def filter_questions():
            filtered = all_questions
            if selected_type_value != "全部":
                filtered = [q for q in filtered if q.type == selected_type_value]
            if selected_category_value != "全部":
                filtered = [q for q in filtered if q.category == selected_category_value]
            if selected_difficulty_value != "全部":
                diff_map = {"⭐ 简单": 1, "⭐⭐ 中等": 2, "⭐⭐⭐ 困难": 3}
                target = diff_map.get(selected_difficulty_value)
                if target:
                    filtered = [q for q in filtered if q.difficulty == target]
            return filtered
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎲 随机抽题", type="primary", use_container_width=True):
                questions = filter_questions()
                
                if questions:
                    import random
                    question = random.choice(questions)
                    st.session_state.practice_state["current_question"] = question
                    st.session_state.practice_state["started"] = True
                    st.session_state.practice_state["answered"] = False
                    st.session_state.practice_state["result"] = None
                    st.session_state.practice_state["mode"] = mode
                    st.session_state.practice_state["question_pool_ids"] = [q.id for q in questions if q.id is not None]
                    st.session_state.practice_state["question_pool"] = questions
                    st.rerun()
                else:
                    st.error("没有符合条件的题目")
        
        with col2:
            if st.button("📋 顺序刷题", use_container_width=True):
                questions = filter_questions()
                if "practice_index" not in st.session_state:
                    st.session_state.practice_index = 0
                
                if st.session_state.practice_index < len(questions):
                    question = questions[st.session_state.practice_index]
                    st.session_state.practice_state["current_question"] = question
                    st.session_state.practice_state["started"] = True
                    st.session_state.practice_state["answered"] = False
                    st.session_state.practice_state["result"] = None
                    st.session_state.practice_state["mode"] = mode
                    st.session_state.practice_state["question_pool_ids"] = [q.id for q in questions if q.id is not None]
                    st.session_state.practice_state["question_pool"] = questions
                    st.rerun()
                else:
                    st.error("没有符合条件的题目")
        
        with col3:
            if st.button("🔄 重置进度", use_container_width=True):
                st.session_state.practice_index = 0
                st.success("进度已重置")
        
        st.markdown("### 📊 题库预览")
        
        preview_count = min(5, len(all_questions))
        for i, q in enumerate(all_questions[:preview_count]):
            with st.expander(f"{q.type} | {q.content[:50]}..."):
                st.markdown(f"**答案：** {q.answer}")
                st.markdown(f"**分类：** {q.category}")
    
    else:
        question = st.session_state.practice_state["current_question"]
        
        if question:
            col_meta1, col_meta2, col_meta3 = st.columns([1, 1, 3])
            with col_meta1:
                st.caption(f"📌 {question.type}")
            with col_meta2:
                st.caption(f"📊 {question.category}")
            with col_meta3:
                st.caption(f"⭐ 难度：{'⭐' * question.difficulty}")
            
            st.markdown(f"""
            <div class="highlight-box">
                <h3 style="margin:0; padding:0.5rem 0;">{question.content}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            if question.type in ("选择题", "单选题", "多选题"):
                options = question.get_options_list()
                if options:
                    pass
            
            mode = st.session_state.practice_state.get("mode", "刷题模式")
            pool = st.session_state.practice_state.get("question_pool") or all_questions

            if mode == "背题模式":
                with st.expander("✅ 查看标准答案", expanded=True):
                    st.success(question.answer)
                    if question.explanation:
                        st.markdown("**📖 解析：**")
                        st.write(question.explanation)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🎲 下一题（随机）", type="primary", use_container_width=True):
                        import random
                        new_question = random.choice(pool)
                        st.session_state.practice_state["current_question"] = new_question
                        st.session_state.practice_state["answered"] = False
                        st.session_state.practice_state["result"] = None
                        st.rerun()
                
                with col2:
                    if st.button("➡️ 下一题（顺序）", use_container_width=True):
                        if "practice_index" not in st.session_state:
                            st.session_state.practice_index = 0
                        st.session_state.practice_index += 1
                        
                        if st.session_state.practice_index < len(pool):
                            new_question = pool[st.session_state.practice_index]
                            st.session_state.practice_state["current_question"] = new_question
                            st.session_state.practice_state["answered"] = False
                            st.session_state.practice_state["result"] = None
                        else:
                            st.session_state.practice_state["started"] = False
                            st.success("🎉 恭喜！已完成所有题目！")
                        st.rerun()
                
                with col3:
                    if st.button("🏠 返回首页", use_container_width=True):
                        st.session_state.practice_state["started"] = False
                        st.rerun()

            elif not st.session_state.practice_state["answered"]:
                if question.type in ("选择题", "单选题", "多选题"):
                    options = question.get_options_list()
                    option_labels = [opt.split(".")[0] if "." in opt else opt[0] for opt in options]

                    if options:
                         st.info("\n".join([f"- {opt}" for opt in options]))

                    if question.type == "多选题":
                        user_answer = st.text_input("请输入答案（多个选项用逗号分隔，如 A,C）：")
                    else:
                        user_answer = st.radio("选择答案：", option_labels, horizontal=True, label_visibility="collapsed")

                    if st.button("✅ 提交", type="primary"):
                        user_answer_upper = str(user_answer).strip().upper()
                        if question.type == "多选题":
                            correct_set = set((question.answer or "").strip().upper().replace(" ", "").split(","))
                            user_set = set(user_answer_upper.replace(" ", "").replace("，", ",").split(","))
                            is_correct = user_set == correct_set
                            score = max(0, 100 - len(user_set.symmetric_difference(correct_set)) * (100 // max(len(correct_set), 1)))
                        else:
                            correct_answer = (question.answer or "").strip().upper()
                            is_correct = user_answer_upper == correct_answer
                            score = 100 if is_correct else 0

                        st.session_state.practice_state["answered"] = True
                        st.session_state.practice_state["result"] = {
                            "is_correct": is_correct,
                            "score": score,
                            "feedback": "回答正确！" if is_correct else f"回答错误，正确答案是 {question.answer}",
                            "user_answer": user_answer
                        }

                        save_practice_record(question.id or 0, str(user_answer), is_correct)
                        if not is_correct and question.id:
                            add_wrong_question(question.id, str(user_answer))
                        elif is_correct and question.id:
                            mark_question_mastered(question.id)
                        st.rerun()

                elif question.type == "判断题":
                    user_answer = st.radio("判断对错：", ["对", "错"], horizontal=True, label_visibility="collapsed")

                    if st.button("✅ 提交", type="primary"):
                        correct_answer = (question.answer or "").strip()
                        user_clean = user_answer.strip()
                        is_correct = (user_clean == "对" and (correct_answer in ("对", "正确", "T", "t", "true", "True"))) or (user_clean == "错" and (correct_answer in ("错", "错误", "F", "f", "false", "False")))

                        st.session_state.practice_state["answered"] = True
                        st.session_state.practice_state["result"] = {
                            "is_correct": is_correct,
                            "score": 100 if is_correct else 0,
                            "feedback": "回答正确！" if is_correct else f"回答错误，正确答案是 {question.answer}",
                            "user_answer": user_answer
                        }

                        save_practice_record(question.id or 0, str(user_answer), is_correct)
                        if not is_correct and question.id:
                            add_wrong_question(question.id, str(user_answer))
                        elif is_correct and question.id:
                            mark_question_mastered(question.id)
                        st.rerun()
                elif question.type == "填空题":
                    user_answer = st.text_input("请填写答案（多个空用逗号分隔）：")
                    
                    col_exit, col_submit = st.columns([1, 3])
                    with col_exit:
                        if st.button("🏠 退出", use_container_width=True):
                            st.session_state.practice_state["started"] = False
                            st.rerun()
                    with col_submit:
                        if st.button("✅ 提交", type="primary", use_container_width=True) and user_answer:
                            with st.spinner("AI 判题中..."):
                                result = grade_answer(
                                    question.type,
                                    question.content,
                                    question.answer,
                                    user_answer
                                )
                            
                            if "error" not in result:
                                result["user_answer"] = user_answer
                                st.session_state.practice_state["answered"] = True
                                st.session_state.practice_state["result"] = result
                                save_practice_record(question.id or 0, user_answer, result.get("is_correct", False))
                                if question.id and not result.get("is_correct", False):
                                    add_wrong_question(question.id, user_answer)
                                elif question.id and result.get("is_correct", False):
                                    mark_question_mastered(question.id)
                            else:
                                st.error(f"评判失败：{result['error']}")
                            st.rerun()

                else:
                    user_answer = st.text_area(
                        "请输入你的答案：",
                        height=200,
                        placeholder="在此输入你的答案..."
                    )
                    
                    col_exit, col_submit = st.columns([1, 3])
                    with col_exit:
                        if st.button("🏠 返回首页", use_container_width=True):
                            st.session_state.practice_state["started"] = False
                            st.rerun()
                    with col_submit:
                        if st.button("✅ 提交答案", type="primary", use_container_width=True) and user_answer:
                            with st.spinner("AI 正在评判..."):
                                result = grade_answer(
                                    question.type,
                                    question.content,
                                    question.answer,
                                    user_answer
                                )
                            
                            if "error" not in result:
                                result["user_answer"] = user_answer
                                st.session_state.practice_state["answered"] = True
                                st.session_state.practice_state["result"] = result
                                save_practice_record(question.id or 0, user_answer, result.get("is_correct", False))
                                if question.id and not result.get("is_correct", False):
                                    add_wrong_question(question.id, user_answer)
                                elif question.id and result.get("is_correct", False):
                                    mark_question_mastered(question.id)
                            else:
                                st.error(f"评判失败：{result['error']}")
                            st.rerun()
            
            else:
                result = st.session_state.practice_state["result"]
                
                if result:
                    if result.get("is_correct"):
                        st.success(f"✅ 回答正确！得分：{result.get('score', 100)} 分")
                    else:
                        st.error(f"❌ 回答错误。得分：{result.get('score', 0)} 分")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**你的答案：**")
                        st.info(result.get("user_answer", ""))
                    
                    with col2:
                        st.markdown("**标准答案：**")
                        st.success(question.answer)
                    
                    if result.get("feedback"):
                        with st.expander("📝 查看评语", expanded=True):
                            st.write(result.get("feedback", ""))
                            
                            if result.get("key_points_hit"):
                                st.markdown("**✅ 答对的要点：**")
                                for point in result["key_points_hit"]:
                                    st.markdown(f"- {point}")
                            
                            if result.get("key_points_missed"):
                                st.markdown("**❌ 遗漏的要点：**")
                                for point in result["key_points_missed"]:
                                    st.markdown(f"- {point}")
                    
                    if question.explanation:
                        with st.expander("📖 查看解析"):
                            st.write(question.explanation)
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🎲 下一题（随机）", type="primary", use_container_width=True):
                        import random
                        new_question = random.choice(all_questions)
                        st.session_state.practice_state["current_question"] = new_question
                        st.session_state.practice_state["answered"] = False
                        st.session_state.practice_state["result"] = None
                        st.rerun()
                
                with col2:
                    if st.button("➡️ 下一题（顺序）", use_container_width=True):
                        if "practice_index" not in st.session_state:
                            st.session_state.practice_index = 0
                        st.session_state.practice_index += 1
                        
                        if st.session_state.practice_index < len(all_questions):
                            new_question = all_questions[st.session_state.practice_index]
                            st.session_state.practice_state["current_question"] = new_question
                            st.session_state.practice_state["answered"] = False
                            st.session_state.practice_state["result"] = None
                        else:
                            st.session_state.practice_state["started"] = False
                            st.success("🎉 恭喜！已完成所有题目！")
                        st.rerun()
                
                with col3:
                    if st.button("🏠 返回首页", use_container_width=True):
                        st.session_state.practice_state["started"] = False
                        st.rerun()
