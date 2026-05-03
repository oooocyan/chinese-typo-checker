"""
智能文字校对工具 - AI增强版
整合本地词典检测 + AI深度检测
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

    .top-bar {
        background: white;
        border-bottom: 1px solid #e8e8e8;
        padding: 12px 0;
        margin-bottom: 12px;
    }

    .editor-box {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        min-height: 480px;
    }

    .text-content {
        padding: 16px;
        line-height: 2.2;
        font-size: 15px;
        min-height: 440px;
        white-space: pre-wrap;
        word-break: break-all;
    }

    /* 错误标记样式 */
    .err {
        background: linear-gradient(to bottom, transparent 60%, #ffcdd2 60%);
        color: #c62828;
        cursor: pointer;
        padding: 0 2px;
        border-radius: 2px;
        position: relative;
    }
    .err:hover {
        background: #ffcdd2;
    }
    .err.标点 { background: linear-gradient(to bottom, transparent 60%, #ffe0b2 60%); color: #e65100; }
    .err.标点:hover { background: #ffe0b2; }
    .err.语法 { background: linear-gradient(to bottom, transparent 60%, #bbdefb 60%); color: #1565c0; }
    .err.语法:hover { background: #bbdefb; }
    .err.语义 { background: linear-gradient(to bottom, transparent 60%, #e1bee7 60%); color: #7b1fa2; }
    .err.语义:hover { background: #e1bee7; }

    /* 悬浮卡片 */
    .tip-card {
        position: absolute;
        bottom: 100%;
        left: 0;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        padding: 12px;
        min-width: 200px;
        z-index: 100;
        display: none;
    }
    .err:hover .tip-card { display: block; }

    /* 问题列表 */
    .issue-card {
        background: white;
        border: 1px solid #e8e8e8;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 6px;
        border-left: 3px solid #e74c3c;
    }
    .issue-card:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
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

    /* AI标识 */
    .ai-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        margin-left: 4px;
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
    source: str = "本地"  # 本地 或 AI
    id: int = 0
    applied: bool = False
    ignored: bool = False


def get_color(t: str) -> str:
    return {"错别字": "#e74c3c", "标点": "#f39c12", "语法": "#3498db", "语义": "#9b59b6"}.get(t, "#7f8c8d")


def render_error(issue: Issue) -> str:
    """渲染错误标记"""
    c = get_color(issue.error_type)
    ai_badge = '<span class="ai-badge">AI</span>' if issue.source == "AI" else ""

    return f'''
    <span class="err {issue.error_type}">
        {issue.error_text}
        <div class="tip-card">
            <div style="margin-bottom:6px;">
                <span class="tag" style="background:{c}20;color:{c};">{issue.error_type}</span>{ai_badge}
            </div>
            <div style="font-size:14px;margin-bottom:8px;">
                <span style="color:{c};text-decoration:line-through;">{issue.error_text}</span>
                <span style="margin:0 4px;color:#999;">→</span>
                <span style="color:#27ae60;font-weight:600;">{issue.suggestion}</span>
            </div>
            <div style="font-size:12px;color:#999;">置信度: {issue.confidence:.0%}</div>
        </div>
    </span>
    '''


def render_text(text: str, issues: List[Issue]) -> str:
    """渲染带标记的文本"""
    if not issues:
        return text

    sorted_issues = sorted([i for i in issues if not i.ignored], key=lambda x: x.position)
    result = []
    last = 0

    for issue in sorted_issues:
        if issue.position > last:
            result.append(text[last:issue.position])
        result.append(render_error(issue))
        last = issue.position_end

    if last < len(text):
        result.append(text[last:])

    return "".join(result)


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


def run_ai_check(text: str) -> List[Issue]:
    """AI检测"""
    api_key = st.secrets.get("NVIDIA_API_KEY", "")
    base_url = st.secrets.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    if not api_key:
        return []

    detector = AIDetector(api_key, base_url)
    if not detector.is_available():
        return []

    issues = []
    for issue in detector.detect_batch(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, issue.error_type, issue.suggestion, issue.confidence, "AI"))

    return issues


def merge_issues(local: List[Issue], ai: List[Issue]) -> List[Issue]:
    """合并检测结果，去重"""
    # 用位置和错误文本作为key去重
    seen = set()
    merged = []

    for issue in local + ai:
        key = (issue.position, issue.error_text)
        if key not in seen:
            seen.add(key)
            merged.append(issue)

    # 按位置排序
    merged.sort(key=lambda x: x.position)

    # 分配ID
    for i, issue in enumerate(merged):
        issue.id = i

    return merged


def run_ai_polish(text: str) -> str:
    """AI润色"""
    try:
        from openai import OpenAI
        api_key = st.secrets.get("NVIDIA_API_KEY", "")
        base_url = st.secrets.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        if not api_key:
            return "⚠️ 请配置 NVIDIA_API_KEY"
        client = OpenAI(base_url=base_url, api_key=api_key)
        r = client.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=[
                {"role": "system", "content": "你是一位专业的文字编辑，擅长润色优化中文文本。"},
                {"role": "user", "content": f"请润色优化以下文本，直接输出润色后的结果：\n\n{text[:2500]}"}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"出错: {e}"


def main():
    # 初始化状态
    for k, v in [("text", ""), ("issues", []), ("checked", False), ("ai_result", ""), ("use_ai", True)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # 顶部工具栏
    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])

    with col1:
        st.markdown("### 📝 智能文字校对")

    with col2:
        st.markdown(f'<div class="stat-box">字数: {count_chinese(st.session_state.text)}/10000</div>', unsafe_allow_html=True)

    with col3:
        # AI检测开关
        st.session_state.use_ai = st.checkbox("🤖 AI检测", value=st.session_state.use_ai)

    with col4:
        if st.button("🔍 开始校对", type="primary", use_container_width=True):
            if st.session_state.text.strip() and count_chinese(st.session_state.text) <= 10000:
                # 本地检测
                local_issues = run_local_check(st.session_state.text)

                # AI检测
                ai_issues = []
                if st.session_state.use_ai:
                    with st.spinner("AI检测中..."):
                        ai_issues = run_ai_check(st.session_state.text)

                # 合并结果
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
            st.rerun()

    # 主区域
    col_left, col_right = st.columns([3, 1])

    with col_left:
        # 文本区
        if not st.session_state.checked or not st.session_state.issues:
            text_input = st.text_area(
                "输入文本",
                value=st.session_state.text,
                height=480,
                label_visibility="collapsed",
                placeholder="在此粘贴或输入需要校对的文本...\n\n支持：错别字、标点符号、语法问题、语义问题\n\n💡 开启AI检测可获得更准确的检测结果",
                key="main_input"
            )
            if text_input != st.session_state.text:
                st.session_state.text = text_input
                st.session_state.issues = []
                st.session_state.checked = False
        else:
            # 显示检测结果
            st.markdown(f"""
            <div class="editor-box">
                <div class="text-content">{render_text(st.session_state.text, st.session_state.issues)}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✏️ 重新编辑"):
                st.session_state.checked = False
                st.session_state.issues = []
                st.rerun()

    with col_right:
        st.markdown("**📋 检测结果**")

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
                st.markdown(f'<div style="font-size:12px;color:#666;margin-bottom:8px;">🤖 AI检测发现 {ai_count} 个问题</div>', unsafe_allow_html=True)

            st.markdown("---")

            # 问题列表
            for issue in st.session_state.issues:
                if issue.ignored:
                    continue

                color = get_color(issue.error_type)
                ai_badge = '<span class="ai-badge">AI</span>' if issue.source == "AI" else ""

                st.markdown(f"""
                <div class="issue-card" style="border-left-color:{color};">
                    <div style="display:flex;align-items:center;margin-bottom:4px;">
                        <span class="tag" style="background:{color}20;color:{color};">{issue.error_type}</span>{ai_badge}
                        <span style="color:#999;font-size:11px;margin-left:auto;">第{issue.position}字</span>
                    </div>
                    <div style="font-size:13px;">
                        <span style="color:{color};text-decoration:line-through;">{issue.error_text}</span>
                        <span style="color:#27ae60;margin-left:4px;">→ {issue.suggestion}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✓ 采纳", key=f"a{issue.id}", use_container_width=True):
                        new_text = st.session_state.text[:issue.position] + issue.suggestion + st.session_state.text[issue.position_end:]
                        st.session_state.text = new_text
                        st.session_state.issues = [i for i in st.session_state.issues if i.id != issue.id]
                        st.rerun()
                with c2:
                    if st.button("✕ 忽略", key=f"i{issue.id}", use_container_width=True):
                        issue.ignored = True
                        st.rerun()

            # 导出
            st.markdown("---")
            if st.button("📥 导出报告", use_container_width=True):
                report = f"# 校对报告\n\n问题: {len([i for i in st.session_state.issues if not i.ignored])}个\n\n"
                for i, issue in enumerate(st.session_state.issues, 1):
                    if not issue.ignored:
                        report += f"{i}. [{issue.error_type}]({issue.source}) {issue.error_text} → {issue.suggestion}\n"
                report += f"\n## 原文\n\n{st.session_state.text}"
                st.download_button("下载", report, "校对报告.md", "text/markdown")

        else:
            st.markdown("""
            <div style="text-align:center;padding:40px 10px;color:#999;">
                <p>👈 输入文本后点击「开始校对」</p>
                <p style="font-size:12px;">开启AI检测可获得更准确结果</p>
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
