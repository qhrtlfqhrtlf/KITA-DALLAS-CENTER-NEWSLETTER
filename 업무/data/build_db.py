import pandas as pd, warnings; warnings.filterwarnings('ignore')
g=pd.read_csv('gep_dedup.csv')

COLS=['No','전시회명(영문)','전시회명(국문)','회의시작일','회의종료일','전시시작일','전시종료일',
'일자확정여부','개최주기','2027개최여부','도시','주','전시장','산업분야','규모','규모기준연도',
'한국관모집상태','한국관운영기관','출처구분','검증등급','공식URL','확인일자','비고']

rows=[]
for _,r in g.iterrows():
    s,e=str(r['개최시작일자'])[:10],str(r['개최종료일자'])[:10]
    conf=r['일자확정여부']
    rows.append({'전시회명(영문)':str(r['전시회명(영문)']).strip(),'전시회명(국문)':r['전시회명(국문)'],
    '회의시작일':s if conf!='미정' else '','회의종료일':e if conf!='미정' else '',
    '전시시작일':'','전시종료일':'','일자확정여부':conf,'개최주기':'⚠ 미확인','2027개최여부':'⚠ 미확인',
    '도시':r['도시'],'주':'','전시장':r['전시장'],'산업분야':r['산업분야'],
    '규모':r['개최규모'],'규모기준연도':'⚠ 미표기','한국관모집상태':'⚠ 미게시(GEP 공란)',
    '한국관운영기관':'⚠ 미확인','출처구분':'GEP','검증등급':'⚠','공식URL':'','확인일자':'',
    '비고':f"GEP월단위:{s}~{e}" if conf!='확정' else ''})

# 외부 발굴 + 공식 확인 건
EXT=[
# 명, 국문, 회의S,회의E,전시S,전시E,주기,개최,도시,주,전시장,분야,등급,URL,비고
("Consumer Electronics Show (CES)","2027 미국 라스베가스 소비자가전 전시회","2027-01-06","2027-01-09","","","연1회","개최","라스베가스","NV","Las Vegas Convention Center 외 12개 회장","소비자가전·IT","✅","ces.tech","GEP 교차일치"),
("AHR Expo","2027 미국 시카고 공조냉난방 전시회","","","2027-01-25","2027-01-27","연1회","개최","시카고","IL","McCormick Place","공조·냉난방(HVACR)","✅","ahrexpo.com","10-18시, 최종일 16시 단축. GEP 교차일치"),
("International Pipeline Pigging Forum","2027 미국 휴스턴 파이프라인 피깅 포럼","2027-01-25","2027-01-28","","","연1회","개최","휴스턴","TX","George R. Brown CC","파이프라인·에너지","⚠","","컨벤션센터 캘린더 기반"),
("Dallas Franchise Show","2027 미국 달라스 프랜차이즈 전시회","2027-01-30","2027-01-31","","","연1회","개최","달라스","TX","⚠ 미확인","프랜차이즈","⚠","franchiseshowinfo.com",""),
("NAPE Summit","2027 미국 휴스턴 석유가스 자산거래 서밋","2027-02-03","2027-02-05","","","연1회","개최","휴스턴","TX","George R. Brown CC","석유·가스","⚠","","컨벤션센터 캘린더 기반"),
("Hydrogen Technology Expo North America","2027 미국 휴스턴 수소기술 전시회","2027-02-10","2027-02-11","","","연1회","개최","휴스턴","TX","George R. Brown CC","수소·에너지","⚠","hydrogen-expo.com","400+사·7,000+명 주장(연도 미확인)"),
("NADA Show","2027 미국 올랜도 자동차딜러 전시회","2027-02-17","2027-02-20","2027-02-18","2027-02-20","연1회","개최","올랜도","FL","Orange County CC West Concourse","자동차 유통","✅","nada.org","회의/전시 분리 확인"),
("Texas Technology Summit","2027 미국 휴스턴 IT 서밋","2027-03-04","2027-03-04","","","연1회","개최","휴스턴","TX","Norris Conference Center","IT","⚠","technologysummit.net","단일일·소규모"),
("Natural Products Expo West","2027 미국 애너하임 천연건강식품 전시회","2027-03-02","2027-03-05","2027-03-03","2027-03-05","연1회","개최","애너하임","CA","Anaheim Convention Center","식품·건강","⚠","","집계사이트만 — 공식 확인 필요"),
("SXSW EDU","2027 미국 오스틴 SXSW EDU","2027-03-13","2027-03-16","","","연1회","개최","오스틴","TX","Austin Convention Center","교육","✅","sxswedu.com",""),
("SXSW","2027 미국 오스틴 사우스바이사우스웨스트","2027-03-15","2027-03-21","","","연1회","개최","오스틴","TX","Austin Convention Center 외","테크·미디어·문화","✅","sxsw.com","배지 판매 2026-08-18 개시"),
("International Battery Seminar & Exhibit","2027 미국 올랜도 배터리 세미나","2027-03-15","2027-03-18","","","연1회","개최","올랜도","FL","Rosen Shingle Creek","배터리","⚠","","Battery Show NA와 별개"),
("Energy & Mobility Conference & Expo","2027 미국 클리블랜드 에너지모빌리티 전시회","2027-03-29","2027-03-31","","","연1회","개최","클리블랜드","OH","⚠ 미확인","에너지·모빌리티","⚠","energyandmobility.org",""),
("SEMICON West","2027 미국 피닉스 반도체 전시회","2027-03-30","2027-04-01","","","연1회","개최","피닉스","AZ","Phoenix Convention Center","반도체","✅✅","semi.org","SF→피닉스 상설·춘계 전환. 2028 5/9-11, 2029 4/3-5"),
("ISC West","2027 미국 라스베가스 보안 전시회","2027-04-05","2027-04-09","2027-04-07","2027-04-09","연1회","개최","라스베가스","NV","Venetian Expo","보안","⚠","discoverisc.com","GEP는 3월로 오기재. SEMICON West와 별개"),
("ProMat","2027 미국 시카고 물류공급망 전시회","2027-04-19","2027-04-21","2027-04-19","2027-04-21","격년(홀수년)","개최","시카고","IL","McCormick Place","물류·공급망","✅","promatshow.com","4일→3일 단축. 1,000+사·670,000sqft('27계획). GEP 미수록"),
("NPE: The Plastics Show","2027 미국 올랜도 플라스틱 전시회","2027-05-03","2027-05-07","","","3년주기","개최","올랜도","FL","Orange County CC","플라스틱","✅","npe.org","2,200+사·55,000명('27목표). 테마 NEXT IS NOW. GEP 교차일치"),
("Offshore Technology Conference (OTC)","2027 미국 휴스턴 해양기술 컨퍼런스","2027-05-03","2027-05-05","","","연1회","개최","휴스턴","TX","NRG Park","해양·에너지","⚠","otcnet.org","집계사이트만 — 공식 확인 필수"),
("SynBioBeta","2027 미국 산호세 합성생물학 컨퍼런스","2027-05-03","2027-05-06","","","연1회","개최","산호세","CA","San Jose Convention Center","합성생물학·바이오","⚠","synbiobeta.com",""),
("TECHSPO Dallas","2027 미국 달라스 테크 엑스포","2027-05-13","2027-05-14","","","연1회","개최","달라스","TX","Westin Galleria Dallas","테크·마케팅","⚠","techspodallas.com","호텔 개최·소규모"),
("AI+ Expo (SCSP)","2027 미국 워싱턴DC AI 엑스포","","","","","연1회","개최","워싱턴 D.C.","DC","⚠ 미확인","AI·국가안보","⚠","expo.scsp.ai","⚠ 날짜 상충: 5/7-9 vs 5/24-25 병기"),
("Power Generation Engineering & Construction (EPC Expo)","2027 미국 휴스턴 발전EPC 전시회","2027-06-16","2027-06-17","","","연1회","개최","휴스턴","TX","NRG Center","발전·EPC","⚠","epcshow.com",""),
("FABTECH","2027 미국 시카고 금속가공 전시회","2027-09-13","2027-09-16","","","연1회","개최","시카고","IL","McCormick Place","금속가공·용접","✅","fabtechexpo.com","2026 10월 라스베가스→2027 9월 시카고. GEP 교차일치"),
("WEFTEC","2027 미국 시카고 물환경 전시회","2027-09-25","2027-09-29","2027-09-27","2027-09-29","연1회","개최","시카고","IL","McCormick Place","물·수처리","✅","weftec.org","100th Annual(100회차). GEP는 'Water Quality Event'명으로 전시기간만 수록"),
("PACK EXPO Las Vegas","2027 미국 라스베가스 패키징 전시회","","","2027-09-27","2027-09-29","격년(홀수년)","개최","라스베가스","NV","Las Vegas Convention Center","패키징·가공","✅","packexpolasvegas.com","9-17시, 최종일 15시 단축. GEP 미수록"),
# 미개최 판정 건 (기록 보존)
("IMTS","2027 미국 시카고 국제제조기술전시회","","","","","격년(짝수년)","❌ 미개최","시카고","IL","McCormick Place","공작기계","✅","imts.com","다음 회차 2028"),
("MODEX","2027 미국 애틀랜타 물류 전시회","","","","","격년(짝수년)","❌ 미개최","애틀랜타","GA","Georgia World Congress Center","물류·공급망","✅","modexshow.com","🔴 GEP 오류 수록. 실제 2026/4/13-16 → 다음 2028/4/3-6"),
("CONEXPO-CON/AGG","2027 미국 라스베가스 건설기계 전시회","","","","","3년주기","❌ 미개최","라스베가스","NV","Las Vegas Convention Center","건설기계","✅","conexpoconagg.com","다음 2029/3/13-17"),
]
for t in EXT:
    n,k,cs,ce,es,ee,cy,held,city,st,ven,ind,gr,url,memo=t
    conf='확정' if (cs or es) else ('해당없음' if held.startswith('❌') else '미정')
    rows.append({'전시회명(영문)':n,'전시회명(국문)':k,'회의시작일':cs,'회의종료일':ce,
    '전시시작일':es,'전시종료일':ee,'일자확정여부':conf,'개최주기':cy,'2027개최여부':held,
    '도시':city,'주':st,'전시장':ven,'산업분야':ind,'규모':'','규모기준연도':'',
    '한국관모집상태':'⚠ 미확인','한국관운영기관':'⚠ 미확인','출처구분':'외부','검증등급':gr,
    '공식URL':url,'확인일자':'2026-08-11','비고':memo})

db=pd.DataFrame(rows)

# GEP↔외부 교차일치 표시
ALIAS={'CONSUMER ELECTRONICS SHOW':'CES','INTERNATIONAL AIR':'AHR','WATER QUALITY EVENT':'WEFTEC',
'FABTECH':'FABTECH','NPE':'NPE','MODEX':'MODEX','SECURITY CONFERENCE':'ISC WEST'}
def norm(x): return str(x).upper()
gep_names=' | '.join(db[db['출처구분']=='GEP']['전시회명(영문)'].map(norm))
cross={'Consumer Electronics Show (CES)','AHR Expo','FABTECH','NPE: The Plastics Show','WEFTEC','MODEX'}
db.loc[db['전시회명(영문)'].isin(cross)&(db['출처구분']=='외부'),'출처구분']='양쪽(교차일치)'
db.loc[db['전시회명(영문)']=='MODEX','출처구분']='양쪽(⚠GEP오류)'

# GEP측 중복행 제거(외부가 대체한 건)
drop=['CONSUMER ELECTRONICS SHOW','FABTECH 2027','2027 MODEX','THE WATER QUALITY EVENT 2027',
'2027 ORLANDO NPE, THE PLASTIC SHOW','INTERNATIONAL AIR‑CONDITIONING, HEATING, REFRIGERATING EXPOS',
'INTERNATIONAL AIR-CONDITIONING HEATING REFRIGERATION EXPOSIT',
'INTERNATIONAL SECURITY CONFERENCE & EXPOSITION WEST 2027']
db=db[~((db['출처구분']=='GEP')&(db['전시회명(영문)'].map(norm).isin(drop)))]

db=db.sort_values(['회의시작일','전시시작일','전시회명(영문)'],na_position='last').reset_index(drop=True)
db.insert(0,'No',range(1,len(db)+1))
db=db[COLS]
db.to_csv('/home/user/KITA-DALLAS-CENTER-NEWSLETTER/업무/data/전시회DB_2027미국.csv',index=False)
print('총 레코드:',len(db))
print(db['출처구분'].value_counts().to_string())
print(db['검증등급'].value_counts().to_string())
print(db['일자확정여부'].value_counts().to_string())
