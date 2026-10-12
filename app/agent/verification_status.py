def get_verification_status(
    page_read: bool,
    product_info: dict | None = None,
    verified_fields: list[str] | None = None,
    required_fields: list[str] | None = None,
) -> str:
    """根据详情页读取情况和规格核验结果，返回验证状态。"""
    if not page_read:
        return "验证失败，详情页未成功读取"
    if not product_info:
        return "详情页已读取，商品信息提取失败"
    if verified_fields is None:
        return "详情页已读取，参数待核验"
    if not required_fields:
        return (
            "部分参数已核验"
            if verified_fields
            else "详情页已读取，参数待核验"
        )
    verified = set(verified_fields)
    required = set(required_fields)
    if required.issubset(verified):
        return "参数已核验"
    if verified:
        return "部分参数已核验"
    return "详情页已读取，参数待核验"
def verify_product_specs(
    page_text: str,
    product_info: dict,
    required_fields: list[str] | None = None,
) -> dict:
    """根据详情页原文，初步检查商品规格是否有对应证据。"""

    required_fields = required_fields or [
        "capacity",
        "interface",
        "form_factor",
        "model",
    ]

    text = (page_text or "").casefold()

    specs = {
        "capacity": str(product_info.get("capacity") or ""),
        "interface": str(product_info.get("interface") or ""),
        "form_factor": str(product_info.get("form_factor") or ""),
        "model": str(product_info.get("model") or ""),
    }

    evidence = {}

    # 第一步：检查所有要求核验的字段
    for field in required_fields:
        value = specs.get(field, "").strip()

        if value and value.casefold() in text:
            evidence[field] = {
                "verified": True,
                "value": value,
            }
        else:
            evidence[field] = {
                "verified": False,
                "value": value or None,
            }
    # 第二步：循环结束后，再统一统计核验结果
    verified_fields = [
        field
        for field, result in evidence.items()
        if result["verified"]
    ]
    # 第三步：复用统一的状态判断函数
    status = get_verification_status(
        page_read=True,
        product_info=product_info,
        verified_fields=verified_fields,
        required_fields=required_fields,
    )
    return {
        "verification_status": status,
        "verified_fields": verified_fields,
        "evidence": evidence,
    }



