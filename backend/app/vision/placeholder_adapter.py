"""Placeholder vision adapter — returns mock structured descriptions.

This is the V1.3 default.  It does **not** call any real vision API;
it returns a hard-coded example VisionDescription in Chinese.  Swap to
a real adapter by setting ``VISION_PROVIDER`` in your ``.env`` file.
"""

from app.vision.base import VisionAdapter
from app.schemas.responses import VisionDescription


_MOCK_DESCRIPTION = VisionDescription(
    summary="当前为占位视觉描述，未调用真实视觉模型。返回的描述为固定中文示例，不匹配实际图片。",
    colors=["深炭黑", "橙色", "米白色"],
    composition="文字占据画面主体，竖向居中排列，视觉冲击力强。",
    typography="粗重中文标题字体，带有倾斜和立体阴影效果。",
    materials=["颗粒纹理", "火焰划痕质感"],
    subjects=["直播封面", "中文标题", "考前冲刺主题"],
    background="深色颗粒背景，带有橙色划痕点缀。",
    style_keywords=["强冲击", "紧张感", "冲刺感", "直播感"],
    potential_issues=[
        "文字过于拥挤，阅读节奏可能偏快",
        "信息层级可能需要进一步区分主副标题",
        "火焰/划痕质感可能分散对核心信息的注意力",
    ],
    suggested_prompt_text=(
        "这是一张考前直播封面，深色颗粒背景上使用橙色和米白色大字突出考前最后一场直播。"
        "粗重中文标题字体带有倾斜和立体阴影，视觉冲击力强。整体风格紧张、有冲刺感，"
        "适合教育培训类直播推广场景。"
    ),
    design_category="直播封面",
    target_audience_guess="考前冲刺的学生（占位示例，非真实识别）",
    price_band_guess="平价/免费推广（占位示例，非真实识别）",
    use_case="教育培训类直播推广",
)


class PlaceholderAdapter(VisionAdapter):
    """Returns a fixed mock structured description in Chinese.

    Does not read the actual image file — always returns the same
    example description.  Useful for testing and development when no
    real vision API key is available.
    """

    def describe_image(self, image_path: str, hint: str | None = None) -> str:
        return _MOCK_DESCRIPTION.suggested_prompt_text

    def describe_image_structured(self, image_path: str) -> VisionDescription:
        return _MOCK_DESCRIPTION
