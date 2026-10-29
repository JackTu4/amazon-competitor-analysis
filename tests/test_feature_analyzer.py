from app.models.extraction import Feature
from app.analyzers.feature_analyzer import analyze_features


def test_analyze_features():
    target = [
        Feature(name="NVMe", description="支持 NVMe 协议"),
        Feature(name="PCIe 4.0", description="支持 PCIe 4.0"),
        Feature(name="Warranty", description="三年质保"),
    ]

    competitor = [
        Feature(name="NVMe", description="支持 NVMe 协议"),
        Feature(name="PCIe 4.0", description="支持 PCIe 4.0"),
        Feature(name="Warranty", description="五年质保"),
    ]

    result = analyze_features(target, competitor)

    # 名称相同就视为共有功能
    assert len(result["common_features"]) == 3
    assert result["target_only_features"] == []
    assert result["competitor_only_features"] == []


def test_empty_features():
    result = analyze_features([], [])

    assert result["common_features"] == []
    assert result["target_only_features"] == []
    assert result["competitor_only_features"] == []
