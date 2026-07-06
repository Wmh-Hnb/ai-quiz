import streamlit as st
import json
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import (
    get_all_questions,
    get_question_stats,
    delete_question,
    update_question,
    Question,
    get_exam_records,
    get_practice_stats,
    get_wrong_questions,
    mark_question_mastered,
    remove_from_wrong_questions,
    get_wrong_question_stats,
    add_wrong_question,
    clear_all_questions,
    clear_wrong_questions
)
from utils.gemini import summarize_wrong_questions, summarize_weak_points
from utils.ui import inject_custom_css

st.set_page_config(page_title="题库管理", page_icon="📚", layout="wide")
inject_custom_css()

st.title("📚 题库管理")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📋 题目列表", "📊 数据统计", "📜 考试记录", "❌ 错题集"])

with tab1:
    questions = get_all_questions()

    with st.expander("⚠️ 危险区域：清空题库", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning("此操作将永久删除所有题目、考试记录和错题集，不可恢复。")
        with col2:
            if st.button("🗑️ 确认清空所有数据", type="primary", use_container_width=True):
                clear_all_questions()
                st.success("数据已全部清空")
                st.rerun()

    if not questions:
        st.info("题库为空，请前往 [导入题库](/导入题库) 添加题目。")
    else:
        st.markdown(f"**共 {len(questions)} 道题目**")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            search_term = st.text_input("🔍 搜索", placeholder="题目内容 / 关键词", label_visibility="collapsed")
        
        with col2:
            type_filter = st.selectbox(
                "题型",
                ["全部"] + list(set(q.type for q in questions)),
                label_visibility="collapsed"
            )
        
        with col3:
            sort_by = st.selectbox("排序", ["最新", "最早", "难度↑", "难度↓"], label_visibility="collapsed")
        
        filtered = questions
        
        if search_term:
            filtered = [q for q in filtered if search_term.lower() in q.content.lower() 
                       or search_term.lower() in (q.keywords or "").lower()]
        
        if type_filter != "全部":
            filtered = [q for q in filtered if q.type == type_filter]
        
        if sort_by == "最早":
            filtered = filtered[::-1]
        elif sort_by == "难度↑":
            filtered = sorted(filtered, key=lambda x: x.difficulty)
        elif sort_by == "难度↓":
            filtered = sorted(filtered, key=lambda x: x.difficulty, reverse=True)
        
        st.markdown(f"共 **{len(filtered)}** 道题目")
        st.markdown("---")
        
        for i, q in enumerate(filtered):
            with st.expander(f"#{q.id} 【{q.type}】{q.content[:50]}..."):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**题目：** {q.content}")
                    
                    if q.type in ("选择题", "单选题", "多选题"):
                        options = q.get_options_list()
                        if options:
                            st.markdown("**选项：**")
                            for opt in options:
                                st.markdown(f"- {opt}")
                    
                    st.markdown(f"**答案：** {q.answer}")
                    st.markdown(f"**解析：** {q.explanation or '无'}")
                    st.markdown(f"**关键词：** {q.keywords or '无'}")
                
                with col2:
                    st.markdown(f"**难度：** {'⭐' * q.difficulty}")
                    st.markdown(f"**分类：** {q.category or '未分类'}")
                    st.markdown(f"**创建：** {q.created_at[:10] if q.created_at else '未知'}")
                    
                    if st.button("🗑️ 删除", key=f"del_{q.id}"):
                        if q.id and delete_question(q.id):
                            st.success("已删除")
                            st.rerun()

with tab2:
    stats = get_question_stats()
    practice_stats = get_practice_stats()
    
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("题目总数", stats['total'])
        with col2:
            st.metric("题型", len(stats['by_type']))
        with col3:
            st.metric("学科", len(stats['by_category']))
        with col4:
            accuracy = practice_stats.get('accuracy', 0) * 100
            st.metric("正确率", f"{accuracy:.1f}%")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption("题型分布")
        if stats['by_type']:
            type_df = pd.DataFrame(
                list(stats['by_type'].items()),
                columns=pd.Index(['题型', '数量'])
            )
            st.bar_chart(type_df.set_index('题型'))
        else:
            st.info("暂无数据")
    
    with col2:
        st.markdown("### 学科分布")
        if stats['by_category']:
            cat_df = pd.DataFrame(
                list(stats['by_category'].items()),
                columns=pd.Index(['学科', '数量'])
            )
            st.bar_chart(cat_df.set_index('学科'))
        else:
            st.info("暂无数据")
    
    st.markdown("---")
    st.markdown("### 难度分布")
    
    if stats['by_difficulty']:
        diff_labels = {1: "⭐ 简单", 2: "⭐⭐ 中等", 3: "⭐⭐⭐ 困难"}
        diff_data = {diff_labels.get(k, f"难度{k}"): v for k, v in stats['by_difficulty'].items()}
        
        diff_df = pd.DataFrame(
            list(diff_data.items()),
            columns=pd.Index(['难度', '数量'])
        )
        st.bar_chart(diff_df.set_index('难度'))
    else:
        st.info("暂无数据")

with tab3:
    records = get_exam_records()
    
    if not records:
        st.info("暂无考试记录")
    else:
        st.markdown(f"### 共 {len(records)} 次考试记录")
        
        for i, record in enumerate(records[:20]):
            passed = record.score >= 60
            status = "✅ 通过" if passed else "❌ 未通过"
            
            with st.expander(f"{status} | {record.start_time[:10] if record.start_time else '未知'} | 得分：{record.score:.1f}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("得分", f"{record.score:.1f}")
                with col2:
                    st.metric("正确数", f"{record.correct_count}/{record.total_questions}")
                with col3:
                    if record.start_time and record.end_time:
                        start = record.start_time
                        end = record.end_time
                        st.metric("开始时间", start[11:19] if len(start) > 19 else start)
                with col4:
                    accuracy = record.correct_count / record.total_questions * 100 if record.total_questions else 0
                    st.metric("正确率", f"{accuracy:.1f}%")
        
        st.markdown("---")
        
        if len(records) >= 3:
            st.markdown("### 成绩趋势")
            
            scores = [r.score for r in records[:10][::-1]]
            score_df = pd.DataFrame({
                '考试次数': range(1, len(scores) + 1),
                '得分': scores
            })
            st.line_chart(score_df.set_index('考试次数'))

with tab4:
    wrong_stats = get_wrong_question_stats()

    st.markdown("### ❌ 错题集概览")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("未掌握错题", wrong_stats.get('total_wrong', 0))
    with col2:
        st.metric("已掌握", wrong_stats.get('mastered', 0))
    with col3:
        st.metric("累计错题次数", wrong_stats.get('total_wrong_times', 0))

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("清空错题集会移除所有错题记录。")
    with col2:
        if st.button("一键清空错题集", use_container_width=True):
            clear_wrong_questions()
            st.success("错题集已清空")
            st.rerun()

    st.markdown("---")
    
    st.markdown("### 🤖 AI 智能总结")
    col_sum1, col_sum2 = st.columns(2)
    
    with col_sum1:
        if st.button("📝 生成错题总结", use_container_width=True):
            with st.spinner("正在生成错题总结..."):
                w_qs = get_wrong_questions(include_mastered=False)
                res = summarize_wrong_questions(w_qs)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.session_state["wrong_summary"] = res["summary"]
                    if "weak_summary" in st.session_state:
                        del st.session_state["weak_summary"]
    
    with col_sum2:
        if st.button("🧠 生成薄弱点分析", use_container_width=True):
            with st.spinner("正在生成薄弱点分析..."):
                w_qs = get_wrong_questions(include_mastered=True)
                res = summarize_weak_points(w_qs)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.session_state["weak_summary"] = res["summary"]
                    if "wrong_summary" in st.session_state:
                        del st.session_state["wrong_summary"]

    if "wrong_summary" in st.session_state:
        st.markdown("#### 📝 错题总结")
        st.info(st.session_state["wrong_summary"])
        if st.button("关闭", key="close_ws"):
            del st.session_state["wrong_summary"]
            st.rerun()

    if "weak_summary" in st.session_state:
        st.markdown("#### 🧠 薄弱点分析")
        st.info(st.session_state["weak_summary"])
        if st.button("关闭", key="close_wps"):
            del st.session_state["weak_summary"]
            st.rerun()

    st.markdown("---")

    show_mastered = st.checkbox("显示已掌握题目", value=False)
    wrong_questions = get_wrong_questions(include_mastered=show_mastered)

    if not wrong_questions:
        st.info("暂无错题记录")
    else:
        st.markdown(f"共 {len(wrong_questions)} 道错题")

        for item in wrong_questions:
            question = item["question"]
            status = "✅ 已掌握" if item.get("is_mastered") else "❌ 未掌握"

            with st.expander(f"{status} | 错题 {item['wrong_count']} 次 | {question.type} - {question.content[:30]}..."):
                st.markdown(f"**题目：** {question.content}")

                if question.type in ("选择题", "单选题", "多选题"):
                    options = question.get_options_list()
                    if options:
                        st.markdown("**选项：**")
                        for opt in options:
                            st.markdown(f"- {opt}")

                st.markdown(f"**标准答案：** {question.answer}")
                st.markdown(f"**你的上次答案：** {item.get('user_answer', '') or '未记录'}")
                st.markdown(f"**解析：** {question.explanation or '无'}")
                st.markdown(f"**分类：** {question.category or '未分类'}")

                col1, col2 = st.columns(2)
                with col1:
                    if item.get("is_mastered"):
                        if st.button("↩️ 恢复未掌握", key=f"restore_{question.id}"):
                            add_wrong_question(question.id, item.get("user_answer", ""))
                            st.rerun()
                    else:
                        if st.button("✅ 标记掌握", key=f"master_{question.id}"):
                            mark_question_mastered(question.id)
                            st.rerun()

                with col2:
                    if st.button("🗑️ 移除", key=f"remove_{question.id}"):
                        remove_from_wrong_questions(question.id)
                        st.rerun()
