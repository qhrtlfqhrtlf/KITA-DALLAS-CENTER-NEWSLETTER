OUTLET_MAP = {
    "Reuters":   "@reuters",
    "Bloomberg": "@bloombergbusiness",
    "WSJ":       "@wsj",
    "FT":        "@financialtimes",
    "Politico":  "@politico",
    "USTR":      "@usambassador",  # USTR 공식 계정
    "기타":      None,
}

FIXED_TAGS = ["@kitasns", "@kita_dallas_center"]

def get_tags(source: str, caption_text: str) -> list[str]:
    tags = list(FIXED_TAGS)
    outlet_tag = OUTLET_MAP.get(source)
    if outlet_tag and outlet_tag not in tags:
        tags.append(outlet_tag)
    return tags
