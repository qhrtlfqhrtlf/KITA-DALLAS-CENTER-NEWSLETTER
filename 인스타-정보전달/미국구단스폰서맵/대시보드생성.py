# -*- coding: utf-8 -*-
"""데이터.json을 읽어 인터랙티브 단일 HTML 대시보드를 생성한다.

- 외부 CDN·폰트·이미지를 일절 쓰지 않는다 (단일 파일 자체 완결).
- file:// 에서 fetch는 CORS로 막히므로 데이터를 <script>에 인라인으로 박는다.
- 지도는 실제 경위도를 등장방형 투영으로 그린다. 외곽선과 도시 핀이 같은
  투영식을 쓰므로 핀 위치가 외곽선과 어긋나지 않는다.
- Phase 2(미국 전도) 확장 시 REGION에 항목을 추가하기만 하면
  카드 렌더링 로직은 그대로 재사용된다.

실행: python 대시보드생성.py
출력: 대시보드.html
"""
import io
import json

SRC = "데이터.json"
OUT = "대시보드.html"

# 정본 팔레트는 보고서(밝은 배경)와 동일하게 유지한다.
업종색 = {
    "에너지": "#b45309", "기술·IT": "#4338ca", "헬스케어": "#0f766e",
    "금융": "#1d4ed8", "자동차": "#b91c1c", "식음료": "#a16207",
    "유통·이커머스": "#7c2d92", "건설·설비": "#57534e", "항공": "#0369a1",
    "통신": "#9333ea", "보험": "#065f46", "기타": "#525252",
}

# 대시보드는 어두운 배경이라 어두운 색이 묻힌다. 색을 손으로 다시 고르지 않고
# 상대 휘도를 계산해 기준 미달인 색만 흰색 쪽으로 자동 보정한다.
휘도최소 = 0.30


def _휘도(rgb):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (c(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def 다크보정(hex색):
    rgb = [int(hex색[i:i + 2], 16) for i in (1, 3, 5)]
    for _ in range(60):
        if _휘도(rgb) >= 휘도최소:
            break
        rgb = [min(255, round(v + (255 - v) * 0.08)) for v in rgb]
    return "#%02x%02x%02x" % tuple(rgb)


업종색다크 = {k: 다크보정(v) for k, v in 업종색.items()}

# 텍사스 외곽선 — (경도, 위도). 팬핸들 북서쪽에서 시계방향.
TEXAS = [
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

# 도시 좌표 — 데이터.json의 "도시" 값과 키가 일치해야 한다.
도시좌표 = {
    "DFW": (-96.90, 32.78),
    "휴스턴": (-95.37, 29.76),
    "샌안토니오": (-98.49, 29.42),
    "오스틴": (-97.74, 30.27),
}
도시라벨 = {
    "DFW": "댈러스-포트워스",
    "휴스턴": "휴스턴",
    "샌안토니오": "샌안토니오",
    "오스틴": "오스틴",
}
도시순서 = ["DFW", "휴스턴", "샌안토니오", "오스틴"]

W, H, PAD = 560, 520, 26


def 투영(구역):
    """경위도 → SVG 좌표 변환 함수와 투영된 외곽선을 돌려준다."""
    lons = [p[0] for p in 구역]
    lats = [p[1] for p in 구역]
    lo0, lo1, la0, la1 = min(lons), max(lons), min(lats), max(lats)
    sx = (W - PAD * 2) / (lo1 - lo0)
    sy = (H - PAD * 2) / (la1 - la0)
    s = min(sx, sy)                       # 종횡비 유지
    ox = PAD + ((W - PAD * 2) - (lo1 - lo0) * s) / 2
    oy = PAD + ((H - PAD * 2) - (la1 - la0) * s) / 2

    def f(lon, lat):
        return (round(ox + (lon - lo0) * s, 1),
                round(oy + (la1 - lat) * s, 1))
    return f, [f(*p) for p in 구역]


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    구단들 = d["구단"]
    기준 = d["메타"].get("기준시점", {})

    f, outline = 투영(TEXAS)
    path = "M" + " L".join(f"{x},{y}" for x, y in outline) + " Z"
    핀 = {c: f(*도시좌표[c]) for c in 도시순서}

    # 데이터·설정을 JS로 인라인. </script> 조기 종료 방지를 위해 < 를 이스케이프.
    def js(obj):
        return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")

    지도설정 = {
        "이름": "텍사스 권역",
        "path": path,
        "viewBox": f"0 0 {W} {H}",
        "핀": {c: {"x": 핀[c][0], "y": 핀[c][1], "라벨": 도시라벨[c]} for c in 도시순서},
        "도시순서": 도시순서,
    }

    html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>미국 구단·스폰서 지도 — 텍사스 권역 대시보드</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:"Malgun Gothic","맑은 고딕",-apple-system,"Segoe UI",sans-serif;
  background:#0c0a09;color:#e7e5e4;line-height:1.65;font-size:15px}}
.top{{padding:20px 26px 16px;border-bottom:1px solid #292524}}
h1{{margin:0;font-size:19px;letter-spacing:-.01em}}
.top .sub{{color:#a8a29e;font-size:12.5px;margin-top:5px}}
.asof{{display:inline-block;margin-top:9px;font-size:11.5px;color:#c4b5fd;
  background:#2e1065;border:1px solid #4c1d95;border-radius:5px;padding:4px 10px}}
.layout{{display:grid;grid-template-columns:minmax(340px,560px) minmax(0,1fr);
  gap:0;align-items:start}}
/* 지도 */
.mapwrap{{padding:18px 22px 26px;border-right:1px solid #292524;position:sticky;top:0}}
svg{{width:100%;height:auto;display:block;overflow:visible}}
.state{{fill:#1c1917;stroke:#57534e;stroke-width:1.4}}
.pin{{cursor:pointer}}
.pin circle.hit{{fill:transparent}}
.pin circle.dot{{fill:#f59e0b;stroke:#0c0a09;stroke-width:2.5;transition:r .12s}}
.pin text{{fill:#e7e5e4;font-size:12px;font-weight:700;paint-order:stroke;
  stroke:#0c0a09;stroke-width:3.5px;pointer-events:none}}
.pin text.cnt{{fill:#0c0a09;stroke:none;font-size:11px;text-anchor:middle}}
.pin:hover circle.dot,.pin:focus-visible circle.dot{{fill:#fbbf24}}
.pin.on circle.dot{{fill:#fff}}
.pin:focus-visible{{outline:none}}
.pin:focus-visible circle.dot{{stroke:#fbbf24;stroke-width:3}}
.legend{{margin-top:14px;display:flex;flex-wrap:wrap;gap:5px}}
.legend span{{font-size:10.5px;padding:2px 7px;border-radius:3px;color:var(--c);
  background:color-mix(in srgb,var(--c) 20%,#0c0a09);border:1px solid color-mix(in srgb,var(--c) 45%,#0c0a09)}}
.hint{{font-size:11.5px;color:#78716c;margin-top:12px}}
/* 패널 */
.panel{{padding:18px 26px 60px;min-width:0}}
.ph{{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
  padding-bottom:10px;border-bottom:1px solid #292524;margin-bottom:4px}}
.ph h2{{margin:0;font-size:17px}}
.ph .c{{font-size:12px;color:#a8a29e}}
.ov{{display:grid;grid-template-columns:repeat(auto-fit,minmax(115px,1fr));gap:9px;margin:16px 0 20px}}
.ov div{{background:#1c1917;border:1px solid #292524;border-radius:7px;padding:11px 13px}}
.ov b{{display:block;font-size:20px}}
.ov span{{font-size:11px;color:#a8a29e}}
.team{{border:1px solid #292524;border-radius:9px;margin:14px 0;overflow:hidden;background:#141210}}
.th{{padding:12px 16px;background:#1c1917;border-bottom:1px solid #292524}}
.th .r1{{display:flex;flex-wrap:wrap;align-items:center;gap:8px}}
.th .nm{{font-size:15px;font-weight:700}}
.th .lg{{font-size:10px;font-weight:700;background:#e7e5e4;color:#0c0a09;padding:2px 7px;border-radius:3px}}
.th .ex{{font-size:10px;font-weight:700;background:#4c1d95;color:#ddd6fe;padding:2px 7px;border-radius:3px}}
.th .meta{{font-size:12px;color:#a8a29e;margin-top:5px}}
.th .meta b{{color:#e7e5e4}}
.nr{{font-size:12px;color:#fbbf24;margin-top:4px}}
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
.foot{{margin-top:26px;padding-top:14px;border-top:1px solid #292524;font-size:11.5px;color:#57534e}}
@media(max-width:900px){{.layout{{grid-template-columns:1fr}}
  .mapwrap{{position:static;border-right:none;border-bottom:1px solid #292524}}
  .panel{{padding:18px 20px 50px}}}}
</style></head><body>
<div class="top">
<h1>미국 구단·스폰서 지도 — 텍사스 권역</h1>
<p class="sub">도시 핀을 클릭하면 해당 도시 구단과 스폰서가 표시됩니다 · 한국무역협회 달러스지부</p>
<p class="asof"><b>기준 시점</b> {기준.get("기준", "")}</p>
</div>
<div class="layout">
<div class="mapwrap">
  <svg id="map" viewBox="{지도설정['viewBox']}" role="group" aria-label="텍사스 권역 지도">
    <path class="state" d="{path}"></path>
    <g id="pins"></g>
  </svg>
  <div class="legend" id="legend"></div>
  <p class="hint">기업 로고는 상표권 문제로 사용하지 않고 업종 색상 배지로 표시합니다.</p>
</div>
<div class="panel" id="panel"></div>
</div>
<script>
const DATA = {js(구단들)};
const MAP = {js(지도설정)};
const COLOR = {js(업종색다크)};
const ASOF = {js(기준)};
const LABEL = {js(도시라벨)};

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}})[c]);
const active = t => t.스폰서.filter(s => s.상태 !== "종료");
const byCity = c => DATA.filter(t => t.도시 === c);
const chip = i => `<span class="chip" style="--c:${{COLOR[i] || "#525252"}}">${{esc(i)}}</span>`;
const grade = g => `<span class="gr ${{ {{"공식 발표":"g1","언론 보도":"g2"}}[g] || "g3" }}">${{esc(g)}}</span>`;

/* 네이밍 라이츠 판정은 보고서생성.py와 동일 기준(노출영역에 "구장 명칭")을 쓴다. */
const namingRights = t => active(t).find(s => (s.노출영역 || "").includes("구장 명칭"));

function legend() {{
  const used = new Set();
  DATA.forEach(t => active(t).forEach(s => used.add(s.업종)));
  document.getElementById("legend").innerHTML =
    Object.keys(COLOR).filter(k => used.has(k))
      .map(k => `<span style="--c:${{COLOR[k]}}">${{esc(k)}}</span>`).join("");
}}

function pins() {{
  const g = document.getElementById("pins");
  g.innerHTML = MAP.도시순서.map(c => {{
    const p = MAP.핀[c], n = byCity(c).length;
    const r = 9 + n * 1.7;
    const anchor = (c === "샌안토니오") ? "end" : "start";
    const dx = anchor === "end" ? -(r + 6) : (r + 6);
    return `<g class="pin" data-city="${{esc(c)}}" tabindex="0" role="button"
      aria-label="${{esc(p.라벨)}} — 구단 ${{n}}개">
      <circle class="hit" cx="${{p.x}}" cy="${{p.y}}" r="${{r + 14}}"></circle>
      <circle class="dot" cx="${{p.x}}" cy="${{p.y}}" r="${{r}}"></circle>
      <text class="cnt" x="${{p.x}}" y="${{p.y + 4}}">${{n}}</text>
      <text x="${{p.x + dx}}" y="${{p.y + 4}}" text-anchor="${{anchor}}">${{esc(p.라벨)}}</text>
    </g>`;
  }}).join("");
  g.querySelectorAll(".pin").forEach(el => {{
    const go = () => select(el.dataset.city);
    el.addEventListener("click", go);
    el.addEventListener("keydown", e => {{
      if (e.key === "Enter" || e.key === " ") {{ e.preventDefault(); go(); }}
    }});
  }});
}}

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
  const nr = namingRights(t);
  return `<div class="team"><div class="th">
    <div class="r1"><span class="nm">${{esc(t.구단명)}}</span><span class="lg">${{esc(t.리그)}}</span>
      ${{t.기준시점예외 ? `<span class="ex">기준 예외 · ${{esc(t.기준시점예외)}}</span>` : ""}}</div>
    <div class="meta">${{esc(t.연고지)}} · 창단 ${{esc(t.창단연도)}} · 구단주 ${{esc(t.구단주)}}</div>
    <div class="meta">홈구장 <b>${{esc(t.홈구장)}}</b>${{t.각주 ? ` (각주 1–${{t.각주.length}})` : ""}}</div>
    ${{nr ? `<div class="nr">네이밍 라이츠 — ${{esc(nr.기업명)}} · ${{esc(nr.계약.금액)}}</div>`
          : '<div class="nr" style="color:#78716c">네이밍 라이츠 없음</div>'}}
    <div class="meta">유니폼 광고 — ${{esc(t.유니폼패치)}}</div>
    ${{t.구장비고 ? `<div class="meta" style="color:#78716c">${{esc(t.구장비고)}}</div>` : ""}}
  </div><div class="tb">
    ${{t.스폰서.map(sponsorHTML).join("")}}
    <div class="pt"><b>생활 밀접 포인트</b>${{esc(t.생활밀접포인트)}}</div>
    ${{t.각주 ? `<div class="fn"><b>각주</b><ol>${{t.각주.map(x => `<li>${{esc(x)}}</li>`).join("")}}</ol>
      ${{t.각주출처 ? `<p class="s">출처 — ${{esc(t.각주출처)}}</p>` : ""}}</div>` : ""}}
  </div></div>`;
}}

function overview() {{
  const act = DATA.flatMap(active);
  const stad = new Set(DATA.map(t => t.홈구장));
  const named = new Set(DATA.filter(namingRights).map(t => t.홈구장));
  const ind = {{}};
  act.forEach(s => ind[s.업종] = (ind[s.업종] || 0) + 1);
  const top = Object.entries(ind).sort((a, b) => b[1] - a[1]).slice(0, 3);
  document.getElementById("panel").innerHTML = `
    <div class="ph"><h2>텍사스 권역 전체</h2><span class="c">지도에서 도시를 선택하세요</span></div>
    <div class="ov">
      <div><b>${{DATA.length}}</b><span>구단</span></div>
      <div><b>${{act.length}}</b><span>활성 스폰서</span></div>
      <div><b>${{named.size}}/${{stad.size}}</b><span>기업명 구장</span></div>
      <div><b>${{MAP.도시순서.length}}</b><span>도시</span></div>
    </div>
    <p style="font-size:13px;color:#a8a29e">업종 상위 — ${{top.map(([k, v]) => `${{esc(k)}} ${{v}}건`).join(" · ")}}.
    기업명이 없는 구장은 ${{stad.size - named.size === 0 ? "없습니다" : (stad.size - named.size) + "곳입니다"}}.</p>
    <p style="font-size:12.5px;color:#78716c">${{esc(ASOF.예외 || "")}}</p>
    ${{MAP.도시순서.map(c => {{
      const ts = byCity(c);
      return `<div class="team"><div class="th"><div class="r1">
        <span class="nm">${{esc(LABEL[c])}}</span><span class="lg">${{ts.length}}개 구단</span></div>
        <div class="meta">${{ts.map(t => esc(t.구단명) + "(" + esc(t.리그) + ")").join(", ")}}</div>
      </div></div>`;
    }}).join("")}}
    <p class="foot">데이터 원본: 데이터.json · 이 페이지는 대시보드생성.py로 생성됩니다.</p>`;
}}

function select(city) {{
  document.querySelectorAll(".pin").forEach(p => p.classList.toggle("on", p.dataset.city === city));
  const ts = byCity(city);
  const act = ts.flatMap(active);
  document.getElementById("panel").innerHTML = `
    <div class="ph"><h2>${{esc(LABEL[city])}}</h2>
      <span class="c">구단 ${{ts.length}}개 · 활성 스폰서 ${{act.length}}건</span>
      <button id="back" style="margin-left:auto;font:inherit;font-size:12px;cursor:pointer;
        background:#1c1917;color:#e7e5e4;border:1px solid #44403c;border-radius:5px;padding:4px 11px">
        전체 보기</button></div>
    ${{ts.map(teamHTML).join("")}}
    <p class="foot">데이터 원본: 데이터.json</p>`;
  document.getElementById("back").addEventListener("click", () => {{
    document.querySelectorAll(".pin").forEach(p => p.classList.remove("on"));
    overview();
  }});
  document.getElementById("panel").scrollIntoView({{block: "start", behavior: "smooth"}});
}}

legend(); pins(); overview();
</script></body></html>"""

    io.open(OUT, "w", encoding="utf-8").write(html)
    print("generated: %s (%d teams, %d cities)" % (OUT, len(구단들), len(도시순서)))


if __name__ == "__main__":
    main()
