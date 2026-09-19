import os
import re
from bs4 import BeautifulSoup
import requests

url = "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio50410441.html"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

print("1. 웹 데이터 요청 중...")
res = requests.get(url, headers=headers)

# 진학사 페이지의 실제 인코딩(UTF-8) 적용
res.encoding = "utf-8"

soup = BeautifulSoup(res.text, "html.parser")
rows = soup.find_all("tr")
print(f"2. 전체 테이블 행(tr) 개수: {len(rows)}개 확인")


def to_int(val):
  try:
    num = re.sub(r"[^\d]", "", str(val))
    return int(num) if num else 0
  except:
    return 0


data = []
current_campus = ""
valid_campuses = ["서울정수", "서울강서", "성남", "제주"]

for tr in rows:
  cells = tr.find_all(["td", "th"])
  if not cells:
    continue

  # 셀 텍스트 정제
  cols = [
      re.sub(r"\s+", " ", c.get_text()).replace("\xa0", "").strip()
      for c in cells
  ]

  # 헤더 제목 행 제외
  if not cols or any(
      h in cols[0] for h in ["캠퍼스", "경쟁률 현황", "모집단위", "일반_일반전형"]
  ):
    continue

  first_val = cols[0]

  # 캠퍼스 판별 및 갱신
  for c in valid_campuses:
    if c in first_val:
      current_campus = c
      break

  is_total = "총계" in first_val
  is_subtotal = "소계" in cols

  # 유효 캠퍼스 또는 총계인 경우 처리
  if current_campus in valid_campuses or is_total:
    if is_total:
      campus_name = "전체"
      dept_name = "총계"
      offset = 1
    elif any(c in first_val for c in valid_campuses):
      campus_name = current_campus
      dept_name = cols[1] if len(cols) > 1 else ""
      offset = 2
    elif "소계" in first_val:
      campus_name = current_campus
      dept_name = "소계"
      offset = 1
    else:
      campus_name = current_campus
      dept_name = cols[0]
      offset = 1

    # 전형 데이터 열 개수 검사
    if len(cols) >= offset + 14:
      # 일반전형 4개 합산
      gen_cap = (
          to_int(cols[offset])
          + to_int(cols[offset + 3])
          + to_int(cols[offset + 6])
          + to_int(cols[offset + 9])
      )
      gen_app = (
          to_int(cols[offset + 1])
          + to_int(cols[offset + 4])
          + to_int(cols[offset + 7])
          + to_int(cols[offset + 10])
      )

      # 정원외 특별전형
      out_cap = to_int(cols[offset + 12])
      out_app = to_int(cols[offset + 13])

      # 경쟁률: (일반 지원 + 정원외 특별 지원) * 100 / 일반 모집
      if gen_cap > 0:
        rate_str = f"{round(((gen_app + out_app) * 100) / gen_cap)} %"
      else:
        rate_str = "-"

      row_type = (
          "total" if is_total else ("subtotal" if is_subtotal else "normal")
      )

      data.append({
          "campus": campus_name,
          "dept": dept_name,
          "gen_cap": gen_cap,
          "gen_app": gen_app,
          "out_cap": out_cap,
          "out_app": out_app,
          "rate": rate_str,
          "type": row_type,
      })

print(f"3. 집계 완료된 항목 수: {len(data)}개")

# HTML 생성
table_rows = ""
for item in data:
  cls_name = ""
  if item["type"] == "subtotal":
    cls_name = ' class="subtotal-row"'
  elif item["type"] == "total":
    cls_name = ' class="total-row"'

  table_rows += f"""
    <tr{cls_name}>
        <td>{item['campus']}</td>
        <td class="dept">{item['dept']}</td>
        <td>{item['gen_cap']:,}</td>
        <td>{item['gen_app']:,}</td>
        <td>{item['out_cap']:,}</td>
        <td>{item['out_app']:,}</td>
        <td class="highlight">{item['rate']}</td>
    </tr>
    """

html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>한국폴리텍I대학 전 캠퍼스 경쟁률 집계</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif;
            padding: 24px;
            background: #f1f3f5;
            color: #212529;
        }}
        h2 {{
            text-align: center;
            color: #1a365d;
            margin-bottom: 20px;
        }}
        .table-container {{
            max-width: 1050px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: center;
            white-space: nowrap;
        }}
        th, td {{
            padding: 11px 12px;
            border-bottom: 1px solid #e9ecef;
            font-size: 14px;
        }}
        th {{
            background: #1e3a8a;
            color: #ffffff;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8fafc;
        }}
        .dept {{
            text-align: left;
            padding-left: 18px;
            font-weight: 500;
        }}
        .highlight {{
            color: #d90429;
            font-weight: 700;
        }}
        .subtotal-row {{
            background-color: #f1f5f9;
            font-weight: 600;
            border-top: 2px solid #cbd5e1;
            border-bottom: 2px solid #cbd5e1;
        }}
        .total-row {{
            background-color: #e2e8f0;
            font-weight: 700;
            border-top: 2px solid #94a3b8;
            font-size: 15px;
        }}
    </style>
</head>
<body>
    <h2>📊 한국폴리텍I대학 캠퍼스별 경쟁률 집계</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>캠퍼스</th>
                    <th>모집단위</th>
                    <th>모집인원(일반)</th>
                    <th>지원인원(일반)</th>
                    <th>정원외 특별전형 모집인원</th>
                    <th>정원외 특별전형 지원인원</th>
                    <th>경쟁률</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
  f.write(html_content)

print("4. 완료: index.html 파일이 생성되었습니다.")