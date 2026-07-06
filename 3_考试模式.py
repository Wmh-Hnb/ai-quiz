import streamlit as st
import json
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import (
    get_all_questions,
    get_random_questions,
    ExamRecord,
    save_exam_record,
    get_exam_records,
    add_wrong_question,
    mark_question_mastered
)
from utils.gemini import grade_answer
from utils.ui import inject_custom_css

st.set_page_config(page_title="考试模式", page_icon="📋", layout="wide")
inject_custom_css()

st.title("📋 考试模式")
st.markdown("---")

if "exam_state" not in st.session_state:
    st.session_state.exam_state = {
        "started": False,
        "finished": False,
        "questions": [],
        "answers": {},
        "results": {},
        "start_time": None,
        "time_limit": 60,
        "current_index": 0
    }

all_questions = get_all_questions()

if not all_questions:
    st.warning("⚠️ 题库为空，请先导入题目！")
    if st.button("前往导入题库"):
        st.switch_page("pages/1_导入题库.py")

elif not st.session_state.exam_state["started"] and not st.session_state.exam_state["finished"]:
    st.markdown("### ⚙️ 考试配置")

    required_counts = {
        "名词解释": 5,
        "单选题": 8,
        "多选题": 4,
        "填空题": 8,
        "简答题": 4,
        "论述题": 2,
        "判断题": 8,
        "病例分析题": 1
    }
    total_required = sum(required_counts.values())

    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            time_limit = st.selectbox(
                "⏰ 考试时长",
                options=[15, 30, 45, 60, 90, 120],
                index=2,
                format_func=lambda x: f"{x} 分钟"
            )
            
            st.markdown("#### 📝 题型分布")
            dist_cols = st.columns(3)
            for i, (q_type, count) in enumerate(required_counts.items()):
                with dist_cols[i % 3]:
                    st.caption(f"**{q_type}**: {count}")
        
        with col2:
            st.markdown("#### 📊 概览")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("总题数", total_required)
            with m2:
                st.metric("及格分", "60")
            with m3:
                st.metric("题库量", len(all_questions))
            with m4:
                st.metric("预计用时", f"{time_limit}m")
            
            st.info("⚠️ 考试期间请勿关闭页面，系统将自动计时并在结束后评分。")

            if st.button("🚀 开始考试", type="primary", use_container_width=True):
                import random

                missing = []
                selected_by_type = []

                for q_type, count in required_counts.items():
                    candidates = [q for q in all_questions if q.type == q_type]
                    if len(candidates) < count:
                        missing.append(f"{q_type} {len(candidates)}/{count}")
                        continue
                    selected_by_type.extend(random.sample(candidates, count))

                if missing:
                    st.error("题库数量不足：" + "，".join(missing))
                else:
                    random.shuffle(selected_by_type)
                    st.session_state.exam_state["started"] = True
                    st.session_state.exam_state["questions"] = selected_by_type
                    st.session_state.exam_state["answers"] = {}
                    st.session_state.exam_state["results"] = {}
                    st.session_state.exam_state["start_time"] = time.time()
                    st.session_state.exam_state["time_limit"] = time_limit
                    st.session_state.exam_state["current_index"] = 0
                    st.rerun()


elif st.session_state.exam_state["started"] and not st.session_state.exam_state["finished"]:
    questions = st.session_state.exam_state["questions"]
    start_time = st.session_state.exam_state["start_time"]
    time_limit = st.session_state.exam_state["time_limit"]
    current_index = st.session_state.exam_state["current_index"]
    
    elapsed = time.time() - start_time
    remaining = max(0, time_limit * 60 - elapsed)
    
    if remaining <= 0:
        st.session_state.exam_state["finished"] = True
        st.rerun()
    
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    time_color = "🟢" if remaining > 300 else "🟡" if remaining > 60 else "🔴"
    answered_count = len(st.session_state.exam_state["answers"])
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.caption(f"题目进度: {current_index + 1}/{len(questions)}")
        st.progress((current_index + 1) / len(questions))
    with c2:
        st.caption("已答")
        st.markdown(f"**{answered_count}/{len(questions)}**")
    with c3:
        st.caption("剩余时间")
        st.markdown(f"**{time_color} {minutes:02d}:{seconds:02d}**")

    question = questions[current_index]
    
    st.markdown(f"""
    <div style="background:#f8fafc; padding:1rem; border-radius:8px; border:1px solid #e2e8f0; margin: 1rem 0;">
        <div style="color:#64748b; font-size:0.9rem; margin-bottom:0.5rem;">
            【{question.type}】 {question.category}
        </div>
        <div style="font-size:1.1rem; font-weight:600; color:#1e293b;">
            {question.content}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
        if question.type in ("选择题", "单选题"):
        options = question.get_options_list()
        option_labels = [opt.split(".")[0] if "." in opt else opt[0] for opt in options]

        current_answer = st.session_state.exam_state["answers"].get(current_index, "")
        default_index = option_labels.index(current_answer) if current_answer in option_labels else 0

        if options:
             st.info("\n".join([f"- {opt}" for opt in options]))

        answer = st.radio(
            "选择答案",
            option_labels,
            index=default_index if current_answer else None,
            horizontal=True,
            key=f"answer_{current_index}",
            label_visibility="collapsed"
        )
        st.session_state.exam_state["answers"][current_index] = answer

    elif question.type == "判断题":
        st.info("请判断：对 / 错")
        current_answer = st.session_state.exam_state["answers"].get(current_index, "")
        default_index = 0
        if current_answer == "错":
            default_index = 1

        answer = st.radio(
            "判断对错",
            ["对", "错"],
            index=default_index if current_answer else None,
            horizontal=True,
            key=f"answer_{current_index}",
            label_visibility="collapsed"
        )
        st.session_state.exam_state["answers"][current_index] = answer

    elif question.type == "多选题":
        options = question.get_options_list()
        if options:
            st.info("\n".join([f"- {opt}" for opt in options]))
        current_answer = st.session_state.exam_state["answers"].get(current_index, "")
        answer = st.text_input(
            "请输入答案（多个选项用逗号分隔，如 A,C）：",
            value=current_answer,
            key=f"answer_{current_index}"
        )
        st.session_state.exam_state["answers"][current_index] = answer

    else:
        current_answer = st.session_state.exam_state["answers"].get(current_index, "")
        answer = st.text_area(
            "请输入答案：",
            value=current_answer,
            height=150,
            key=f"answer_{current_index}"
        )
        st.session_state.exam_state["answers"][current_index] = answer
    
    col_nav1, col_nav2, col_submit = st.columns([1, 1, 2])
    
    with col_nav1:
        if current_index > 0:
            if st.button("⬅️ 上一题", use_container_width=True):
                st.session_state.exam_state["current_index"] -= 1
                st.rerun()
    
    with col_nav2:
        if current_index < len(questions) - 1:
            if st.button("➡️ 下一题", use_container_width=True):
                st.session_state.exam_state["current_index"] += 1
                st.rerun()
    
    with col_submit:
        if st.button("🏁 交卷", type="primary", use_container_width=True):
            unanswered = len(questions) - len(st.session_state.exam_state["answers"])
            if unanswered > 0:
                st.warning(f"还有 {unanswered} 道题未作答，确定要交卷吗？")
            st.session_state.exam_state["finished"] = True
            st.rerun()
            
    with st.expander("答题卡 (点击跳转)", expanded=False):
        cols = st.columns(10)
        for i, q in enumerate(questions):
            with cols[i % 10]:
                answered = i in st.session_state.exam_state["answers"]
                status = "🟢" if answered else "⚪"
                if st.button(f"{status} {i+1}", key=f"nav_{i}", use_container_width=True):
                    st.session_state.exam_state["current_index"] = i
                    st.rerun()

elif st.session_state.exam_state["finished"]:
    st.markdown("### 🎉 考试结束")
    st.markdown("---")
    
    questions = st.session_state.exam_state["questions"]
    answers = st.session_state.exam_state["answers"]
    start_time = st.session_state.exam_state["start_time"]
    
    end_time = time.time()
    duration = end_time - start_time
    
    if not st.session_state.exam_state.get("graded"):
        with st.spinner("AI 正在批改试卷..."):
            results = {}
            progress = st.progress(0)
            
            for i, question in enumerate(questions):
                user_answer = answers.get(i, "")
                
                if question.type == "选择题":
                    correct_answer = question.answer.strip().upper()
                    user_answer_upper = user_answer.strip().upper() if user_answer else ""
                    is_correct = user_answer_upper == correct_answer
                    
                    results[i] = {
                        "is_correct": is_correct,
                        "score": 100 if is_correct else 0,
                        "feedback": "正确！" if is_correct else f"错误，正确答案是 {correct_answer}",
                        "user_answer": user_answer
                    }
                    if question.id:
                        if is_correct:
                            mark_question_mastered(question.id)
                        else:
                            add_wrong_question(question.id, user_answer)
                else:
                    if user_answer:
                        result = grade_answer(
                            question.type,
                            question.content,
                            question.answer,
                            user_answer
                        )
                        if "error" not in result:
                            result["user_answer"] = user_answer
                            results[i] = result
                            if question.id and result.get("is_correct", False):
                                mark_question_mastered(question.id)
                            elif question.id and not result.get("is_correct", False):
                                add_wrong_question(question.id, user_answer)
                        else:
                            results[i] = {
                                "is_correct": False,
                                "score": 0,
                                "feedback": "评判失败",
                                "user_answer": user_answer
                            }
                            if question.id:
                                add_wrong_question(question.id, user_answer)
                    else:
                        results[i] = {
                            "is_correct": False,
                            "score": 0,
                            "feedback": "未作答",
                            "user_answer": ""
                        }
                
                progress.progress((i + 1) / len(questions))
            
            st.session_state.exam_state["results"] = results
            st.session_state.exam_state["graded"] = True
            
            correct_count = sum(1 for r in results.values() if r.get("is_correct"))
            total_score = sum(r.get("score", 0) for r in results.values()) / len(questions)
            
            record = ExamRecord(
                start_time=datetime.fromtimestamp(start_time).isoformat(),
                end_time=datetime.fromtimestamp(end_time).isoformat(),
                total_questions=len(questions),
                correct_count=correct_count,
                score=total_score,
                details=json.dumps({
                    "questions": [q.to_dict() for q in questions],
                    "answers": answers,
                    "results": results
                }, ensure_ascii=False)
            )
            save_exam_record(record)
    
    results = st.session_state.exam_state["results"]
    
    correct_count = sum(1 for r in results.values() if r.get("is_correct"))
    total_score = sum(r.get("score", 0) for r in results.values()) / len(questions) if questions else 0
    
    st.markdown("#### 🏁 考试结果")
    
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总分", f"{total_score:.1f}")
        with col2:
            st.metric("正确率", f"{correct_count}/{len(questions)}")
        with col3:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            st.metric("用时", f"{minutes}m {seconds}s")
        with col4:
            status = "🎉 通过" if total_score >= 60 else "😢 未通过"
            st.metric("状态", status)
    
    st.markdown("### 📝 答题详情")
    
    for i, question in enumerate(questions):
        result = results.get(i, {})
        is_correct = result.get("is_correct", False)
        
        status_icon = "✅" if is_correct else "❌"
        
        with st.expander(f"{status_icon} 第 {i+1} 题 ({result.get('score', 0)}分)"):
            st.markdown(f"**题目：** {question.content}")
            
            if question.type in ("选择题", "单选题"):
                    correct_answer = question.answer.strip().upper()
                    user_answer_upper = user_answer.strip().upper() if user_answer else ""
                    is_correct = user_answer_upper == correct_answer

                    results[i] = {
                        "is_correct": is_correct,
                        "score": 100 if is_correct else 0,
                        "feedback": "正确！" if is_correct else f"错误，正确答案是 {question.answer}",
                        "user_answer": user_answer
                    }
                    if question.id:
                        if is_correct:
                            mark_question_mastered(question.id)
                        else:
                            add_wrong_question(question.id, user_answer)
                elif question.type == "判断题":
                    user_clean = user_answer.strip()
                    correct_clean = question.answer.strip()
                    is_correct = (user_clean == "对" and (correct_clean in ("对", "正确", "T", "t", "true", "True"))) or (user_clean == "错" and (correct_clean in ("错", "错误", "F", "f", "false", "False")))

                    results[i] = {
                        "is_correct": is_correct,
                        "score": 100 if is_correct else 0,
                        "feedback": "正确！" if is_correct else f"错误，正确答案是 {question.answer}",
                        "user_answer": user_answer
                    }
                    if question.id:
                        if is_correct:
                            mark_question_mastered(question.id)
                        else:
                            add_wrong_question(question.id, user_answer)
                elif question.type == "多选题":
                    correct_set = set(question.answer.strip().upper().replace(" ", "").split(","))
                    user_set = set(user_answer.strip().upper().replace(" ", "").replace("，", ",").split(","))
                    is_correct = user_set == correct_set
                    score = max(0, 100 - len(user_set.symmetric_difference(correct_set)) * (100 // max(len(correct_set), 1)))

                    results[i] = {
                        "is_correct": is_correct,
                        "score": score,
                        "feedback": "完全正确！" if is_correct else f"错误，正确答案是 {question.answer}",
                        "user_answer": user_answer
                    }
                    if question.id:
                        if is_correct:
                            mark_question_mastered(question.id)
                        else:
                            add_wrong_question(question.id, user_answer)
                else:
                    st.error(user_ans if user_ans else "未作答")
            
            with c2:
                st.markdown("**标准答案**")
                st.info(question.answer)
            
            if result.get('feedback'):
                st.caption(f"**评语：** {result.get('feedback', '')}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 再考一次", type="primary", use_container_width=True):
            st.session_state.exam_state = {
                "started": False,
                "finished": False,
                "questions": [],
                "answers": {},
                "results": {},
                "start_time": None,
                "time_limit": 60,
                "current_index": 0
            }
            st.rerun()
    
    with col2:
        if st.button("🏠 返回首页", use_container_width=True):
            st.session_state.exam_state = {
                "started": False,
                "finished": False,
                "questions": [],
                "answers": {},
                "results": {},
                "start_time": None,
                "time_limit": 60,
                "current_index": 0
            }
            st.switch_page("app.py")
