"""
智能文字校对工具 - 参考爱校对设计
输入与预览合并，行内悬浮修改建议
"""
import streamlit as st
from dataclasses import dataclass
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from checker.typo import TypoChecker
from checker.punctuation import PunctuationChecker
from checker.grammar import GrammarChecker
from checker.context import ContextChecker
from scene.detector import SceneDetector

st.set_page_config(
    page_title="智能文字校对",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 自定义样式
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .main .block-container {padding-top: 0.5rem; max-width: 100%;}

    /* 顶部栏 */
    .top-bar {
        background: white;
        border-bottom: 1px solid #e8e8e8;
        padding: 12px 0;
        margin-bottom: 16px;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    /* 主编辑区 */
    .editor-container {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        min-height: 500px;
        position: relative;
    }

    /* 文本显示区 */
    .text-content {
        padding: 20px;
        line-height: 2.2;
        font-size: 16px;
        min-height: 450px;
        white-space: pre-wrap;
        word-break: break-all;
    }

    /* 错误标记 */
    .error-mark {
        background: linear-gradient(to bottom, transparent 60%, #ffcdd2 60%);
        color: #c62828;
        cursor: pointer;
        position: relative;
        padding: 0 2px;
        border-radius: 2px;
        transition: all 0.15s;
    }
    .error-mark:hover {
        background: #ffcdd2;
        box-shadow: 0 2px 8px rgba(198, 40, 40, 0.3);
    }
    .error-mark.type-标点 { background: linear-gradient(to bottom, transparent 60%, #ffe0b2 60%); color: #e65100; }
    .error-mark.type-标点:hover { background: #ffe0b2; }
    .error-mark.type-语法 { background: linear-gradient(to bottom, transparent 60%, #bbdefb 60%); color: #1565c0; }
    .error-mark.type-语法:hover { background: #bbdefb; }
    .error-mark.type-语义 { background: linear-gradient(to bottom, transparent 60%, #e1bee7 60%); color: #7b1fa2; }
    .error-mark.type-语义:hover { background: #e1bee7; }

    /* 悬浮卡片 */
    .float-card {
        position: absolute;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        padding: 12px 16px;
        min-width: 220px;
        z-index: 1000;
        display: none;
    }
    .error-mark:hover .float-card {
        display: block;
    }

    /* 右侧面板 */
    .side-panel {
        background: #fafafa;
        border-left: 1px solid #e0e0e0;
        height: 100%;
        overflow-y: auto;
    }

    /* 问题项 */
    .issue-item {
        background: white;
        border: 1px solid #e8e8e8;
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .issue-item:hover {
        border-color: #1a73e8;
        box-shadow: 0 2px 8px rgba(26, 115, 232, 0.15);
    }
    .issue-item.active {
        border-color: #1a73e8;
        background: #e8f0fe;
    }

    /* 标签 */
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 500;
    }

    /* 按钮 */
    .stButton button {
        border-radius: 6px;
    }

    /* 统计 */
    .stat-badge {
        background: #f5f5f5;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
    }

    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #999;
    }
</style>
""", unsafe_allow_html=True)


@dataclass
class Issue:
    position: int
    position_end: int
    error_text: str
    error_type: str
    suggestion: str
    confidence: float
    id: int = 0
    applied: bool = False
    ignored: bool = False


def get_issue_color(error_type: str) -> str:
    colors = {"错别字": "#e74c3c", "标点": "#f39c12", "语法": "#3498db", "语义": "#9b59b6"}
    return colors.get(error_type, "#7f8c8d")


def render_error_with_tooltip(issue: Issue, text: str) -> str:
    """渲染带悬浮卡片的错误文本"""
    error_text = text[issue.position:issue.position_end]
    color = get_issue_color(issue.error_type)

    return f'''
    <span class="error-mark type-{issue.error_type}" data-id="{issue.id}">
        {error_text}
        <div class="float-card">
            <div style="margin-bottom:8px;">
                <span class="tag" style="background:{color}20;color:{color};">{issue.error_type}</span>
                <span style="color:#999;font-size:12px;margin-left:6px;">置信度 {issue.confidence:.0%}</span>
            </div>
            <div style="font-size:15px;margin-bottom:10px;">
                <span style="color:{color};text-decoration:line-through;">{issue.error_text}</span>
                <span style="color:#999;margin:0 6px;">→</span>
                <span style="color:#27ae60;font-weight:600;">{issue.suggestion}</span>
            </div>
            <div style="display:flex;gap:8px;">
                <button onclick="applyFix({issue.id})" style="flex:1;background:#27ae60;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;">采纳修改</button>
                <button onclick="ignoreIssue({issue.id})" style="flex:1;background:#e0e0e0;color:#666;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;">忽略</button>
            </div>
        </div>
    </span>
    '''


def render_text_with_errors(text: str, issues: List[Issue]) -> str:
    """渲染带错误标记的文本"""
    if not issues:
        return text

    sorted_issues = sorted([i for i in issues if not i.ignored], key=lambda x: x.position)
    result = []
    last_end = 0

    for issue in sorted_issues:
        if issue.position > last_end:
            result.append(text[last_end:issue.position])
        result.append(render_error_with_tooltip(issue, text))
        last_end = issue.position_end

    if last_end < len(text):
        result.append(text[last_end:])

    return "".join(result)


def count_chinese(text: str) -> int:
    return sum(1 for c in text if '一' <= c <= '鿿')


def run_check(text: str) -> tuple:
    issues = []
    detector = SceneDetector()
    scene_type, style_type = detector.detect(text)

    for issue in TypoChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "错别字", issue.suggestion, issue.confidence))
    for issue in PunctuationChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "标点", issue.suggestion, issue.confidence))
    for issue in GrammarChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语法", issue.suggestion, issue.confidence))
    for issue in ContextChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语义", issue.suggestion, issue.confidence))

    issues.sort(key=lambda x: x.position)
    for i, issue in enumerate(issues):
        issue.id = i

    return issues, scene_type, style_type


def run_ai(text: str) -> str:
    try:
        import dashscope
        from dashscope import Generation
        api_key = st.secrets.get("DASHSCOPE_API_KEY", "")
        if not api_key:
            return "⚠️ 请配置 DASHSCOPE_API_KEY"
        dashscope.api_key = api_key
        r = Generation.call(model='qwen-turbo', prompt=f"润色优化：\n{text[:2000]}", max_tokens=3000)
        return r.output.text if r.status_code == 200 else f"失败: {r.message}"
    except Exception as e:
        return f"出错: {e}"


def main():
    # 初始化
    for k, v in [("text", ""), ("issues", []), ("scene_type", ""), ("style_type", ""), ("checked", False), ("ai_result", ""), ("selected_id", None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # 顶部栏
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        st.markdown("### 📝 智能文字校对")

    with col2:
        st.markdown(f'<div class="stat-badge">字数: {count_chinese(st.session_state.text)}/10000</div>', unsafe_allow_html=True)

    with col3:
        if st.button("🔍 开始校对", type="primary", use_container_width=True):
            if st.session_state.text.strip():
                st.session_state.issues, st.session_state.scene_type, st.session_state.style_type = run_check(st.session_state.text)
                st.session_state.checked = True
                st.rerun()

    with col4:
        if st.button("✓ 一键采纳全部", use_container_width=True):
            if st.session_state.issues:
                new_text = st.session_state.text
                for issue in sorted(st.session_state.issues, key=lambda x: -x.position):
                    if not issue.ignored:
                        new_text = new_text[:issue.position] + issue.suggestion + new_text[issue.position_end:]
                st.session_state.text = new_text
                st.session_state.issues = []
                st.rerun()

    with col5:
        if st.button("🗑️ 清空", use_container_width=True):
            st.session_state.text = ""
            st.session_state.issues = []
            st.session_state.checked = False
            st.rerun()

    # 主区域：左侧编辑+右侧结果
    col_left, col_right = st.columns([3, 1])

    with col_left:
        # 文本输入/显示区
        if not st.session_state.checked or not st.session_state.issues:
            # 显示输入框
            text_input = st.text_area(
                "输入文本",
                value=st.session_state.text,
                height=500,
                label_visibility="collapsed",
                placeholder="在此粘贴或输入需要校对的文本...\n\n支持检测：错别字、标点符号、语法问题、语义问题",
                key="main_input"
            )
            if text_input != st.session_state.text:
                st.session_state.text = text_input
                st.session_state.issues = []
                st.session_state.checked = False
        else:
            # 显示带标记的文本
            st.markdown(f"""
            <div class="editor-container">
                <div class="text-content">{render_text_with_errors(st.session_state.text, st.session_state.issues)}</div>
            </div>
            """, unsafe_allow_html=True)

            # 重新编辑按钮
            if st.button("✏️ 重新编辑", key="re_edit"):
                st.session_state.checked = False
                st.session_state.issues = []
                st.rerun()

    with col_right:
        st.markdown("**📋 检测结果**")

        if st.session_state.issues:
            # 统计
            type_counts = {}
            for issue in st.session_state.issues:
                if not issue.ignored:
                    type_counts[issue.error_type] = type_counts.get(issue.error_type, 0) + 1

            for t, c in type_counts.items():
                color = get_issue_color(t)
                st.markdown(f'<span class="tag" style="background:{color}20;color:{color};">{t}: {c}</span>', unsafe_allow_html=True)

            st.markdown("---")

            # 问题列表
            for issue in st.session_state.issues:
                if issue.ignored:
                    continue

                color = get_issue_color(issue.error_type)
                is_active = st.session_state.selected_id == issue.id

                with st.container():
                    st.markdown(f"""
                    <div class="issue-item {'active' if is_active else ''}">
                        <div style="display:flex;align-items:center;margin-bottom:4px;">
                            <span class="tag" style="background:{color}20;color:{color};">{issue.error_type}</span>
                            <span style="color:#999;font-size:12px;margin-left:auto;">第{issue.position}字</span>
                        </div>
                        <div style="font-size:14px;">
                            <span style="color:{color};text-decoration:line-through;">{issue.error_text}</span>
                            <span style="color:#27ae60;margin-left:4px;">→ {issue.suggestion}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✓ 采纳", key=f"adopt_{issue.id}", use_container_width=True):
                            new_text = st.session_state.text[:issue.position] + issue.suggestion + st.session_state.text[issue.position_end:]
                            st.session_state.text = new_text
                            issue.applied = True
                            st.session_state.issues = [i for i in st.session_state.issues if i.id != issue.id]
                            st.rerun()
                    with c2:
                        if st.button("✕ 忽略", key=f"ign_{issue.id}", use_container_width=True):
                            issue.ignored = True
                            st.rerun()

            # 导出
            st.markdown("---")
            if st.button("📥 导出报告", use_container_width=True):
                report = f"# 校对报告\n\n问题: {len(st.session_state.issues)}个\n\n"
                for i, issue in enumerate(st.session_state.issues, 1):
                    if not issue.ignored:
                        report += f"{i}. [{issue.error_type}] {issue.error_text} → {issue.suggestion}\n"
                report += f"\n## 原文\n\n{st.session_state.text}"
                st.download_button("下载", report, "校对报告.md", "text/markdown")

        else:
            st.markdown("""
            <div class="empty-state">
                <p>👈 输入文本后点击「开始校对」</p>
                <p style="font-size:12px;">支持检测错别字、标点、语法、语义问题</p>
            </div>
            """, unsafe_allow_html=True)

    # AI润色区
    st.markdown("---")
    with st.expander("✨ AI智能润色", expanded=False):
        if st.session_state.text:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("**原文**")
                st.text_area("", st.session_state.text[:400], height=100, disabled=True, key="orig_preview")
            with col2:
                st.markdown("**润色结果**")
                if st.session_state.ai_result:
                    st.markdown(f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:16px;border-radius:8px;">{st.session_state.ai_result}</div>', unsafe_allow_html=True)
                else:
                    if st.button("🚀 开始润色", type="primary"):
                        with st.spinner("AI润色中..."):
                            st.session_state.ai_result = run_ai(st.session_state.text)
                            st.rerun()

            if st.session_state.ai_result:
                if st.button("📋 使用润色结果替换原文"):
                    st.session_state.text = st.session_state.ai_result
                    st.session_state.ai_result = ""
                    st.session_state.issues = []
                    st.session_state.checked = False
                    st.success("✓ 已替换")
        else:
            st.info("请先输入文本")


if __name__ == "__main__":
    main()
