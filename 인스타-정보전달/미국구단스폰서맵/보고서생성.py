# -*- coding: utf-8 -*-
"""데이터.json을 읽어 보기 편한 단일 HTML 보고서를 생성한다.

데이터가 바뀌면 이 스크립트를 다시 실행하면 된다 (표·집계는 전부 JSON에서 계산).
서술 섹션(리그별 광고 지면 해설, 콘텐츠 후보, 미확인 항목)은 이 파일 안에 텍스트로 보관한다.

실행: python 보고서생성.py
출력: 조사보고서.html
"""
import io
import json
import collections
from html import escape

SRC = "데이터.json"
OUT = "조사보고서.html"

# 업종별 색상 — 대시보드에서도 동일 팔레트를 재사용할 것
업종색 = {
    "에너지": "#b45309", "기술·IT": "#4338ca", "헬스케어": "#0f766e",
    "금융": "#1d4ed8", "자동차": "#b91c1c", "식음료": "#a16207",
    "유통·이커머스": "#7c2d92", "건설·설비": "#57534e", "항공": "#0369a1",
    "통신": "#9333ea", "보험": "#065f46", "기타": "#525252",
}

도시순서 = ["DFW", "휴스턴", "샌안토니오", "오스틴"]


def 등급배지(g):
    cls = {"공식 발표": "g-off", "언론 보도": "g-press", "미공개": "g-none"}.get(g, "g-none")
    return f'<span class="badge {cls}">{escape(g)}</span>'


def 업종배지(업종):
    c = 업종색.get(업종, "#525252")
    return f'<span class="chip" style="--c:{c}">{escape(업종)}</span>'


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    구단들 = d["구단"]

    # ---- 집계 (전부 JSON에서 계산) ----
    활성 = []
    for t in 구단들:
        for s in t["스폰서"]:
            if s.get("상태") != "종료":
                활성.append((t, s))

    업종카운트 = collections.Counter(s["업종"] for _, s in 활성)
    등급카운트 = collections.Counter(s["계약"]["공개등급"] for _, s in 활성)
    도시카운트 = collections.Counter(t["도시"] for t in 구단들)
    한국기업 = [(t, s) for t, s in 활성 if s.get("한국기업")]
    종료수 = sum(1 for t in 구단들 for s in t["스폰서"] if s.get("상태") == "종료")

    업종사례 = collections.defaultdict(list)
    for _, s in 활성:
        업종사례[s["업종"]].append(s["기업명"])

    P = []
    A = P.append

    # ================= HEAD =================
    A("""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>미국 구단·스폰서 지도 — Phase 1 조사보고서 (텍사스 권역)</title>
<style>
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:"Malgun Gothic","맑은 고딕",-apple-system,"Segoe UI",sans-serif;
  color:#1c1917;background:#f5f5f4;line-height:1.7;font-size:15px}
.wrap{display:grid;grid-template-columns:220px minmax(0,1fr);gap:0;max-width:1180px;margin:0 auto;
  background:#fff;min-height:100vh;box-shadow:0 0 40px rgba(0,0,0,.06)}
/* 목차 */
nav{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;padding:28px 18px;
  border-right:1px solid #e7e5e4;background:#fafaf9;font-size:13px}
nav .navttl{font-size:11px;letter-spacing:.08em;color:#78716c;margin:0 0 12px;font-weight:700}
nav a{display:block;padding:6px 8px;color:#44403c;text-decoration:none;border-radius:5px;margin-bottom:1px}
nav a:hover{background:#e7e5e4;color:#0c0a09}
main{padding:44px 48px 90px;min-width:0}
/* 헤더 */
header{border-bottom:3px solid #1c1917;padding-bottom:22px;margin-bottom:34px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.01em;line-height:1.35}
.sub{color:#78716c;font-size:13px}
.kpis{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.kpi{background:#fafaf9;border:1px solid #e7e5e4;border-radius:7px;padding:10px 15px;min-width:96px}
.kpi b{display:block;font-size:21px;line-height:1.25}
.kpi span{font-size:11px;color:#78716c}
h2{font-size:19px;margin:52px 0 14px;padding-bottom:8px;border-bottom:1px solid #e7e5e4;scroll-margin-top:20px}
h3{font-size:15px;margin:26px 0 9px}
h4{font-size:14px;margin:18px 0 6px;color:#44403c}
p{margin:9px 0}
/* 표 */
.scroll{overflow-x:auto;margin:14px 0;border:1px solid #e7e5e4;border-radius:7px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:560px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #f0efee;vertical-align:top}
th{background:#fafaf9;font-weight:700;font-size:11px;letter-spacing:.04em;color:#57534e;
  white-space:nowrap;position:sticky;top:0}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fdfdfc}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
/* 배지 */
.badge{display:inline-block;font-size:10px;padding:2px 7px;border-radius:20px;white-space:nowrap;font-weight:700}
.g-off{background:#dcfce7;color:#14532d}
.g-press{background:#fef3c7;color:#78350f}
.g-none{background:#f5f5f4;color:#57534e}
.chip{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;white-space:nowrap;
  color:var(--c);background:color-mix(in srgb,var(--c) 11%,#fff);border:1px solid color-mix(in srgb,var(--c) 26%,#fff)}
.flag{display:inline-block;font-size:10px;padding:2px 6px;border-radius:3px;background:#1c1917;color:#fff;font-weight:700}
/* 구단 카드 */
.city{margin:36px 0 0}
.cityhd{display:flex;align-items:baseline;gap:10px;margin:0 0 4px}
.cityhd h3{margin:0;font-size:17px}
.cityhd .c{font-size:12px;color:#78716c}
.team{border:1px solid #e7e5e4;border-radius:9px;margin:16px 0;overflow:hidden}
.teamhd{background:#fafaf9;padding:13px 17px;border-bottom:1px solid #e7e5e4}
.teamhd .t1{display:flex;flex-wrap:wrap;align-items:baseline;gap:9px}
.teamhd .nm{font-size:15px;font-weight:700}
.teamhd .lg{font-size:10px;font-weight:700;background:#1c1917;color:#fff;padding:2px 7px;border-radius:3px}
.teamhd .meta{font-size:12px;color:#57534e;margin-top:5px}
.note{font-size:12px;color:#78716c;margin-top:5px;padding-left:10px;border-left:2px solid #e7e5e4}
.teambd{padding:4px 17px 15px}
.sp{padding:13px 0;border-bottom:1px dashed #eeedec}
.sp:last-child{border-bottom:none}
.sp .h{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:6px}
.sp .co{font-weight:700;font-size:14px}
.sp dl{display:grid;grid-template-columns:88px minmax(0,1fr);gap:3px 12px;margin:6px 0 0;font-size:13px}
.sp dt{color:#78716c;font-size:11px;padding-top:3px}
.sp dd{margin:0}
.ended{opacity:.55}
/* 기준 시점 */
.asofbar{margin:16px 0 0;padding:9px 13px;background:#f5f3ff;border:1px solid #ddd6fe;
  border-radius:6px;font-size:12.5px;color:#4c1d95}
.asofbar b{font-size:10px;letter-spacing:.05em;margin-right:7px;text-transform:uppercase}
.asof{font-size:10px;font-weight:700;background:#4c1d95;color:#fff;padding:2px 7px;border-radius:3px}
/* 각주 */
.fn{margin-top:9px;padding:9px 13px;background:#fafaf9;border:1px solid #e7e5e4;border-radius:6px;font-size:12px}
.fn>b{font-size:10px;letter-spacing:.05em;color:#78716c;display:block;margin-bottom:5px}
.fn ol{margin:0;padding-left:20px}
.fn li{margin:3px 0;color:#44403c}
.fn .fnsrc{margin:7px 0 0;padding-top:6px;border-top:1px solid #eeedec;color:#78716c;font-size:11px}
sup.fnref{font-size:9.5px;font-weight:700;color:#4c1d95;background:#f5f3ff;border:1px solid #ddd6fe;
  padding:1px 5px;border-radius:3px;vertical-align:super;white-space:nowrap}
.pt{background:#fafaf9;border-left:3px solid #1c1917;padding:9px 13px;margin:13px 0 0;font-size:13px}
.pt b{font-size:10px;letter-spacing:.05em;color:#78716c;display:block;margin-bottom:2px}
/* 목록 */
ol.hooks{padding-left:0;list-style:none;counter-reset:h;margin:14px 0}
ol.hooks li{counter-increment:h;position:relative;padding:12px 0 12px 42px;border-bottom:1px solid #f0efee}
ol.hooks li:last-child{border-bottom:none}
ol.hooks li::before{content:counter(h);position:absolute;left:0;top:12px;width:25px;height:25px;
  background:#1c1917;color:#fff;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:700}
ol.hooks .t{font-weight:700;display:block;margin-bottom:3px}
ul.tight{margin:9px 0;padding-left:20px}
ul.tight li{margin:5px 0}
.warn{background:#fffbeb;border:1px solid #fde68a;border-radius:7px;padding:14px 17px;margin:14px 0;font-size:13px}
.warn b{color:#78350f}
.src{font-size:12px;color:#57534e}
.src p{margin:5px 0}
footer{margin-top:60px;padding-top:18px;border-top:1px solid #e7e5e4;font-size:12px;color:#a8a29e}
@media(max-width:860px){.wrap{grid-template-columns:1fr}nav{position:static;height:auto;border-right:none;
  border-bottom:1px solid #e7e5e4}main{padding:28px 20px 60px}th{position:static}}
@media print{body{background:#fff;font-size:10.5pt}.wrap{box-shadow:none;display:block;max-width:none}
  nav{display:none}main{padding:0}h2{page-break-after:avoid}.team,ol.hooks li{page-break-inside:avoid}
  .scroll{overflow:visible;border:1px solid #ccc}th{position:static}
  .fn{page-break-inside:avoid}.teamhd{page-break-after:avoid}
  .asofbar{border:1px solid #999;background:#fff}sup.fnref{background:#fff;border:1px solid #999}}
</style></head><body><div class="wrap">""")

    # ================= 목차 =================
    A('<nav><p class="navttl">목차</p>')
    for hid, label in [
        ("s1", "1. 조사 범위"), ("s2", "2. 구장 네이밍 라이츠"), ("s3", "3. 리그별 광고 지면"),
        ("s4", "4. 업종 분포"), ("s5", "5. 구단별 상세"), ("s6", "6. 콘텐츠 후보"),
        ("s7", "7. 한국 기업"), ("s8", "8. 미공개·미확인"), ("s9", "9. 출처"),
    ]:
        A(f'<a href="#{hid}">{label}</a>')
    A("</nav><main>")

    # ================= 헤더 =================
    기준 = d["메타"].get("기준시점", {})
    예외구단 = [t for t in 구단들 if t.get("기준시점예외")]
    A(f"""<header>
<h1>미국 구단·스폰서 지도<br>Phase 1 조사보고서 — 텍사스 권역</h1>
<p class="sub">작성일 2026-08-05 · 한국무역협회 달러스지부 · 인스타그램 정보전달 콘텐츠 기초 조사</p>
<p class="asofbar"><b>기준 시점</b> {escape(기준.get("기준", ""))}
{("· 예외 " + str(len(예외구단)) + "개 구단: " + escape(", ".join(t["구단명"] for t in 예외구단))) if 예외구단 else ""}</p>
<div class="kpis">
<div class="kpi"><b>{len(구단들)}</b><span>구단</span></div>
<div class="kpi"><b>{len(활성)}</b><span>활성 스폰서</span></div>
<div class="kpi"><b>{종료수}</b><span>종료 (참고)</span></div>
<div class="kpi"><b>{len(도시카운트)}</b><span>도시</span></div>
<div class="kpi"><b>{등급카운트.get('공식 발표',0)} / {등급카운트.get('언론 보도',0)}</b><span>공식 / 언론</span></div>
</div>
<p class="sub" style="margin-top:16px">모든 표와 집계는 <code>데이터.json</code>에서 자동 생성됩니다.
설계 근거: <code>docs/superpowers/specs/2026-08-05-미국구단스폰서맵-design.md</code></p>
</header>""")

    # ================= 1. 범위 =================
    A('<h2 id="s1">1. 조사 범위</h2>')
    A('<div class="scroll"><table><thead><tr><th>도시</th><th class="num">구단</th><th>구성</th></tr></thead><tbody>')
    for c in 도시순서:
        ts = [t for t in 구단들 if t["도시"] == c]
        names = ", ".join(f"{t['구단명']}({t['리그']})" for t in ts)
        A(f'<tr><td><b>{escape(c)}</b></td><td class="num">{len(ts)}</td><td>{escape(names)}</td></tr>')
    A("</tbody></table></div>")
    A("<p>텍사스에 4대 리그(NFL·NBA·MLB·NHL) 프랜차이즈는 8개가 전부다. "
      "MLS·WNBA·NWSL을 포함해야 샌안토니오·오스틴이 지도에서 빈 칸이 되지 않는다.</p>")

    A(f"""<h3>기준 시점</h3>
<p>{escape(기준.get("기준", ""))}. 구장명·스폰서 계약은 시점에 따라 바뀌므로 이 보고서를 인용할 때는 기준 시점을 함께 밝혀야 한다.</p>""")
    if 예외구단:
        A(f'<div class="warn"><b>기준이 혼재되는 구단 {len(예외구단)}개</b><ul class="tight" style="margin-bottom:0">')
        for t in 예외구단:
            A(f'<li><b>{escape(t["구단명"])}</b> — {escape(t["기준시점예외"])}. '
              f'{escape(기준.get("예외", ""))}</li>')
        A("</ul></div>")

    # ================= 2. 네이밍 라이츠 =================
    A('<h2 id="s2">2. 구장 네이밍 라이츠</h2>')
    # 네이밍 라이츠 판정: 노출영역에 "구장 명칭"이 있는 스폰서만.
    # 계약 내용의 "네이밍 라이츠" 문구로 판정하면 PNC Plaza(구장 외부 광장)나
    # Minute Maid(과거 보유·현재 미보유)까지 잘못 걸린다.
    구장 = {}
    for t in 구단들:
        for s in t["스폰서"]:
            if s.get("상태") == "종료":
                continue
            if "구장 명칭" not in s.get("노출영역", ""):
                continue
            key = t["홈구장"]
            구장.setdefault(key, {"기업": s["기업명"], "업종": s["업종"], "계약": s["계약"], "구단": []})
            if t["구단명"] not in 구장[key]["구단"]:      # 공용 구장 중복 방지
                구장[key]["구단"].append(t["구단명"])
    전체구장 = {t["홈구장"] for t in 구단들}
    A('<div class="scroll"><table><thead><tr><th>구장</th><th>사용 구단</th><th>기업</th><th>업종</th>'
      '<th>금액</th><th>계약</th><th>등급</th></tr></thead><tbody>')
    for 구장명, v in 구장.items():
        A(f'<tr><td><b>{escape(구장명)}</b></td><td>{escape(", ".join(v["구단"]))}</td>'
          f'<td>{escape(v["기업"])}</td><td>{업종배지(v["업종"])}</td>'
          f'<td>{escape(v["계약"]["금액"])}</td><td>{escape(v["계약"]["내용"][:70])}…</td>'
          f'<td>{등급배지(v["계약"]["공개등급"])}</td></tr>')
    A("</tbody></table></div>")
    ll = [v for v in 구장.values() if not v["계약"]["금액"].startswith("미공개")]
    press = sum(1 for v in ll if v["계약"]["공개등급"] == "언론 보도")

    # 기업명 없는 구장 / 공용 구장 — 전부 집계에서 뽑는다 (하드코딩 금지)
    무기업명 = sorted(전체구장 - set(구장))
    공용 = {k: v["구단"] for k, v in 구장.items() if len(v["구단"]) > 1}

    공용문 = ("".join(f' {escape(k)}는 {len(v)}개 구단({escape("·".join(v))})이 공유한다.'
                      for k, v in 공용.items()) if 공용 else "")

    if 무기업명:
        A(f'<p>권역 내 구장 {len(전체구장)}개 중 <b>{len(구장)}개가 기업명</b>을 달고 있다. '
          f'기업명이 없는 구장은 ' + ", ".join(f"<b>{escape(s)}</b>" for s in 무기업명)
          + f" {len(무기업명)}곳이다.</p>")
    else:
        A(f'<p>권역 내 <b>구장 {len(전체구장)}개 전부가 기업명</b>을 달고 있다 — 예외가 없다.</p>')
    A(f'<div class="warn"><b>금액 신뢰도</b> — 네이밍 라이츠 {len(구장)}건 중 금액이 확인된 것은 {len(ll)}건이고, '
      f'그중 {press}건이 <b>언론 보도</b> 등급이다. 구단·기업이 금액을 공식 발표한 사례는 이 권역에 없다.'
      f'{공용문}</div>')

    # ================= 3. 리그별 지면 =================
    A('<h2 id="s3">3. 리그별 광고 지면 — 리그가 자리를 정한다</h2>')
    A("<p>같은 도시, 같은 팬층이어도 유니폼에 광고를 붙일 수 있는 자리는 리그 규정이 결정한다.</p>")
    리그규정 = [
        ("NFL", "<b>없음</b> — 4대 리그 중 유일하게 유니폼 광고 불허"),
        ("NBA", "패치 1개(좌측 상단). 4대 리그 중 가장 보수적"),
        ("NHL", "어깨 패치 + 헬멧. <b>홈·원정 광고주를 따로 판다</b>"),
        ("MLB", "소매 패치(2023 시즌부터). 투수·타자 자세에서 카메라에 가장 잘 걸리는 위치"),
        ("MLS", "최대 <b>4개</b>(가슴·좌소매·우소매·등하단). 2026 올스타 브레이크 이후 등하단 신설, 가슴 로고의 80% 크기"),
        ("WNBA", "복부 — NBA와 위치가 다름"),
    ]
    A('<div class="scroll"><table><thead><tr><th>리그</th><th>광고 지면</th>'
      '<th>텍사스 권역 사례</th></tr></thead><tbody>')
    for lg, rule in 리그규정:
        사례 = [f"{t['구단명'].replace('Houston ','').replace('Dallas ','').replace('San Antonio ','')}={t['유니폼패치']}"
                for t in 구단들 if t["리그"] == lg]
        사례 = [x for x in 사례 if "해당 없음" not in x]
        txt = escape(" / ".join(사례)) if 사례 else "해당 없음"
        A(f'<tr><td><b>{lg}</b></td><td>{rule}</td><td style="font-size:12px">{txt}</td></tr>')
    A("</tbody></table></div>")
    A("<p>MLB는 2026년 현재 30개 구단 중 29개가 패치 스폰서를 보유(탬파베이만 미체결)하며, "
      "MLS에서 등 하단 스폰서를 가진 구단은 2026년 기준 4곳뿐이고 Houston Dynamo가 그중 하나다.</p>")

    # ================= 4. 업종 분포 =================
    A('<h2 id="s4">4. 업종 분포</h2>')
    A(f"<p>활성 스폰서 {len(활성)}건 기준.</p>")
    A('<div class="scroll"><table><thead><tr><th>업종</th><th class="num">건수</th>'
      '<th>비중</th><th>사례</th></tr></thead><tbody>')
    mx = max(업종카운트.values())
    for 업종, n in 업종카운트.most_common():
        c = 업종색.get(업종, "#525252")
        w = int(n / mx * 100)
        A(f'<tr><td>{업종배지(업종)}</td><td class="num"><b>{n}</b></td>'
          f'<td style="width:130px"><div style="height:7px;border-radius:4px;background:{c};width:{w}%"></div></td>'
          f'<td style="font-size:12px">{escape(", ".join(업종사례[업종]))}</td></tr>')
    A("</tbody></table></div>")
    A(f"""<h3>검증 결과: 예상과 달랐던 부분</h3>
<p>설계 단계에서 "텍사스는 에너지·항공이 두드러질 것"으로 적었다. 실제 데이터는 <b>절반만 맞았다</b>.</p>
<ul class="tight">
<li><b>에너지 1위({업종카운트['에너지']}건)는 확인됐다.</b> 특히 Energy Transfer는 Stars 헬멧과 Rangers 유니폼 소매에 동시에 붙어 있다.</li>
<li><b>항공은 {업종카운트['항공']}건이지만, 전부 American Airlines 한 기업이다.</b>
American Airlines Center 하나를 Mavericks·Stars·Wings 세 구단이 공유해 구단 수만큼 건수가 잡힌 것이라
<b>실질 1건</b>이다. 예상이 틀렸다.</li>
<li>예상하지 못한 것은 <b>헬스케어 {업종카운트['헬스케어']}건</b>이다. 텍사스 권역 MLS·NWSL 구단 유니폼 가슴은 사실상 전부 의료기관이
차지했고(Children's Health, UT Southwestern, MD Anderson×2), NBA에서도 Rockets가 병원(Memorial Hermann)을 패치에 올렸다.
소비재 브랜드가 아니어도 유니폼 최대 지면을 산다는 것이 이 권역의 실제 특징이다.</li>
</ul>""")

    # ================= 5. 구단별 상세 =================
    A('<h2 id="s5">5. 구단별 상세</h2>')
    for c in 도시순서:
        ts = [t for t in 구단들 if t["도시"] == c]
        A(f'<div class="city"><div class="cityhd"><h3>{escape(c)}</h3>'
          f'<span class="c">{len(ts)}개 구단</span></div>')
        for t in ts:
            A('<div class="team"><div class="teamhd"><div class="t1">'
              f'<span class="nm">{escape(t["구단명"])}</span>'
              f'<span class="lg">{escape(t["리그"])}</span>'
              f'<span class="c" style="font-size:12px;color:#78716c">창단 {t["창단연도"]}</span>'
              + (f'<span class="asof">기준 예외 · {escape(t["기준시점예외"])}</span>'
                 if t.get("기준시점예외") else "")
              + "</div>"
              f'<div class="meta">{escape(t["연고지"])} · 홈구장 <b>{escape(t["홈구장"])}</b>'
              + (f' <sup class="fnref">각주 1–{len(t["각주"])}</sup>' if t.get("각주") else "")
              + f' · 구단주 {escape(t["구단주"])}</div>')
            if t.get("구장비고"):
                A(f'<div class="note">{escape(t["구장비고"])}</div>')
            A(f'<div class="note"><b>유니폼 광고</b> — {escape(t["유니폼패치"])}</div>')
            # 각주 — 번호는 구단 카드 내부에서만 매긴다 (문서 전역 번호를 쓰면 어긋날 수 있음)
            각주 = t.get("각주") or []
            if 각주:
                A('<div class="fn"><b>각주</b><ol>')
                for f in 각주:
                    A(f"<li>{escape(f)}</li>")
                A("</ol>")
                if t.get("각주출처"):
                    A(f'<p class="fnsrc">출처 — {escape(t["각주출처"])}</p>')
                A("</div>")
            A('</div><div class="teambd">')
            for s in t["스폰서"]:
                끝 = s.get("상태") == "종료"
                A(f'<div class="sp{" ended" if 끝 else ""}"><div class="h">'
                  f'<span class="co">{escape(s["기업명"])}</span>{업종배지(s["업종"])}'
                  f'{등급배지(s["계약"]["공개등급"])}')
                if s.get("한국기업"):
                    A('<span class="flag">한국 기업</span>')
                if s.get("비고"):
                    A(f'<span class="c" style="font-size:11px;color:#78716c">{escape(s["비고"])}</span>')
                if 끝:
                    A('<span class="badge g-none">종료</span>')
                A("</div><dl>")
                for k, v in [("계약", s["계약"]["내용"]), ("금액", s["계약"]["금액"]),
                             ("노출 영역", s["노출영역"]), ("하는 일", s["하는일"]),
                             ("팬 접점", s["팬접점"]), ("출처", s["계약"]["출처"])]:
                    A(f"<dt>{k}</dt><dd>{escape(str(v))}</dd>")
                A("</dl></div>")
            A(f'<div class="pt"><b>생활 밀접 포인트</b>{escape(t["생활밀접포인트"])}</div>')
            A("</div></div>")
        A("</div>")

    # ================= 6. 콘텐츠 후보 =================
    hooks = [
        ("월드컵 두 달간 AT&T Stadium과 NRG Stadium이 사라졌다",
         "FIFA 클린 스타디움 규정은 대회 기간 구장의 기업명·로고를 금지한다. FIFA 글로벌 파트너와 충돌하기 때문이다. "
         "AT&T Stadium은 'Dallas Stadium'으로 9경기, NRG Stadium은 'Houston Stadium'으로 치렀다. "
         "스폰서십이 무엇인지 한 장으로 설명되는 사례."),
        ("휴스턴 구장 이름의 역사가 곧 미국 기업사",
         "Enron Field(2000~2002, 엔론 회계부정 붕괴로 폐기) → Minute Maid Park(2002~2024) → Daikin Park(2025~2039). "
         "미닛메이드는 이름을 잃었지만 2029년까지 구단 파트너로 남아 있고, 팬들은 여전히 구장을 'Juice Box'라 부른다."),
        ("지역 여론이 네이밍 라이츠를 되돌렸다",
         "Reliant → (인수) → NRG → 2026년 8월 다시 Reliant. 휴스턴 지역 고객 설문에서 90%가 환원을 지지했고, "
         "구단·구장 25주년 시즌에 맞춰 실행됐다. 이름이 M&A로 바뀌고 여론으로 되돌아온 흔치 않은 사례."),
        ("리그마다 광고 붙이는 자리가 다르다",
         "NFL은 아예 없고, NHL은 홈·원정 헬멧 광고주를 따로 팔고, MLB는 투수 자세를 계산해 소매를 골랐고, "
         "MLS는 지면이 4개다. 이것만으로 카드 한 세트가 나온다. (3장 표 그대로 활용)"),
        ("Wings의 유니폼 스폰서는 기업이 아니라 옆 동네 NBA 구단",
         "Dallas Mavericks가 소유주가 다른 WNBA 구단의 유니폼 스폰서가 된 최초 사례. 7자리 수 계약이고, "
         "내용은 광고가 아니라 노스텍사스 여자 유소년 스포츠 프로그램(연 3,000명 이상) 운영이며 "
         "Wings 선수·코치가 직접 참여한다."),
        ("구단이 이 도시에 있는 이유가 스폰서 때문",
         "1973년 Tom C. Frost가 프랜차이즈의 샌안토니오 이전 자금을 지원했다. 50년 뒤 Frost Bank는 "
         "유니폼 패치 스폰서를 거쳐 구장 이름(연 약 900만 달러)을 갖게 됐다. 그 패치 자리는 "
         "핀테크(Self Financial) → 암호화폐 보안(Ledger)이 이어받았다."),
        ("Chase 카드가 있으면 전용 게이트로 들어간다",
         "Mavericks 유니폼 패치가 7년 쓴 핀테크(Chime)에서 대형 은행(Chase)으로 바뀌었고, 계약에는 "
         "American Airlines Center 동측 전용 출입구, 매점·굿즈 할인, 지역 창업 지원 프로그램 운영이 포함됐다. "
         "스폰서십이 관중 동선을 바꾼 사례."),
        ("MLS가 광고 자리를 하나 더 만들자 물티슈 회사가 제일 먼저 샀다",
         "2026 올스타 브레이크 이후 등 하단 지면이 신설됐고(가슴 로고의 80% 크기), Houston Dynamo는 이 자리를 "
         "DUDE Wipes에 팔았다. 등 하단 스폰서를 가진 MLS 구단은 2026년 기준 4곳뿐이다."),
    ]
    A('<h2 id="s6">6. 콘텐츠로 쓸 만한 사례</h2>')
    A("<p>카드뉴스 원고 후보. 순서는 후크 강도 순.</p><ol class='hooks'>")
    for t_, b_ in hooks:
        A(f'<li><span class="t">{escape(t_)}</span>{escape(b_)}</li>')
    A("</ol>")

    # ================= 7. 한국 기업 =================
    A('<h2 id="s7">7. 한국 기업 관련</h2>')
    A(f"<p>권역 {len(구단들)}개 구단 {len(활성)}건 중 <b>{len(한국기업)}건</b>이다.</p><ul class='tight'>")
    for t, s in 한국기업:
        A(f'<li><b>{escape(s["기업명"])} — {escape(t["구단명"])}</b> · {escape(s["계약"]["내용"])} '
          f'(금액 {escape(s["계약"]["금액"])}, {escape(s["계약"]["공개등급"])}). {escape(s["하는일"])}</li>')
    A("</ul>")
    해외 = [(t, s) for t, s in 활성 if s.get("비고") and "기업" in s.get("비고", "")]
    A("<p>참고로 아시아·유럽 기업은 별도로 표기했다: "
      + escape(" / ".join(f'{s["기업명"]}({t["구단명"]}, {s["비고"]})' for t, s in 해외)) + ".</p>")

    # ================= 8. 미공개·미확인 =================
    A('<h2 id="s8">8. 미공개·미확인 항목</h2>')
    A("<p>확인하지 못한 것을 명시한다. <b>추정치는 어디에도 넣지 않았다.</b></p>")
    A(f"""<div class="warn"><b>발행 전 반드시 재확인할 2건</b>
<ul class="tight" style="margin-bottom:0">
<li><b>Reliant Stadium 개칭이 2026년 8월 중 실제 완료됐는지 미확인.</b>
본 조사는 2026년 4월 발표 기준이고 예정 시점이 이번 달이다.</li>
<li><b>Dallas Wings 홈구장이 유동적이다.</b> 2026 시즌은 College Park Center + American Airlines Center 3경기,
2027 시즌은 American Airlines Center 전 경기, Dallas Memorial Auditorium 완공은 2028년으로 지연(시 사용계약 15년 1,900만 달러).
지도·대시보드에 어느 구장으로 표기할지 결정이 필요하다.</li>
</ul></div>""")
    미공개 = [f'{s["기업명"]}({t["구단명"]})' for t, s in 활성 if s["계약"]["금액"] == "미공개"]
    A(f"<h4>계약 금액 미공개 — 활성 {len(활성)}건 중 {len(미공개)}건</h4>")
    A(f'<p style="font-size:12px;color:#57534e">{escape(", ".join(미공개))}</p>')
    A("<p>유니폼 패치·전면 스폰서 계약 금액은 <b>13개 구단 전부 미공개</b>다. "
      "Daikin Park는 구단·기업 공동 발표에서 금액을 명시적으로 비공개 처리했고, "
      "총 1억 4,000만 달러·연 800만~900만 달러는 Pollstar 보도 기준이다.</p>")
    적은구단 = sorted(((len([s for s in t["스폰서"] if s.get("상태") != "종료"]), t["구단명"]) for t in 구단들))[:3]
    A(f"""<h4>수집 편차 / 표본의 한계</h4><ul class="tight">
<li>스폰서 수집이 적은 구단: {escape(", ".join(f"{n}—{c}건" for c, n in 적은구단))}.
해당 구단의 공식 파트너 페이지를 개별 확인하면 보강 가능하다.</li>
<li>Houston Texans는 공식 파트너 페이지 전수 확인을 하지 못했고, 검색으로 잡힌 3건만 기재했다.</li>
<li>Cowboys는 공식 파트너가 150곳 이상, Stars는 120곳 이상으로 보도된다.
본 조사는 각 구단의 <b>대표 3~5곳만 다룬 표본</b>이다.</li>
</ul>""")

    # ================= 9. 출처 =================
    A('<h2 id="s9">9. 출처</h2><div class="src">')
    A("<h4>구단·기업 공식</h4><p>LG USA 보도자료(Cowboys, 2024) · Fanatics Inc. · PR Newswire(Kohler, 2024) · "
      "media.chase.com(Mavericks, 2026) · Businesswire(Chime, 2024) · NHL.com 구단 보도자료(PNC Plaza) · "
      "Paylocity(2024) · MLB.com(Globe Life 연장, Energy Transfer 패치, Oxy 패치) · "
      "FC Dallas 구단 발표(Toyota 갱신 2025-10, DNA Kit 2026-02) · 프리스코시 보도자료 · "
      "Mavs.com·NBA.com(Wings GEM) · NBA.com(Spurs Frost, Spurs Ledger) · "
      "Daikin Global·PR Newswire(2024-11) · Astros 발표(Minute Maid 잔류) · Shell·구단 공동 보도자료 · "
      "Houston Dynamo(DUDE Wipes) · Reliant Energy·Businesswire(2026-04-15) · Q2 Holdings · Diageo · TDECU</p>")
    A("<h4>업계 매체</h4><p>Sportico · SportBusiness · SportsPro · Pollstar(Daikin Park) · "
      "SponsorUnited 댈러스 마켓 리포트 · Zoomph(NHL 헬멧 2025-26, NBA 패치) · SportsLogos.Net(2025-26 NBA 패치) · "
      "Blinkfire(2026 NWSL 키트) · FOR SOCCER(2026 MLS 저지)</p>")
    A("<h4>일반 언론</h4><p>Forbes·VentureBeat(AT&amp;T Stadium 2013) · ESPN · Yahoo Sports · CBS Sports · "
      "Houston Public Media·click2houston·FOX 26 Houston·KHOU · KSAT·KENS5 · WFAA·CBS Texas·Axios Dallas · "
      "NBC DFW·FOX 4(월드컵 개칭) · KERA News · InsideArenas·Stadiums of Pro Football·Dallas.Wiki</p>")
    A("</div>")

    A(f"""<footer>한국무역협회 달러스지부 · 2026-08-05 작성 · 구단 {len(구단들)} / 활성 스폰서 {len(활성)}건<br>
이 문서는 <code>데이터.json</code>에서 <code>보고서생성.py</code>로 자동 생성됩니다.
데이터를 수정한 뒤 스크립트를 다시 실행하세요.</footer>""")
    A("</main></div></body></html>")

    io.open(OUT, "w", encoding="utf-8").write("".join(P))
    print("generated: %s (%d teams / %d active sponsors)" % (OUT, len(구단들), len(활성)))


if __name__ == "__main__":
    main()
