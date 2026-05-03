"""
中文错别字检查工具 - Streamlit 主入口
"""
import streamlit as st
from dataclasses import dataclass
from typing import List, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from checker.typo import TypoChecker
from checker.punctuation import PunctuationChecker
from checker.grammar import GrammarChecker
from checker.context import ContextChecker
from scene.detector import SceneDetector

# 配置页面
st.set_page_config(
    page_title="中文错别字检查工具",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-container {
        max-width: 100%;
        padding: 1rem;
    }
    .issue-card {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    .issue-card:hover {
        background-color: #f5f5f5;
    }
    .issue-selected {
        border: 2px solid #4B8BFF !important;
        background-color: #f0f7ff !important;
    }
    .stat-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        background-color: #e8e8e8;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@dataclass
class Issue:
    """问题数据类"""
    position: int           # 位置（第几个字）
    position_end: int       # 结束位置
    error_text: str         # 错误文本
    error_type: str         # 错误类型：错别字/标点/语法/语义/AI建议
    suggestion: str         # 修改建议
    confidence: float       # 置信度 0-1
    applied: bool = False   # 是否已应用
    ignored: bool = False   # 是否已忽略


def get_issue_color(error_type: str) -> str:
    """获取问题类型对应的颜色"""
    colors = {
        "错别字": "#FF4B4B",
        "标点": "#FFA500",
        "语法": "#4B8BFF",
        "语义": "#9B59B6",
        "AI建议": "#2ECC71",
    }
    return colors.get(error_type, "#808080")


def highlight_text(text: str, issues: List[Issue], selected_idx: Optional[int] = None) -> str:
    """高亮显示文本中的错误"""
    if not issues:
        return text

    # 按位置排序
    sorted_issues = sorted([i for i in issues if not i.ignored], key=lambda x: x.position)

    result = []
    last_end = 0

    for idx, issue in enumerate(sorted_issues):
        # 添加正常文本
        if issue.position > last_end:
            result.append(text[last_end:issue.position])

        # 添加高亮文本
        color = get_issue_color(issue.error_type)
        is_selected = (selected_idx is not None and idx == selected_idx)

        if is_selected:
            result.append(f'<mark style="background-color: {color}; color: white; padding: 2px 4px; border-radius: 3px;">▶{text[issue.position:issue.position_end]}◀</mark>')
        else:
            result.append(f'<span style="background-color: {color}40; color: {color}; padding: 1px 2px; border-radius: 2px; border-bottom: 2px solid {color};">{text[issue.position:issue.position_end]}</span>')

        last_end = issue.position_end

    # 添加剩余文本
    if last_end < len(text):
        result.append(text[last_end:])

    return "".join(result)


def count_chinese_chars(text: str) -> int:
    """统计中文字符数"""
    count = 0
    for char in text:
        if '一' <= char <= '鿿':
            count += 1
    return count


def run_check(text: str) -> tuple:
    """
    运行完整的检测流程

    Returns:
        (issues, scene_type, style_type)
    """
    issues = []

    # 1. 场景识别
    detector = SceneDetector()
    scene_type, style_type = detector.detect(text)

    # 2. 错别字检测
    typo_checker = TypoChecker()
    typo_issues = typo_checker.check(text)
    for issue in typo_issues:
        issues.append(Issue(
            position=issue.position,
            position_end=issue.position_end,
            error_text=issue.error_text,
            error_type="错别字",
            suggestion=issue.suggestion,
            confidence=issue.confidence
        ))

    # 3. 标点检查
    punct_checker = PunctuationChecker()
    punct_issues = punct_checker.check(text)
    for issue in punct_issues:
        issues.append(Issue(
            position=issue.position,
            position_end=issue.position_end,
            error_text=issue.error_text,
            error_type="标点",
            suggestion=issue.suggestion,
            confidence=issue.confidence
        ))

    # 4. 语法检查
    grammar_checker = GrammarChecker()
    grammar_issues = grammar_checker.check(text)
    for issue in grammar_issues:
        issues.append(Issue(
            position=issue.position,
            position_end=issue.position_end,
            error_text=issue.error_text,
            error_type="语法",
            suggestion=issue.suggestion,
            confidence=issue.confidence
        ))

    # 5. 语义检查（如果是书面语风格）
    if style_type == "书面化":
        context_checker = ContextChecker()
        context_issues = context_checker.check(text)
        for issue in context_issues:
            issues.append(Issue(
                position=issue.position,
                position_end=issue.position_end,
                error_text=issue.error_text,
                error_type="语义",
                suggestion=issue.suggestion,
                confidence=issue.confidence
            ))

    # 按位置排序
    issues.sort(key=lambda x: x.position)

    return issues, scene_type, style_type


def main():
    """主函数"""
    st.title("📝 中文错别字检查工具")

    # 初始化 session state
    if "text" not in st.session_state:
        st.session_state.text = ""
    if "issues" not in st.session_state:
        st.session_state.issues = []
    if "scene_type" not in st.session_state:
        st.session_state.scene_type = "未识别"
    if "style_type" not in st.session_state:
        st.session_state.style_type = "未识别"
    if "selected_issue_idx" not in st.session_state:
        st.session_state.selected_issue_idx = None
    if "checking" not in st.session_state:
        st.session_state.checking = False

    # 顶部工具栏
    col_stats, col_btns = st.columns([1, 2])

    with col_stats:
        char_count = count_chinese_chars(st.session_state.text)
        st.markdown(f"**字数: {char_count}/10000**")

    with col_btns:
        col1, col2, col3 = st.columns(3)
        with col1:
            check_btn = st.button("🔍 开始检查", type="primary", use_container_width=True)
        with col2:
            clear_btn = st.button("🗑️ 清空", use_container_width=True)
        with col3:
            export_btn = st.button("📥 导出", use_container_width=True)

    # 处理按钮事件
    if clear_btn:
        st.session_state.text = ""
        st.session_state.issues = []
        st.session_state.scene_type = "未识别"
        st.session_state.style_type = "未识别"
        st.session_state.selected_issue_idx = None
        st.rerun()

    if check_btn:
        if not st.session_state.text.strip():
            st.warning("请先输入文本")
        elif count_chinese_chars(st.session_state.text) > 10000:
            st.error("文本超过10000字，请减少字数")
        else:
            st.session_state.checking = True
            st.rerun()

    # 主内容区：左右分栏
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📄 输入文本")

        # 文本输入框
        text_input = st.text_area(
            "输入或粘贴文本",
            value=st.session_state.text,
            height=500,
            label_visibility="collapsed",
            key="text_input",
        )

        # 更新文本
        if text_input != st.session_state.text:
            st.session_state.text = text_input
            # 如果文本改变，清空检测结果
            if st.session_state.issues:
                st.session_state.issues = []
                st.session_state.scene_type = "未识别"
                st.session_state.style_type = "未识别"

        # 显示高亮文本（如果有检测结果）
        if st.session_state.issues:
            st.markdown("---")
            st.markdown("**原文预览（错误已高亮）：**")
            highlighted = highlight_text(
                st.session_state.text,
                st.session_state.issues,
                st.session_state.selected_issue_idx
            )
            st.markdown(f'<div style="background-color: #fafafa; padding: 1rem; border-radius: 0.5rem; line-height: 1.8;">{highlighted}</div>', unsafe_allow_html=True)

    with col_right:
        st.subheader("📋 检测结果")

        # 执行检测
        if st.session_state.checking and not st.session_state.issues:
            with st.spinner("正在检查..."):
                issues, scene_type, style_type = run_check(st.session_state.text)
                st.session_state.issues = issues
                st.session_state.scene_type = scene_type
                st.session_state.style_type = style_type
                st.session_state.checking = False
            st.rerun()

        # 显示场景识别结果和统计
        if st.session_state.issues or st.session_state.scene_type != "未识别":
            active_issues = [i for i in st.session_state.issues if not i.ignored]
            applied_count = sum(1 for i in st.session_state.issues if i.applied)
            ignored_count = sum(1 for i in st.session_state.issues if i.ignored)

            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <span style="color: #666;">识别为：</span>
                <strong>{st.session_state.scene_type}/{st.session_state.style_type}</strong>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <span class="stat-badge">共 {len(st.session_state.issues)} 个</span>
                <span class="stat-badge" style="background-color: #d4edda;">已修正 {applied_count} 个</span>
                <span class="stat-badge" style="background-color: #fff3cd;">已忽略 {ignored_count} 个</span>
            </div>
            """, unsafe_allow_html=True)

        # 显示问题卡片
        if st.session_state.issues:
            for idx, issue in enumerate(st.session_state.issues):
                if issue.ignored:
                    continue

                color = get_issue_color(issue.error_type)
                is_selected = (st.session_state.selected_issue_idx == idx)

                # 问题卡片
                card_class = "issue-card issue-selected" if is_selected else "issue-card"

                st.markdown(f"""
                <div class="{card_class}" id="issue-{idx}">
                    <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                        <span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.8rem; margin-right: 0.5rem;">
                            {issue.error_type}
                        </span>
                        <strong>第{issue.position}字</strong>
                        <span style="margin-left: 0.5rem; color: #666;">"{issue.error_text}"</span>
                    </div>
                    <div style="color: #333; margin-left: 0.5rem;">
                        → 建议改为：<strong style="color: {color};">{issue.suggestion}</strong>
                        <span style="color: #999; font-size: 0.8rem; margin-left: 0.5rem;">(置信度: {issue.confidence:.0%})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 按钮行
                col_a, col_b, col_c = st.columns([1, 1, 3])
                with col_a:
                    if st.button("✓ 应用", key=f"apply_{idx}", use_container_width=True):
                        # 应用修改
                        old_text = st.session_state.text
                        new_text = old_text[:issue.position] + issue.suggestion + old_text[issue.position_end:]
                        st.session_state.text = new_text
                        issue.applied = True
                        st.rerun()
                with col_b:
                    if st.button("✕ 忽略", key=f"ignore_{idx}", use_container_width=True):
                        issue.ignored = True
                        st.rerun()
                with col_c:
                    if st.button("📍 定位", key=f"locate_{idx}", use_container_width=True):
                        st.session_state.selected_issue_idx = idx if st.session_state.selected_issue_idx != idx else None
                        st.rerun()

        elif not st.session_state.checking:
            st.info("请在左侧输入文本，然后点击"开始检查"按钮")

    # 导出功能
    if export_btn and st.session_state.issues:
        report = f"""# 中文错别字检查报告

## 文本信息
- 场景类型：{st.session_state.scene_type}
- 表达风格：{st.session_state.style_type}
- 检测问题数：{len(st.session_state.issues)}
- 已修正：{sum(1 for i in st.session_state.issues if i.applied)}
- 已忽略：{sum(1 for i in st.session_state.issues if i.ignored)}

## 问题列表

"""
        for idx, issue in enumerate(st.session_state.issues, 1):
            if not issue.ignored:
                report += f"{idx}. 第{issue.position}字 \"{issue.error_text}\" - {issue.error_type} → 建议改为\"{issue.suggestion}\"\n"

        report += f"\n## 原文\n\n{st.session_state.text}"

        st.download_button(
            label="下载报告",
            data=report,
            file_name="错别字检查报告.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
