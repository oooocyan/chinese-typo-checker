"""
智能文字校对工具 - AI增强版
参考爱校对设计，优化交互体验
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
from ai.detector import AIDetector

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

    .editor-box {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        min-height: 450px;
        padding: 16px;
        line-height: 2.2;
        font-size: 15px;
        white-space: pre-wrap;
        word-break: break-all;
    }

    .err {
        background: linear-gradient(to bottom, transparent 60%, #ffcdd2 60%);
        color: #c62828;
        padding: 1px 3px;
        border-radius: 3px;
        cursor: pointer;
    }
    .err:hover { background: #ffcdd2; }
    .err.标点 { background: linear-gradient(to bottom, transparent 60%, #ffe0b2 60%); color: #e65100; }
    .err.标点:hover { background: #ffe0b2; }
    .err.语法 { background: linear-gradient(to bottom, transparent 60%, #bbdefb 60%); color: #1565c0; }
    .err.语法:hover { background: #bbdefb; }
    .err.语义 { background: linear-gradient(to bottom, transparent 60%, #e1bee7 60%); color: #7b1fa2; }
    .err.语义:hover { background: #e1bee7; }

    .err {
        position: relative;
        cursor: pointer;
    }
    .err-tip {
        display: none;
        position: absolute;
        bottom: calc(100% + 8px);
        left: 50%;
        transform: translateX(-50%);
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.15);
        white-space: nowrap;
        z-index: 9999;
        font-size: 13px;
        line-height: 1.6;
        pointer-events: auto;
    }
    .err-tip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: #fff;
    }
    .err:hover .err-tip {
        display: block;
    }
    .tip-type {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .tip-orig {
        color: #c62828;
        text-decoration: line-through;
        font-weight: 500;
    }
    .tip-sugg {
        color: #27ae60;
        font-weight: 600;
    }
    .tip-conf {
        color: #999;
        font-size: 11px;
        margin-top: 4px;
    }
    .tip-actions {
        display: flex;
        gap: 8px;
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #eee;
    }
    .tip-btn {
        flex: 1;
        text-align: center;
        padding: 5px 14px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: 500;
        text-decoration: none;
        cursor: pointer;
        transition: all 0.15s;
    }
    .tip-btn.adopt {
        background: #27ae60;
        color: #fff;
    }
    .tip-btn.adopt:hover {
        background: #219a52;
        color: #fff;
        text-decoration: none;
    }
    .tip-btn.ignore {
        background: #f5f5f5;
        color: #999;
    }
    .tip-btn.ignore:hover {
        background: #eee;
        color: #666;
        text-decoration: none;
    }

    .card-btn-row {
        display: flex;
        gap: 8px;
        margin-top: 8px;
    }
    .tip-btn.card-btn {
        padding: 3px 10px;
        font-size: 10px;
    }

    .issue-item {
        padding: 10px;
    }
    .issue-item .issue-header {
        display: flex;
        align-items: center;
        margin-bottom: 4px;
    }
    .issue-item .issue-body {
        font-size: 14px;
        margin-bottom: 4px;
    }

    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 500;
    }

    .stat-box {
        background: #f5f5f5;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
    }

    .ai-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1px 5px;
        border-radius: 4px;
        font-size: 10px;
        margin-left: 4px;
    }

    .btn-row {
        display: flex;
        gap: 6px;
        margin-top: 8px;
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
    source: str = "本地"
    id: int = 0
    applied: bool = False
    ignored: bool = False


def get_color(t: str) -> str:
    return {"错别字": "#e74c3c", "标点": "#f39c12", "语法": "#3498db", "语义": "#9b59b6"}.get(t, "#7f8c8d")


def count_chinese(text: str) -> int:
    return sum(1 for c in text if '一' <= c <= '鿿')


def run_local_check(text: str) -> List[Issue]:
    """本地规则检测"""
    issues = []
    for issue in TypoChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "错别字", issue.suggestion, issue.confidence, "本地"))
    for issue in PunctuationChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "标点", issue.suggestion, issue.confidence, "本地"))
    for issue in GrammarChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语法", issue.suggestion, issue.confidence, "本地"))
    for issue in ContextChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语义", issue.suggestion, issue.confidence, "本地"))
    return issues


def run_ai_check(text: str) -> tuple:
    """AI检测"""
    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    base_url = st.secrets.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    if not api_key:
        return [], "未配置 DEEPSEEK_API_KEY"
    detector = AIDetector(api_key, base_url)
    if not detector.is_available():
        return [], detector.get_error() or "AI初始化失败"
    issues, error = detector.detect_batch(text)
    if error:
        return [], error
    result = [Issue(i.position, i.position_end, i.error_text, i.error_type, i.suggestion, i.confidence, "AI") for i in issues]
    return result, ""


def merge_issues(local: List[Issue], ai: List[Issue]) -> List[Issue]:
    seen = set()
    merged = []
    for issue in local + ai:
        key = (issue.position, issue.error_text)
        if key not in seen:
            seen.add(key)
            merged.append(issue)
    merged.sort(key=lambda x: x.position)
    for i, issue in enumerate(merged):
        issue.id = i
    return merged


def run_ai_polish(text: str) -> str:
    try:
        from openai import OpenAI
        api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
        base_url = st.secrets.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        if not api_key:
            return "⚠️ 请配置 DEEPSEEK_API_KEY"
        client = OpenAI(base_url=base_url, api_key=api_key)
        r = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是专业文字编辑。"},
                {"role": "user", "content": f"润色优化：\n{text[:2500]}"}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"出错: {e}"


def main():
    # 初始化
    for k, v in [("text", ""), ("issues", []), ("checked", False), ("ai_result", ""), ("use_ai", True), ("ai_error", ""), ("selected_id", None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # 处理悬浮框操作（通过URL参数）
    params = st.query_params
    if "adopt" in params and st.session_state.issues:
        try:
            issue_id = int(params["adopt"])
            for issue in st.session_state.issues:
                if issue.id == issue_id:
                    st.session_state.text = st.session_state.text[:issue.position] + issue.suggestion + st.session_state.text[issue.position_end:]
                    st.session_state.issues = [i for i in st.session_state.issues if i.id != issue_id]
                    break
        except (ValueError, IndexError):
            pass
        st.query_params.clear()
        st.rerun()
    if "ignore" in params and st.session_state.issues:
        try:
            issue_id = int(params["ignore"])
            for issue in st.session_state.issues:
                if issue.id == issue_id:
                    issue.ignored = True
                    break
        except (ValueError, IndexError):
            pass
        st.query_params.clear()
        st.rerun()

    # 顶部工具栏
    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])

    with col1:
        st.markdown("### 📝 智能文字校对")

    with col2:
        st.markdown(f'<div class="stat-box">字数: {count_chinese(st.session_state.text)}/10000</div>', unsafe_allow_html=True)

    with col3:
        st.session_state.use_ai = st.checkbox("🤖 AI检测", value=st.session_state.use_ai)

    with col4:
        if st.button("🔍 开始校对", type="primary", use_container_width=True):
            if st.session_state.text.strip() and count_chinese(st.session_state.text) <= 10000:
                local_issues = run_local_check(st.session_state.text)
                ai_issues = []
                if st.session_state.use_ai:
                    with st.spinner("AI检测中..."):
                        ai_issues, ai_error = run_ai_check(st.session_state.text)
                        st.session_state.ai_error = ai_error if ai_error else ""
                st.session_state.issues = merge_issues(local_issues, ai_issues)
                st.session_state.checked = True
                st.rerun()

    with col5:
        if st.button("✓ 一键采纳全部", use_container_width=True):
            if st.session_state.issues:
                new_text = st.session_state.text
                for issue in sorted(st.session_state.issues, key=lambda x: -x.position):
                    if not issue.ignored:
                        new_text = new_text[:issue.position] + issue.suggestion + new_text[issue.position_end:]
                st.session_state.text = new_text
                st.session_state.issues = []
                st.rerun()

    with col6:
        if st.button("🗑️ 清空", use_container_width=True):
            st.session_state.text = ""
            st.session_state.issues = []
            st.session_state.checked = False
            st.session_state.ai_error = ""
            st.rerun()

    # 主区域
    col_left, col_right = st.columns([3, 1])

    with col_left:
        # 文本区
        if not st.session_state.checked or not st.session_state.issues:
            text_input = st.text_area(
                "输入文本",
                value=st.session_state.text,
                height=450,
                label_visibility="collapsed",
                placeholder="在此粘贴或输入需要校对的文本...\n\n支持：错别字、标点符号、语法问题、语义问题\n\n💡 开启AI检测可获得更准确的检测结果",
                key="main_input"
            )
            if text_input != st.session_state.text:
                st.session_state.text = text_input
                st.session_state.issues = []
                st.session_state.checked = False
        else:
            # 显示检测结果 - 使用高亮文本
            sorted_issues = sorted([i for i in st.session_state.issues if not i.ignored], key=lambda x: x.position)

            # 构建高亮文本（带锚点和悬浮提示）
            html_parts = []
            last_end = 0
            for issue in sorted_issues:
                if issue.position > last_end:
                    html_parts.append(st.session_state.text[last_end:issue.position])
                color = get_color(issue.error_type)
                type_class = issue.error_type
                html_parts.append(
                    f'<span class="err {type_class}" style="border-bottom:2px solid {color};" id="err-{issue.id}">'
                    f'{issue.error_text}'
                    f'<span class="err-tip">'
                    f'<span class="tip-type" style="background:{color}20;color:{color};">{issue.error_type}</span><br>'
                    f'<span class="tip-orig">{issue.error_text}</span> → <span class="tip-sugg">{issue.suggestion}</span><br>'
                    f'<span class="tip-conf">置信度: {issue.confidence:.0%}</span>'
                    f'<div class="tip-actions">'
                    f'<a class="tip-btn adopt" href="?adopt={issue.id}">采纳</a>'
                    f'<a class="tip-btn ignore" href="?ignore={issue.id}">忽略</a>'
                    f'</div>'
                    f'</span></span>'
                )
                last_end = issue.position_end
            if last_end < len(st.session_state.text):
                html_parts.append(st.session_state.text[last_end:])

            highlighted_text = "".join(html_parts)
            st.markdown(f'<div class="editor-box">{highlighted_text}</div>', unsafe_allow_html=True)

            if st.button("✏️ 重新编辑"):
                st.session_state.checked = False
                st.session_state.issues = []
                st.rerun()

    with col_right:
        st.markdown("**📋 检测结果**")

        # 显示AI错误
        if st.session_state.get("ai_error"):
            st.error(f"🤖 {st.session_state.ai_error}")

        if st.session_state.issues:
            # 统计
            type_counts = {}
            ai_count = 0
            for issue in st.session_state.issues:
                if not issue.ignored:
                    type_counts[issue.error_type] = type_counts.get(issue.error_type, 0) + 1
                    if issue.source == "AI":
                        ai_count += 1

            stats = " ".join([f'<span class="tag" style="background:{get_color(t)}20;color:{get_color(t)};">{t}:{c}</span>' for t, c in type_counts.items()])
            st.markdown(f'<div style="margin-bottom:8px;">{stats}</div>', unsafe_allow_html=True)

            if ai_count > 0:
                st.markdown(f'<div style="font-size:12px;color:#666;margin-bottom:8px;">🤖 AI发现 {ai_count} 个</div>', unsafe_allow_html=True)

            st.markdown("---")

            # 问题列表 - 卡片内操作
            for issue in st.session_state.issues:
                if issue.ignored:
                    continue

                color = get_color(issue.error_type)
                ai_badge = '<span class="ai-badge">AI</span>' if issue.source == "AI" else ""

                with st.container(border=True):
                    # 卡片信息（点击定位）+ 操作按钮（绿色采纳/灰色忽略）
                    st.markdown(f"""
                    <a href="#err-{issue.id}" style="text-decoration:none;color:inherit;">
                    <div class="issue-item" style="border-left:3px solid {color};">
                        <div class="issue-header">
                            <span class="tag" style="background:{color}20;color:{color};">{issue.error_type}</span>{ai_badge}
                            <span style="color:#999;font-size:11px;margin-left:auto;">第{issue.position}字</span>
                        </div>
                        <div class="issue-body">
                            <span style="color:{color};text-decoration:line-through;">{issue.error_text}</span>
                            <span style="color:#27ae60;margin-left:4px;font-weight:600;">→ {issue.suggestion}</span>
                        </div>
                        <div style="margin-top:4px;">
                            <span style="color:#999;font-size:10px;">置信度 {issue.confidence:.0%}</span>
                        </div>
                    </div>
                    </a>
                    <div style="display:flex;justify-content:flex-end;gap:6px;margin-top:6px;">
                        <a class="tip-btn adopt card-btn" href="?adopt={issue.id}">采纳</a>
                        <a class="tip-btn ignore card-btn" href="?ignore={issue.id}">忽略</a>
                    </div>
                    """, unsafe_allow_html=True)

            # 导出
            st.markdown("---")
            if st.button("📥 导出报告", use_container_width=True):
                report = f"# 校对报告\n\n问题: {len([i for i in st.session_state.issues if not i.ignored])}个\n\n"
                for i, issue in enumerate(st.session_state.issues, 1):
                    if not issue.ignored:
                        report += f"{i}. [{issue.error_type}] {issue.error_text} → {issue.suggestion}\n"
                report += f"\n## 原文\n\n{st.session_state.text}"
                st.download_button("下载", report, "校对报告.md", "text/markdown")

        else:
            st.markdown("""
            <div style="text-align:center;padding:40px 10px;color:#999;">
                <p>👈 输入文本后点击「开始校对」</p>
            </div>
            """, unsafe_allow_html=True)

    # AI润色
    st.markdown("---")
    with st.expander("✨ AI智能润色", expanded=False):
        if st.session_state.text:
            if st.session_state.ai_result:
                st.markdown("**润色结果：**")
                st.markdown(f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:16px;border-radius:8px;white-space:pre-wrap;">{st.session_state.ai_result}</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📋 使用此结果"):
                        st.session_state.text = st.session_state.ai_result
                        st.session_state.ai_result = ""
                        st.session_state.issues = []
                        st.session_state.checked = False
                        st.success("✓ 已替换")
                with c2:
                    if st.button("🔄 重新润色"):
                        st.session_state.ai_result = ""
                        st.rerun()
            else:
                if st.button("🚀 开始AI润色", type="primary"):
                    with st.spinner("AI润色中..."):
                        st.session_state.ai_result = run_ai_polish(st.session_state.text)
                        st.rerun()
        else:
            st.info("请先输入文本")


if __name__ == "__main__":
    main()
