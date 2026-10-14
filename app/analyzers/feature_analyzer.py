from app.models.extraction import Feature
from app.models.extraction import Feature


def analyze_features(
    target_features: list[Feature],
    competitor_features: list[Feature],
) -> dict:
    """比较目标商品和竞品的功能特点。"""

    # 按功能名称建立映射，方便比较
    target_map = {
        feature.name.strip().casefold(): feature
        for feature in target_features
        if feature.name and feature.name.strip()
    }

    competitor_map = {
        feature.name.strip().casefold(): feature
        for feature in competitor_features
        if feature.name and feature.name.strip()
    }

    target_names = set(target_map)
    competitor_names = set(competitor_map)

    common_names = target_names & competitor_names
    target_only_names = target_names - competitor_names
    competitor_only_names = competitor_names - target_names

    return {
        "common_features": [
            target_map[name].model_dump()
            for name in sorted(common_names)
        ],
        "target_only_features": [
            target_map[name].model_dump()
            for name in sorted(target_only_names)
        ],
        "competitor_only_features": [
            competitor_map[name].model_dump()
            for name in sorted(competitor_only_names)
        ],
        "conclusion": (
            f"共有功能 {len(common_names)} 项，"
            f"目标商品独有功能 {len(target_only_names)} 项，"
            f"竞品独有功能 {len(competitor_only_names)} 项。"
        ),
    }
