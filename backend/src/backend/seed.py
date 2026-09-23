"""种子数据：11 条认知扭曲选项（spec 1.2，逐字取自 log_editor.py，不得改写）
+ 单用户锚点 jong(id=0)。
"""

from __future__ import annotations

from sqlalchemy import engine, text

SINGLE_USER = {"id": 0, "username": "jong"}

DISTORTION_OPTIONS = [
    (
        "all_or_nothing",
        "非此即彼",
        "All-or-Nothing Thinking",
        "用非黑即白的极端方式看待事物。如果表现不够完美，就会认为自己彻底失败。",
        "You see things in black-and-white extremes: if your performance falls "
        "short of perfect, you see yourself as a total failure.",
    ),
    (
        "overgeneralization",
        "以偏概全",
        "Overgeneralization",
        "基于单一事件推断出广泛结论，常使用“总是”、“从不”等绝对化语言。",
        'You draw broad conclusions from a single event, often using words like '
        '"always" or "never".',
    ),
    (
        "mental_filter",
        "心理过滤",
        "Mental Filter",
        "专注于消极事件而忽略积极方面，只看到负面信息，好像戴上了一副有色眼镜。",
        "You dwell on the negative and ignore the positive, seeing only the "
        "downside as if through tinted lenses.",
    ),
    (
        "disqualifying_the_positive",
        "否定正面思考",
        "Disqualifying the Positive",
        "拒绝接受正面的经验，找理由告诉自己这些经验不算数。",
        'You reject positive experiences by insisting that they "don\'t count".',
    ),
    (
        "mind_reading",
        "妄下结论 - 读心术",
        "Jumping to Conclusions - Mind Reading",
        "未经证实就认为知道别人在想什么，通常假设他人对自己有负面看法。",
        "Without evidence you assume you know what others are thinking, usually "
        "that they judge you negatively.",
    ),
    (
        "fortune_telling",
        "妄下结论 - 先知错误",
        "Jumping to Conclusions - Fortune Telling",
        "预测事情会变得很糟糕，并坚信这一预言为事实。",
        "You predict that things will turn out badly and treat that prediction "
        "as an established fact.",
    ),
    (
        "magnification_minimization",
        "放大和缩小",
        "Magnification and Minimization",
        "夸大自己的错误或他人的成就，同时缩小自己的优点或他人的缺点。",
        "You exaggerate your mistakes or others' achievements while shrinking "
        "your own strengths or others' shortcomings.",
    ),
    (
        "emotional_reasoning",
        "情绪化推理",
        "Emotional Reasoning",
        "根据感觉来判断现实，“我这么感觉，所以它肯定是真的”。",
        'You take your feelings as proof of reality: "I feel it, so it must be '
        'true."',
    ),
    (
        "should_statements",
        "‘应该’句式",
        '"Should" Statements',
        "常用“我应该…”、“我不应该…”来要求自己或他人，带来内疚感或愤怒。",
        'You use "I should…" or "I shouldn\'t…" to demand things of yourself or '
        "others, which breeds guilt or anger.",
    ),
    (
        "labeling",
        "乱贴标签",
        "Labeling",
        "给自己或他人贴上固定、消极的标签，而不是描述具体的行为。",
        "You attach a fixed, negative label to yourself or others instead of "
        "describing the specific behavior.",
    ),
    (
        "personalization",
        "罪责归己",
        "Personalization",
        "即使没有直接责任，也会将外界的消极事件归咎于自己。",
        "You blame yourself for negative external events even when you were not "
        "responsible for them.",
    ),
]


def run(eng: engine.Engine) -> None:
    """幂等写入种子数据：单用户 + 11 条扭曲选项（已存在则跳过）。"""
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, username) "
                "VALUES (:id, :username) "
                "ON CONFLICT(id) DO NOTHING"
            ),
            SINGLE_USER,
        )
        # spec 1.2：sort_order 固定 1–11，顺序即列表枚举序
        for i, (code, name_zh, name_en, note_zh, note_en) in enumerate(
            DISTORTION_OPTIONS, start=1
        ):
            conn.execute(
                text(
                    "INSERT INTO distortion_options "
                    "(code, name_zh, name_en, default_note_zh, default_note_en, sort_order) "
                    "VALUES (:code, :name_zh, :name_en, :note_zh, :note_en, :sort_order) "
                    "ON CONFLICT(code) DO NOTHING"
                ),
                {
                    "code": code,
                    "name_zh": name_zh,
                    "name_en": name_en,
                    "note_zh": note_zh,
                    "note_en": note_en,
                    "sort_order": i,
                },
            )
