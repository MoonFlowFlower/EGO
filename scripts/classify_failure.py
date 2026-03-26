#!/usr/bin/env python3
"""
开发闭环 v1 - 失败分类与收口检查器

功能：
1. 失败类型分类（7 类）
2. 假完成口径检查
3. 收口状态验证

失败分类：
- boundary_error: 边界归属错误，能力错位写入
- authority_error: 权威源错误，数据定义不一致
- schema_error: schema/contract 错误，字段定义缺失
- runtime_error: runtime/orchestration 错误，执行链异常
- e2e_broken: E2E 断链，主链验证失败
- test_gap: 测试缺口，覆盖不足
- wording_error: 仅口径错误，实际未生效

使用方式：
    python scripts/classify_failure.py --error-log PATH
    python scripts/classify_failure.py --check-wording PATH
    python scripts/classify_failure.py --analyze-report PATH
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
EGO_ROOT = SCRIPT_DIR.parent


# 失败类型定义
FAILURE_TYPES = {
    "boundary_error": {
        "description": "边界归属错误，能力错位写入",
        "patterns": [
            r"EgoCore.*不应该.*OpenEmotion",
            r"OpenEmotion.*不应该.*EgoCore",
            r"越界",
            r"边界.*错误",
            r"归属.*错误",
            r"偷做",
        ],
        "severity": "high",
    },
    "authority_error": {
        "description": "权威源错误，数据定义不一致",
        "patterns": [
            r"权威源.*错误",
            r"双重真相源",
            r"双主",
            r"数据定义.*不一致",
            r"schema.*冲突",
        ],
        "severity": "high",
    },
    "schema_error": {
        "description": "schema/contract 错误，字段定义缺失",
        "patterns": [
            r"schema.*错误",
            r"contract.*错误",
            r"字段.*缺失",
            r"字段.*未定义",
            r"类型.*错误",
            r"KeyError",
            r"AttributeError",
        ],
        "severity": "medium",
    },
    "runtime_error": {
        "description": "runtime/orchestration 错误，执行链异常",
        "patterns": [
            r"runtime.*错误",
            r"orchestration.*错误",
            r"执行.*失败",
            r"Exception",
            r"Error:",
            r"Traceback",
            r"ImportError",
            r"ModuleNotFoundError",
        ],
        "severity": "medium",
    },
    "e2e_broken": {
        "description": "E2E 断链，主链验证失败",
        "patterns": [
            r"E2E.*失败",
            r"主链.*断",
            r"验证.*失败",
            r"assert.*failed",
            r"AssertionError",
            r"测试.*失败",
        ],
        "severity": "high",
    },
    "test_gap": {
        "description": "测试缺口，覆盖不足",
        "patterns": [
            r"测试.*覆盖.*不足",
            r"缺少.*测试",
            r"未测试",
            r"test.*gap",
            r"coverage.*low",
        ],
        "severity": "low",
    },
    "wording_error": {
        "description": "仅口径错误，实际未生效",
        "patterns": [
            r"口径.*错误",
            r"误报",
            r"未生效",
            r"未接主链",
            r"未启用",
        ],
        "severity": "low",
    },
}

# 假完成口径
FAKE_COMPLETION_PHRASES = [
    (r"已完成(?!.*验证)", "声称'已完成'但无验证证据"),
    (r"已修复(?!.*测试)", "声称'已修复'但无测试验证"),
    (r"已生效(?!.*触发)", "声称'已生效'但无触发证据"),
    (r"已闭环(?!.*启用)", "声称'已闭环'但未启用"),
    (r"完成.*但.*待验证", "声称完成但需要验证"),
]


@dataclass
class FailureClassification:
    """失败分类结果"""
    error_id: str
    error_type: str
    description: str
    severity: str
    evidence: str
    matched_pattern: Optional[str]
    timestamp: str


@dataclass
class WordingCheckResult:
    """口径检查结果"""
    file_path: str
    line_number: int
    phrase: str
    issue: str
    context: str


@dataclass
class ClosureCheckResult:
    """收口检查结果"""
    main_chain_accessed: bool
    enabled: bool
    trigger_evidence: Optional[str]
    fake_phrases_found: List[str]
    valid_closure: bool
    issues: List[str]


@dataclass
class ClassificationReport:
    """分类报告"""
    run_id: str
    timestamp: str
    failures_classified: int
    failures_by_type: Dict[str, int]
    failures_by_severity: Dict[str, int]
    wording_issues: int
    closure_issues: int
    classifications: List[dict]
    wording_results: List[dict]
    closure_result: Optional[dict]


def classify_error(error_text: str) -> FailureClassification:
    """分类单个错误"""
    error_id = f"err_{hash(error_text) % 1000000:06d}"

    best_match = None
    best_type = "runtime_error"  # 默认

    for ftype, info in FAILURE_TYPES.items():
        for pattern in info["patterns"]:
            if re.search(pattern, error_text, re.IGNORECASE):
                best_match = pattern
                best_type = ftype
                break
        if best_match:
            break

    info = FAILURE_TYPES[best_type]

    return FailureClassification(
        error_id=error_id,
        error_type=best_type,
        description=info["description"],
        severity=info["severity"],
        evidence=error_text[:200] if len(error_text) > 200 else error_text,
        matched_pattern=best_match,
        timestamp=datetime.now().isoformat(),
    )


def check_wording(text: str, file_path: str = "input") -> List[WordingCheckResult]:
    """检查假完成口径"""
    results = []
    lines = text.split("\n")

    for i, line in enumerate(lines, 1):
        for pattern, issue in FAKE_COMPLETION_PHRASES:
            if re.search(pattern, line):
                results.append(WordingCheckResult(
                    file_path=file_path,
                    line_number=i,
                    phrase=re.search(pattern, line).group(),
                    issue=issue,
                    context=line.strip()[:100],
                ))

    return results


def check_closure(
    main_chain_accessed: bool,
    enabled: bool,
    trigger_evidence: Optional[str],
    documentation: str = "",
) -> ClosureCheckResult:
    """检查收口状态"""
    issues = []
    fake_phrases = []

    # 检查假完成口径
    wording_results = check_wording(documentation, "documentation")
    for wr in wording_results:
        fake_phrases.append(wr.phrase)
        issues.append(f"假完成口径: '{wr.phrase}' - {wr.issue}")

    # 检查主链接入
    if not main_chain_accessed:
        issues.append("未接入主链")

    # 检查启用状态
    if not enabled:
        issues.append("未启用")

    # 检查触发证据
    if not trigger_evidence:
        issues.append("无触发证据")

    # 判断是否有效收口
    valid = (
        main_chain_accessed
        and enabled
        and trigger_evidence is not None
        and len(fake_phrases) == 0
    )

    return ClosureCheckResult(
        main_chain_accessed=main_chain_accessed,
        enabled=enabled,
        trigger_evidence=trigger_evidence,
        fake_phrases_found=fake_phrases,
        valid_closure=valid,
        issues=issues,
    )


def analyze_error_log(log_path: Path) -> List[FailureClassification]:
    """分析错误日志"""
    content = log_path.read_text(encoding="utf-8", errors="ignore")

    # 尝试分割多个错误
    error_blocks = re.split(r"\n(?=Error|Exception|Traceback|FAIL)", content)

    classifications = []
    for block in error_blocks:
        block = block.strip()
        if block and len(block) > 10:
            classification = classify_error(block)
            classifications.append(classification)

    return classifications


def analyze_test_report(report_path: Path) -> List[FailureClassification]:
    """分析测试报告"""
    content = report_path.read_text(encoding="utf-8", errors="ignore")

    # 解析 JSON 或文本
    if report_path.suffix == ".json":
        try:
            data = json.loads(content)
            # 提取失败信息
            failures = data.get("failures", [])
            if not failures and "results" in data:
                failures = [r for r in data["results"] if not r.get("passed", True)]

            classifications = []
            for f in failures:
                error_text = json.dumps(f, ensure_ascii=False)
                classifications.append(classify_error(error_text))

            return classifications
        except json.JSONDecodeError:
            pass

    # 作为文本处理
    return analyze_error_log(report_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="失败分类与收口检查器")
    parser.add_argument("--error-log", type=str, help="错误日志文件路径")
    parser.add_argument("--check-wording", type=str, help="检查文档中的假完成口径")
    parser.add_argument("--analyze-report", type=str, help="分析测试报告")
    parser.add_argument("--stdin", action="store_true", help="从标准输入读取")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" Development Closed Loop v1 - Failure Classifier")
    print("=" * 70)

    classifications = []
    wording_results = []
    closure_result = None

    # 从错误日志分类
    if args.error_log:
        log_path = Path(args.error_log)
        if log_path.exists():
            print(f"\n[CLASSIFY] Analyzing error log: {log_path}")
            classifications = analyze_error_log(log_path)
            for c in classifications:
                print(f"  [{c.severity.upper()}] {c.error_type}: {c.description[:50]}")

    # 从测试报告分析
    if args.analyze_report:
        report_path = Path(args.analyze_report)
        if report_path.exists():
            print(f"\n[CLASSIFY] Analyzing test report: {report_path}")
            classifications = analyze_test_report(report_path)
            for c in classifications:
                print(f"  [{c.severity.upper()}] {c.error_type}: {c.description[:50]}")

    # 从标准输入读取
    if args.stdin:
        print("\n[CLASSIFY] Reading from stdin...")
        content = sys.stdin.read()
        classifications = [classify_error(content)]
        for c in classifications:
            print(f"  [{c.severity.upper()}] {c.error_type}: {c.description[:50]}")

    # 检查文档口径
    if args.check_wording:
        doc_path = Path(args.check_wording)
        if doc_path.exists():
            print(f"\n[WORDING] Checking: {doc_path}")
            content = doc_path.read_text(encoding="utf-8", errors="ignore")
            wording_results = check_wording(content, str(doc_path))
            for wr in wording_results:
                print(f"  Line {wr.line_number}: '{wr.phrase}' - {wr.issue}")

    # 统计
    failures_by_type = {}
    failures_by_severity = {}
    for c in classifications:
        failures_by_type[c.error_type] = failures_by_type.get(c.error_type, 0) + 1
        failures_by_severity[c.severity] = failures_by_severity.get(c.severity, 0) + 1

    # 生成报告
    run_id = f"classify_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report = ClassificationReport(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        failures_classified=len(classifications),
        failures_by_type=failures_by_type,
        failures_by_severity=failures_by_severity,
        wording_issues=len(wording_results),
        closure_issues=len(closure_result.issues) if closure_result else 0,
        classifications=[asdict(c) for c in classifications],
        wording_results=[asdict(w) for w in wording_results],
        closure_result=asdict(closure_result) if closure_result else None,
    )

    # 保存报告
    artifacts_dir = EGO_ROOT / "artifacts" / "devloop_v1"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_file = artifacts_dir / f"classification_report_{run_id}.json"

    with open(report_file, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str, ensure_ascii=False)

    # 打印结果
    print("\n" + "=" * 70)
    print(f" Failures classified: {len(classifications)}")
    if failures_by_type:
        print(" By type:")
        for ftype, count in failures_by_type.items():
            print(f"   {ftype}: {count}")
    if failures_by_severity:
        print(" By severity:")
        for sev, count in failures_by_severity.items():
            print(f"   {sev}: {count}")
    print(f" Wording issues: {len(wording_results)}")
    print(f" Report: {report_file}")
    print("=" * 70 + "\n")

    return 0 if len(classifications) == 0 and len(wording_results) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
