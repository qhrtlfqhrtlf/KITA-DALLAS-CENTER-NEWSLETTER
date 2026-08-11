# -*- coding: utf-8 -*-
"""데이터.json을 읽어 인터랙티브 단일 HTML 대시보드를 생성한다.

구성: 텍사스 지도 위에 13개 구단 배지를 실제 홈구장 위치에 뿌리고,
배지를 누르면 그 구단 상세로 넘어간다.

- 외부 CDN·원격 이미지를 쓰지 않는다 (단일 파일 자체 완결).
- file:// 에서 fetch는 CORS로 막히므로 데이터를 <script>에 인라인으로 박는다.
- 구단 로고: `로고/` 폴더에 `<약칭>.png|svg|jpg|webp` 파일을 두면 생성 시
  base64 data URI로 HTML 안에 박아 로고 배지로 렌더한다.
  파일이 없는 구단은 구단 상징색 + 약칭 배지로 자동 대체된다(폴백).
  ※ 로고는 각 구단의 등록 상표다. 사용 범위(내부 문서/외부 배포)는
    사용자 책임으로 판단해 배치하며, 본 스크립트는 파일이 있을 때만 사용한다.
- 지도는 실제 경위도를 등장방형 투영으로 그린다. 외곽선·구장 좌표가 같은
  투영식을 쓰므로 배지 위치가 외곽선과 어긋나지 않는다.
- 같은 구장을 쓰는 구단(AAC 3곳, Shell Energy 2곳)과 근접 구장(휴스턴)은
  앵커를 실제 좌표에 두고 배지만 밀어내며 연결선을 그린다.
- Phase 2(미국 전도) 확장 시 OUTLINE과 구단좌표를 교체하면 나머지는 재사용된다.

실행: python 대시보드생성.py
출력: 대시보드.html
"""
import base64
import io
import json
import os

SRC = "데이터.json"
OUT = "대시보드.html"
로고폴더 = "로고"
로고확장자 = [".svg", ".png", ".webp", ".jpg", ".jpeg"]   # 앞쪽 우선
MIME = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def 로고찾기(코드, 구단명):
    """로고/<약칭> 또는 로고/<구단명> 파일을 찾아 data URI로 돌려준다."""
    if not os.path.isdir(로고폴더):
        return None, None
    for 후보 in (코드, 코드.lower(), 구단명):
        for ext in 로고확장자:
            p = os.path.join(로고폴더, 후보 + ext)
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    b = fh.read()
                uri = "data:%s;base64,%s" % (MIME[ext], base64.b64encode(b).decode("ascii"))
                return uri, os.path.basename(p)
    return None, None

업종색 = {
    "에너지": "#b45309", "기술·IT": "#4338ca", "헬스케어": "#0f766e",
    "금융": "#1d4ed8", "자동차": "#b91c1c", "식음료": "#a16207",
    "유통·이커머스": "#7c2d92", "건설·설비": "#57534e", "항공": "#0369a1",
    "통신": "#9333ea", "보험": "#065f46", "기타": "#525252",
}
휘도최소 = 0.30


def _휘도(rgb):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (c(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def 다크보정(h):
    rgb = _rgb(h)
    for _ in range(60):
        if _휘도(rgb) >= 휘도최소:
            break
        rgb = [min(255, round(v + (255 - v) * 0.08)) for v in rgb]
    return "#%02x%02x%02x" % tuple(rgb)


업종색다크 = {k: 다크보정(v) for k, v in 업종색.items()}


def 글자색(배경):
    """배지 바탕색 대비 읽히는 글자색을 고른다."""
    return "#0c0a09" if _휘도(_rgb(배경)) > 0.35 else "#ffffff"


# 텍사스 외곽선 — (경도, 위도). 팬핸들 북서쪽에서 시계방향.
OUTLINE = [
    (-103.04, 36.50), (-100.00, 36.50), (-100.00, 34.56), (-99.20, 34.56),
    (-98.95, 34.22), (-98.40, 34.16), (-97.95, 33.90), (-97.45, 33.83),
    (-97.10, 33.74), (-96.60, 33.68), (-96.15, 33.75), (-95.55, 33.94),
    (-94.98, 33.66), (-94.04, 33.55),
    (-94.04, 32.00), (-94.04, 31.00),
    (-93.83, 30.60), (-93.72, 30.30), (-93.56, 30.05), (-93.83, 29.80),
    (-94.75, 29.35), (-95.10, 29.10), (-95.50, 28.80), (-96.00, 28.60),
    (-96.50, 28.40), (-97.00, 28.05), (-97.20, 27.60), (-97.35, 27.20),
    (-97.45, 26.60), (-97.15, 26.05),
    (-97.80, 26.05), (-98.30, 26.20), (-98.80, 26.35), (-99.10, 26.45),
    (-99.30, 26.85), (-99.45, 27.20), (-99.80, 27.50), (-100.30, 28.00),
    (-100.65, 28.35), (-101.00, 29.20), (-101.40, 29.75), (-102.30, 29.88),
    (-102.80, 29.50), (-103.15, 28.98), (-103.80, 29.30), (-104.50, 29.70),
    (-104.90, 30.30), (-105.60, 30.90), (-106.30, 31.40), (-106.62, 31.90),
    (-106.62, 32.00), (-103.06, 32.00), (-103.06, 36.50),
]

# 구단별 실제 홈구장 좌표 + 배지 색. 색은 구단 상징색(로고 아님).
# 키는 데이터.json의 "구단명"과 정확히 일치해야 한다.
구단좌표 = {
    "Dallas Cowboys":    dict(lon=-97.0929, lat=32.7473, 코드="COW", 색="#041E42", 테두리="#869397"),
    "Dallas Mavericks":  dict(lon=-96.8104, lat=32.7905, 코드="MAV", 색="#00538C", 테두리="#B8C4CA"),
    "Dallas Stars":      dict(lon=-96.8104, lat=32.7905, 코드="STR", 색="#006847", 테두리="#8F8F8C"),
    "Dallas Wings":      dict(lon=-96.8104, lat=32.7905, 코드="WGS", 색="#0C2340", 테두리="#C4D600"),
    "Texas Rangers":     dict(lon=-97.0838, lat=32.7513, 코드="RGR", 색="#003278", 테두리="#C0111F"),
    "FC Dallas":         dict(lon=-96.8353, lat=33.1545, 코드="FCD", 색="#E81F3E", 테두리="#22B0E5"),
    "Houston Texans":    dict(lon=-95.4107, lat=29.6847, 코드="HTX", 색="#03202F", 테두리="#A71930"),
    "Houston Rockets":   dict(lon=-95.3621, lat=29.7508, 코드="ROC", 색="#CE1141", 테두리="#C4CED4"),
    "Houston Astros":    dict(lon=-95.3555, lat=29.7573, 코드="AST", 색="#002D62", 테두리="#EB6E1F"),
    "Houston Dynamo FC": dict(lon=-95.3524, lat=29.7522, 코드="DYN", 색="#F4911E", 테두리="#101820"),
    "Houston Dash":      dict(lon=-95.3524, lat=29.7522, 코드="DSH", 색="#6CADDF", 테두리="#101820"),
    "San Antonio Spurs": dict(lon=-98.4375, lat=29.4270, 코드="SPU", 색="#C4CED4", 테두리="#000000"),
    "Austin FC":         dict(lon=-97.7204, lat=30.3874, 코드="ATX", 색="#00B140", 테두리="#000000"),
}

# 지도에 얹을 도시 이름 (클릭하면 도시 단위로 묶어 보여준다)
# 도시 이름 위치. 배지 밀집 지역을 피해 여백으로 뺀다
# (겹치면 배지가 밀려나므로 안전하지만, 애초에 떨어뜨려 두면 연결선이 짧아진다).
도시라벨좌표 = {
    "DFW": (-98.60, 33.60),      # 배지군 서쪽 여백
    "휴스턴": (-94.60, 30.30),    # 배지군 북동쪽 여백
    "샌안토니오": (-99.60, 28.90),  # 배지 남서쪽
    "오스틴": (-98.90, 30.55),     # 배지 서쪽
}
도시라벨 = {"DFW": "댈러스-포트워스", "휴스턴": "휴스턴",
            "샌안토니오": "샌안토니오", "오스틴": "오스틴"}
도시순서 = ["DFW", "휴스턴", "샌안토니오", "오스틴"]

W, H, PAD = 760, 700, 34


def 투영(구역):
    lons = [p[0] for p in 구역]
    lats = [p[1] for p in 구역]
    lo0, lo1, la0, la1 = min(lons), max(lons), min(lats), max(lats)
    s = min((W - PAD * 2) / (lo1 - lo0), (H - PAD * 2) / (la1 - la0))
    ox = PAD + ((W - PAD * 2) - (lo1 - lo0) * s) / 2
    oy = PAD + ((H - PAD * 2) - (la1 - la0) * s) / 2

    def f(lon, lat):
        return (round(ox + (lon - lo0) * s, 1), round(oy + (la1 - lat) * s, 1))
    return f


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    구단들 = d["구단"]
    기준 = d["메타"].get("기준시점", {})

    # 데이터와 좌표표가 어긋나면 조용히 빠지지 않게 여기서 멈춘다.
    이름들 = {t["구단명"] for t in 구단들}
    빠짐 = 이름들 - set(구단좌표)
    남음 = set(구단좌표) - 이름들
    if 빠짐 or 남음:
        raise SystemExit("구단좌표 불일치 — 좌표 없음: %s / 데이터 없음: %s" % (sorted(빠짐), sorted(남음)))
    코드들 = [v["코드"] for v in 구단좌표.values()]
    if len(set(코드들)) != len(코드들):
        raise SystemExit("구단 약칭 중복: %s" % 코드들)

    f = 투영(OUTLINE)
    path = "M" + " L".join(f"{x},{y}" for x, y in (f(*p) for p in OUTLINE)) + " Z"

    배지 = []
    로고찾음, 로고없음 = [], []
    for t in 구단들:
        v = 구단좌표[t["구단명"]]
        x, y = f(v["lon"], v["lat"])
        uri, 파일 = 로고찾기(v["코드"], t["구단명"])
        (로고찾음 if uri else 로고없음).append(파일 or v["코드"])
        배지.append({
            "구단명": t["구단명"], "리그": t["리그"], "도시": t["도시"],
            "코드": v["코드"], "색": v["색"], "테두리": v["테두리"],
            "글자색": 글자색(v["색"]), "로고": uri,
            "구장": t["홈구장"], "ax": x, "ay": y,
        })

    도시핀 = {c: dict(zip(("x", "y"), f(*도시라벨좌표[c])), 라벨=도시라벨[c])
              for c in 도시순서}

    # 로고를 넣지 않은 상태(기본)와 넣은 상태의 안내 문구를 다르게 쓴다.
    if 로고찾음:
        로고안내 = ("구단 로고 %d/%d개 적용. 나머지는 구단 상징색 + 약칭 배지로 표시됩니다. "
                    "로고는 각 구단의 등록 상표이므로 외부 발행물에는 사용 조건을 확인하세요."
                    % (len(로고찾음), len(배지)))
    else:
        로고안내 = ("구단 표식은 구단 상징색 + 약칭 배지입니다. "
                    "로고 이미지를 쓰려면 <code>로고/&lt;약칭&gt;.png</code>를 넣고 "
                    "<code>대시보드생성.py</code>를 다시 실행하세요.")

    def js(o):
        return json.dumps(o, ensure_ascii=False).replace("<", "\\u003c")

    html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>미국 구단·스폰서 지도 — 텍사스 권역 대시보드</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:"Malgun Gothic","맑은 고딕",-apple-system,"Segoe UI",sans-serif;
  background:#0c0a09;color:#e7e5e4;line-height:1.65;font-size:15px}}
.top{{padding:18px 26px 14px;border-bottom:1px solid #292524}}
h1{{margin:0;font-size:19px;letter-spacing:-.01em}}
.top .sub{{color:#a8a29e;font-size:12.5px;margin-top:5px}}
.asof{{display:inline-block;margin-top:9px;font-size:11.5px;color:#c4b5fd;
  background:#2e1065;border:1px solid #4c1d95;border-radius:5px;padding:4px 10px}}
.layout{{display:grid;grid-template-columns:minmax(380px,52%) minmax(0,1fr);align-items:start}}
/* 지도 */
.mapwrap{{padding:14px 20px 22px;border-right:1px solid #292524;position:sticky;top:0}}
svg{{width:100%;height:auto;display:block;overflow:visible}}
.state{{fill:#d6d3d1;stroke:#57534e;stroke-width:1.6}}
.cityname{{fill:#57534e;font-size:13px;font-weight:700;cursor:pointer;
  paint-order:stroke;stroke:#d6d3d1;stroke-width:3.5px}}
.cityname:hover{{fill:#0c0a09}}
.lead{{stroke:#78716c;stroke-width:1.1;fill:none}}
.anchor{{fill:#44403c}}
.badge{{cursor:pointer}}
.badge rect{{stroke-width:2;rx:6;ry:6}}
.badge text{{font-size:13px;font-weight:800;text-anchor:middle;pointer-events:none;
  letter-spacing:.3px}}
.badge .lgl{{font-size:8.5px;font-weight:700;opacity:.85}}
.badge:hover rect,.badge:focus-visible rect{{stroke:#0c0a09;stroke-width:3}}
.badge.on rect{{stroke:#0c0a09;stroke-width:3.5}}
.badge:focus-visible{{outline:none}}
.legend{{margin-top:12px;display:flex;flex-wrap:wrap;gap:5px}}
.legend span{{font-size:10.5px;padding:2px 7px;border-radius:3px;color:var(--c);
  background:color-mix(in srgb,var(--c) 20%,#0c0a09);border:1px solid color-mix(in srgb,var(--c) 45%,#0c0a09)}}
.hint{{font-size:11.5px;color:#78716c;margin-top:10px}}
/* 패널 */
.panel{{padding:16px 24px 60px;min-width:0}}
.ph{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  padding-bottom:10px;border-bottom:1px solid #292524}}
.ph h2{{margin:0;font-size:17px}}
.ph .c{{font-size:12px;color:#a8a29e}}
.btn{{margin-left:auto;font:inherit;font-size:12px;cursor:pointer;background:#1c1917;
  color:#e7e5e4;border:1px solid #44403c;border-radius:5px;padding:4px 11px}}
.btn:hover{{background:#292524}}
.ov{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:9px;margin:14px 0 16px}}
.ov div{{background:#1c1917;border:1px solid #292524;border-radius:7px;padding:10px 12px}}
.ov b{{display:block;font-size:20px}}
.ov span{{font-size:11px;color:#a8a29e}}
/* 도시별 목록 (개요) */
.citygrp{{margin:14px 0}}
.citygrp h3{{margin:0 0 7px;font-size:14px;display:flex;align-items:center;gap:8px}}
.citygrp h3 span{{font-size:11px;font-weight:400;color:#a8a29e}}
.tiles{{display:flex;flex-wrap:wrap;gap:7px}}
.tile{{display:flex;align-items:center;gap:8px;cursor:pointer;text-align:left;
  background:#1c1917;border:1px solid #292524;border-radius:8px;padding:7px 11px 7px 8px;
  font:inherit;color:#e7e5e4}}
.tile:hover{{background:#292524;border-color:#57534e}}
.tile .mk{{width:30px;height:22px;border-radius:5px;display:grid;place-items:center;
  font-size:10.5px;font-weight:800;flex:none;border:1.5px solid}}
.tile .tn{{font-size:12.5px;font-weight:700;line-height:1.25}}
/* 로고 표식 — 흰 바탕에 원본 비율 유지 */
.mk.lg-img{{background:#fff;padding:2px}}
.mk.lg-img img{{max-width:100%;max-height:100%;object-fit:contain;display:block}}
.tile .tl{{font-size:10.5px;color:#a8a29e}}
/* 구단 상세 */
.team{{border:1px solid #292524;border-radius:9px;margin:14px 0;overflow:hidden;background:#141210}}
.th{{padding:12px 16px;background:#1c1917;border-bottom:1px solid #292524}}
.th .r1{{display:flex;flex-wrap:wrap;align-items:center;gap:8px}}
.th .mk{{width:38px;height:27px;border-radius:6px;display:grid;place-items:center;
  font-size:12px;font-weight:800;flex:none;border:2px solid}}
.th .nm{{font-size:15px;font-weight:700}}
.th .lg{{font-size:10px;font-weight:700;background:#e7e5e4;color:#0c0a09;padding:2px 7px;border-radius:3px}}
.th .ex{{font-size:10px;font-weight:700;background:#4c1d95;color:#ddd6fe;padding:2px 7px;border-radius:3px}}
.th .meta{{font-size:12px;color:#a8a29e;margin-top:5px}}
.th .meta b{{color:#e7e5e4}}
.nr{{font-size:12px;color:#fbbf24;margin-top:4px}}
.share{{font-size:11.5px;color:#a8a29e;margin-top:4px}}
.tb{{padding:3px 16px 14px}}
.sp{{padding:11px 0;border-bottom:1px dashed #292524}}
.sp:last-of-type{{border-bottom:none}}
.sp.end{{opacity:.5}}
.sp .r1{{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin-bottom:5px}}
.sp .co{{font-weight:700;font-size:14px}}
.chip{{font-size:10.5px;padding:2px 7px;border-radius:3px;white-space:nowrap;color:var(--c);
  background:color-mix(in srgb,var(--c) 20%,#0c0a09);border:1px solid color-mix(in srgb,var(--c) 45%,#0c0a09)}}
.gr{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:20px;white-space:nowrap}}
.g1{{background:#052e16;color:#86efac}}
.g2{{background:#422006;color:#fcd34d}}
.g3{{background:#292524;color:#a8a29e}}
.kr{{font-size:10px;font-weight:700;background:#e7e5e4;color:#0c0a09;padding:2px 6px;border-radius:3px}}
.nt{{font-size:10.5px;color:#a8a29e}}
.sp dl{{display:grid;grid-template-columns:76px minmax(0,1fr);gap:2px 12px;margin:5px 0 0;font-size:12.5px}}
.sp dt{{color:#78716c;font-size:10.5px;padding-top:3px}}
.sp dd{{margin:0;color:#d6d3d1}}
.pt{{background:#1c1917;border-left:3px solid #fbbf24;padding:9px 12px;margin-top:12px;font-size:12.5px}}
.pt b{{display:block;font-size:10px;color:#78716c;letter-spacing:.05em;margin-bottom:2px}}
.fn{{margin-top:9px;padding:9px 12px;background:#1c1917;border:1px solid #292524;border-radius:6px;font-size:11.5px}}
.fn>b{{display:block;font-size:10px;color:#78716c;letter-spacing:.05em;margin-bottom:4px}}
.fn ol{{margin:0;padding-left:19px}}
.fn li{{margin:3px 0;color:#a8a29e}}
.fn .s{{margin:6px 0 0;padding-top:5px;border-top:1px solid #292524;color:#78716c;font-size:10.5px}}
.foot{{margin-top:24px;padding-top:14px;border-top:1px solid #292524;font-size:11.5px;color:#57534e}}
@media(max-width:920px){{.layout{{grid-template-columns:1fr}}
  .mapwrap{{position:static;border-right:none;border-bottom:1px solid #292524}}
  .panel{{padding:16px 18px 50px}}}}
</style></head><body>
<div class="top">
<h1>미국 구단·스폰서 지도 — 텍사스 권역</h1>
<p class="sub">지도의 구단 배지를 누르면 그 구단의 스폰서 상세로 넘어갑니다 · 도시 이름을 누르면 도시 단위로 묶어 봅니다 · 한국무역협회 달러스지부</p>
<p class="asof"><b>기준 시점</b> {기준.get("기준", "")}</p>
</div>
<div class="layout">
<div class="mapwrap">
  <svg id="map" viewBox="0 0 {W} {H}" role="group" aria-label="텍사스 권역 구단 지도">
    <path class="state" d="{path}"></path>
    <g id="leads"></g><g id="cities"></g><g id="badges"></g>
  </svg>
  <div class="legend" id="legend"></div>
  <p class="hint">{로고안내}
  배지가 겹치는 구장(American Airlines Center 3개 구단, Shell Energy Stadium 2개 구단, 휴스턴 4개 구장)은
  실제 위치에 점을 두고 배지를 밀어내 연결선으로 이었습니다.</p>
</div>
<div class="panel" id="panel"></div>
</div>
<script>
const DATA = {js(구단들)};
const BADGES = {js(배지)};
const CITY = {js(도시핀)};
const ORDER = {js(도시순서)};
const COLOR = {js(업종색다크)};
const ASOF = {js(기준)};
const LABEL = {js(도시라벨)};
const VB = {{w: {W}, h: {H}}};

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}})[c]);
const active = t => t.스폰서.filter(s => s.상태 !== "종료");
const byCity = c => DATA.filter(t => t.도시 === c);
const team = n => DATA.find(t => t.구단명 === n);
const badge = n => BADGES.find(b => b.구단명 === n);
const chip = i => `<span class="chip" style="--c:${{COLOR[i] || "#525252"}}">${{esc(i)}}</span>`;
const grade = g => `<span class="gr ${{ {{"공식 발표":"g1","언론 보도":"g2"}}[g] || "g3" }}">${{esc(g)}}</span>`;
/* 네이밍 라이츠 판정은 보고서생성.py와 동일 기준(노출영역에 "구장 명칭") */
const namingRights = t => active(t).find(s => (s.노출영역 || "").includes("구장 명칭"));
const sameVenue = t => DATA.filter(x => x.홈구장 === t.홈구장 && x.구단명 !== t.구단명);

/* ---------- 배지 겹침 해소 ----------
   앵커(실제 구장 좌표)는 고정하고 배지만 밀어낸다. 난수를 쓰지 않아
   실행할 때마다 같은 배치가 나온다. */
const BW = 42, BH = 26, GAP = 3;
/* obstacles: 도시 이름 라벨의 실제 bbox. 배지가 이 위로 올라오지 않게 밀어낸다. */
function layout(obstacles) {{
  const groups = {{}};
  BADGES.forEach(b => {{
    const k = b.ax + "," + b.ay;
    (groups[k] = groups[k] || []).push(b);
  }});
  Object.values(groups).forEach(g => {{
    g.forEach((b, i) => {{
      if (g.length === 1) {{ b.x = b.ax; b.y = b.ay - 15; return; }}
      const a = (-Math.PI / 2) + (i * 2 * Math.PI / g.length);
      b.x = b.ax + Math.cos(a) * 30;
      b.y = b.ay + Math.sin(a) * 26;
    }});
  }});
  const push = (a, ow, oh, cx, cy) => {{      // a를 (cx,cy) 중심 사각형 밖으로
    const dx = a.x - cx, dy = a.y - cy;
    const ox = (BW + ow) / 2 + GAP - Math.abs(dx);
    const oy = (BH + oh) / 2 + GAP - Math.abs(dy);
    if (ox <= 0 || oy <= 0) return;
    if (ox < oy) a.x += (dx >= 0 ? 1 : -1) * ox;
    else a.y += (dy >= 0 ? 1 : -1) * oy;
  }};
  const step = pull => {{
    for (let i = 0; i < BADGES.length; i++) {{
      const a = BADGES[i];
      for (let j = i + 1; j < BADGES.length; j++) {{
        const b = BADGES[j];
        const dx = b.x - a.x, dy = b.y - a.y;
        const ox = (BW + GAP) - Math.abs(dx), oy = (BH + GAP) - Math.abs(dy);
        if (ox > 0 && oy > 0) {{
          if (ox < oy) {{ const s = (dx >= 0 ? 1 : -1) * ox / 2; a.x -= s; b.x += s; }}
          else {{ const s = (dy >= 0 ? 1 : -1) * oy / 2; a.y -= s; b.y += s; }}
        }}
      }}
      obstacles.forEach(o => push(a, o.w, o.h, o.cx, o.cy));
      if (pull) {{                       // 앵커로 당겨 연결선을 짧게 유지
        a.x += (a.ax - a.x) * pull;
        a.y += (a.ay - 15 - a.y) * pull;
      }}
      a.x = Math.min(VB.w - BW / 2 - 2, Math.max(BW / 2 + 2, a.x));
      a.y = Math.min(VB.h - BH / 2 - 2, Math.max(BH / 2 + 2, a.y));
    }}
  }};
  for (let it = 0; it < 400; it++) step(0.05);   // 1차: 실제 위치 쪽으로 수렴
  for (let it = 0; it < 400; it++) step(0);      // 2차: 당김 없이 겹침만 해소
  BADGES.forEach(b => {{ b.x = Math.round(b.x * 10) / 10; b.y = Math.round(b.y * 10) / 10; }});
}}

/* 1단계 — 도시 이름을 먼저 그린다. 실제 bbox를 재서 배지 배치의 장애물로 쓴다. */
function drawCities() {{
  document.getElementById("cities").innerHTML = ORDER.map(c =>
    `<text class="cityname" data-city="${{esc(c)}}" x="${{CITY[c].x}}" y="${{CITY[c].y}}"
      text-anchor="middle" tabindex="0" role="button"
      aria-label="${{esc(CITY[c].라벨)}} 도시 전체 보기">${{esc(CITY[c].라벨)}}</text>`).join("");
  document.querySelectorAll(".cityname").forEach(el => {{
    const go = () => showCity(el.dataset.city);
    el.addEventListener("click", go);
    el.addEventListener("keydown", e => {{
      if (e.key === "Enter" || e.key === " ") {{ e.preventDefault(); go(); }}
    }});
  }});
  return [...document.querySelectorAll(".cityname")].map(t => {{
    const b = t.getBBox();
    return {{cx: b.x + b.width / 2, cy: b.y + b.height / 2, w: b.width, h: b.height}};
  }});
}}

/* 2단계 — 배지와 연결선 */
function drawBadges() {{
  document.getElementById("leads").innerHTML = BADGES.map(b =>
    `<g><line class="lead" x1="${{b.ax}}" y1="${{b.ay}}" x2="${{b.x}}" y2="${{b.y}}"></line>
     <circle class="anchor" cx="${{b.ax}}" cy="${{b.ay}}" r="2.6"></circle></g>`).join("");

  document.getElementById("badges").innerHTML = BADGES.map(b => {{
    const x = b.x - BW / 2, y = b.y - BH / 2;
    /* 로고가 있으면 흰 바탕 + 로고. 투명 배경 로고도 밝은 지도 위에서 읽힌다. */
    const body = b.로고
      ? `<rect x="${{x}}" y="${{y}}" width="${{BW}}" height="${{BH}}"
           fill="#ffffff" stroke="${{b.색}}"></rect>
         <image href="${{esc(b.로고)}}" x="${{x + 2}}" y="${{y + 2}}"
           width="${{BW - 4}}" height="${{BH - 4}}" preserveAspectRatio="xMidYMid meet"></image>`
      : `<rect x="${{x}}" y="${{y}}" width="${{BW}}" height="${{BH}}"
           fill="${{b.색}}" stroke="${{b.테두리}}"></rect>
         <text x="${{b.x}}" y="${{b.y - 1}}" fill="${{b.글자색}}">${{esc(b.코드)}}</text>
         <text class="lgl" x="${{b.x}}" y="${{b.y + 10}}" fill="${{b.글자색}}">${{esc(b.리그)}}</text>`;
    return `<g class="badge" data-team="${{esc(b.구단명)}}" tabindex="0" role="button"
      aria-label="${{esc(b.구단명)}} ${{esc(b.리그)}} — 상세 보기">
      <title>${{esc(b.구단명)}} (${{esc(b.리그)}}) · ${{esc(b.구장)}}</title>
      ${{body}}</g>`;
  }}).join("");

  document.querySelectorAll(".badge").forEach(el => {{
    const go = () => showTeam(el.dataset.team);
    el.addEventListener("click", go);
    el.addEventListener("keydown", e => {{
      if (e.key === "Enter" || e.key === " ") {{ e.preventDefault(); go(); }}
    }});
  }});
}}

function legend() {{
  const used = new Set();
  DATA.forEach(t => active(t).forEach(s => used.add(s.업종)));
  document.getElementById("legend").innerHTML = Object.keys(COLOR).filter(k => used.has(k))
    .map(k => `<span style="--c:${{COLOR[k]}}">${{esc(k)}}</span>`).join("");
}}

/* 목록 타일·상세 헤더의 표식. 로고가 있으면 로고, 없으면 색+약칭. */
const mark = (b, cls) => b.로고
  ? `<span class="${{cls}} lg-img" style="border-color:${{b.색}}"><img src="${{esc(b.로고)}}"
      alt="${{esc(b.구단명)}} 로고"></span>`
  : `<span class="${{cls}}" style="background:${{b.색}};color:${{b.글자색}};
      border-color:${{b.테두리}}">${{esc(b.코드)}}</span>`;

function sponsorHTML(s) {{
  const rows = [["계약", s.계약.내용], ["금액", s.계약.금액], ["노출 영역", s.노출영역],
                ["하는 일", s.하는일], ["팬 접점", s.팬접점], ["출처", s.계약.출처]];
  return `<div class="sp${{s.상태 === "종료" ? " end" : ""}}">
    <div class="r1"><span class="co">${{esc(s.기업명)}}</span>${{chip(s.업종)}}${{grade(s.계약.공개등급)}}
      ${{s.한국기업 ? '<span class="kr">한국 기업</span>' : ""}}
      ${{s.비고 ? `<span class="nt">${{esc(s.비고)}}</span>` : ""}}
      ${{s.상태 === "종료" ? '<span class="gr g3">종료</span>' : ""}}</div>
    <dl>${{rows.map(([k, v]) => `<dt>${{esc(k)}}</dt><dd>${{esc(v)}}</dd>`).join("")}}</dl></div>`;
}}

function teamHTML(t) {{
  const nr = namingRights(t), b = badge(t.구단명), sh = sameVenue(t);
  return `<div class="team"><div class="th">
    <div class="r1">${{mark(b, "mk")}}<span class="nm">${{esc(t.구단명)}}</span>
      <span class="lg">${{esc(t.리그)}}</span>
      ${{t.기준시점예외 ? `<span class="ex">기준 예외 · ${{esc(t.기준시점예외)}}</span>` : ""}}</div>
    <div class="meta">${{esc(t.연고지)}} · 창단 ${{esc(t.창단연도)}} · 구단주 ${{esc(t.구단주)}}</div>
    <div class="meta">홈구장 <b>${{esc(t.홈구장)}}</b>${{t.각주 ? ` (각주 1–${{t.각주.length}})` : ""}}</div>
    ${{nr ? `<div class="nr">네이밍 라이츠 — ${{esc(nr.기업명)}} · ${{esc(nr.계약.금액)}}</div>`
          : '<div class="nr" style="color:#78716c">네이밍 라이츠 없음</div>'}}
    ${{sh.length ? `<div class="share">같은 구장 사용 — ${{sh.map(x => esc(x.구단명) + "(" + esc(x.리그) + ")").join(", ")}}</div>` : ""}}
    <div class="meta">유니폼 광고 — ${{esc(t.유니폼패치)}}</div>
    ${{t.구장비고 ? `<div class="meta" style="color:#78716c">${{esc(t.구장비고)}}</div>` : ""}}
  </div><div class="tb">
    ${{t.스폰서.map(sponsorHTML).join("")}}
    <div class="pt"><b>생활 밀접 포인트</b>${{esc(t.생활밀접포인트)}}</div>
    ${{t.각주 ? `<div class="fn"><b>각주</b><ol>${{t.각주.map(x => `<li>${{esc(x)}}</li>`).join("")}}</ol>
      ${{t.각주출처 ? `<p class="s">출처 — ${{esc(t.각주출처)}}</p>` : ""}}</div>` : ""}}
  </div></div>`;
}}

const tile = t => {{
  const b = badge(t.구단명);
  return `<button class="tile" data-team="${{esc(t.구단명)}}">${{mark(b, "mk")}}
    <span><span class="tn">${{esc(t.구단명)}}</span><br>
    <span class="tl">${{esc(t.리그)}} · ${{esc(t.홈구장)}}</span></span></button>`;
}};

function wire() {{
  document.querySelectorAll("#panel .tile").forEach(el =>
    el.addEventListener("click", () => showTeam(el.dataset.team)));
  const back = document.getElementById("back");
  if (back) back.addEventListener("click", overview);
}}
const highlight = names => document.querySelectorAll(".badge")
  .forEach(el => el.classList.toggle("on", names.includes(el.dataset.team)));

function overview() {{
  highlight([]);
  const act = DATA.flatMap(active);
  const stad = new Set(DATA.map(t => t.홈구장));
  const named = new Set(DATA.filter(namingRights).map(t => t.홈구장));
  const ind = {{}};
  act.forEach(s => ind[s.업종] = (ind[s.업종] || 0) + 1);
  const top = Object.entries(ind).sort((a, b) => b[1] - a[1]).slice(0, 3);
  document.getElementById("panel").innerHTML = `
    <div class="ph"><h2>텍사스 권역 전체</h2><span class="c">지도 배지 또는 아래 목록에서 구단을 선택하세요</span></div>
    <div class="ov">
      <div><b>${{DATA.length}}</b><span>구단</span></div>
      <div><b>${{act.length}}</b><span>활성 스폰서</span></div>
      <div><b>${{named.size}}/${{stad.size}}</b><span>기업명 구장</span></div>
      <div><b>${{ORDER.length}}</b><span>도시</span></div>
    </div>
    <p style="font-size:13px;color:#a8a29e">업종 상위 — ${{top.map(([k, v]) => `${{esc(k)}} ${{v}}건`).join(" · ")}}.
    기업명이 없는 구장은 ${{stad.size - named.size === 0 ? "없습니다" : (stad.size - named.size) + "곳입니다"}}.</p>
    <p style="font-size:12.5px;color:#78716c">${{esc(ASOF.예외 || "")}}</p>
    ${{ORDER.map(c => `<div class="citygrp"><h3>${{esc(LABEL[c])}}
      <span>${{byCity(c).length}}개 구단</span></h3>
      <div class="tiles">${{byCity(c).map(tile).join("")}}</div></div>`).join("")}}
    <p class="foot">데이터 원본: 데이터.json · 이 페이지는 대시보드생성.py로 생성됩니다.</p>`;
  wire();
}}

function showCity(c) {{
  const ts = byCity(c);
  highlight(ts.map(t => t.구단명));
  document.getElementById("panel").innerHTML = `
    <div class="ph"><h2>${{esc(LABEL[c])}}</h2>
      <span class="c">구단 ${{ts.length}}개 · 활성 스폰서 ${{ts.flatMap(active).length}}건</span>
      <button class="btn" id="back">전체 보기</button></div>
    <div class="tiles" style="margin:13px 0">${{ts.map(tile).join("")}}</div>
    ${{ts.map(teamHTML).join("")}}
    <p class="foot">데이터 원본: 데이터.json</p>`;
  wire();
  document.getElementById("panel").scrollIntoView({{block: "start", behavior: "smooth"}});
}}

function showTeam(name) {{
  const t = team(name);
  if (!t) return;
  highlight([name]);
  const 형제 = byCity(t.도시).filter(x => x.구단명 !== name);
  document.getElementById("panel").innerHTML = `
    <div class="ph"><h2>${{esc(t.구단명)}}</h2>
      <span class="c">${{esc(t.리그)}} · ${{esc(LABEL[t.도시])}}</span>
      <button class="btn" id="back">전체 보기</button></div>
    ${{teamHTML(t)}}
    ${{형제.length ? `<div class="citygrp"><h3>같은 도시 다른 구단
      <span>${{형제.length}}개</span></h3><div class="tiles">${{형제.map(tile).join("")}}</div></div>` : ""}}
    <p class="foot">데이터 원본: 데이터.json</p>`;
  wire();
  document.getElementById("panel").scrollIntoView({{block: "start", behavior: "smooth"}});
}}

layout(drawCities()); drawBadges(); legend(); overview();
</script></body></html>"""

    io.open(OUT, "w", encoding="utf-8").write(html)
    print("generated: %s (%d badges / %d cities)" % (OUT, len(배지), len(도시순서)))
    print("logo: %d/%d embedded" % (len(로고찾음), len(배지)))
    if 로고찾음:
        print("  found   : %s" % ", ".join(sorted(로고찾음)))
    if 로고없음:
        print("  fallback: %s" % ", ".join(sorted(로고없음)))
        print("  -> put files in ./%s/ named <CODE>%s (e.g. %s.png)"
              % (로고폴더, "|".join(로고확장자), 로고없음[0]))


if __name__ == "__main__":
    main()
