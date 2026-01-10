
import sys
import os
import pandas as pd

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.sql_agent import agent

suggestions = [
    "📉 상하이(CNSHG)행 총 물량 및 파손율",
    "🔥 구간별 충격 리스크 히트맵 분석",
    "⚠️ 누적 충격 피로도 Top 5 운송 건",
    "🌡️ 오사카행 온도 이탈 평균 지속 시간",
    "📊 포장 타입별 파손율 및 안전 점수 비교",
    "🛳️ 해상 운송 중 5G 이상 충격 발생 비율",
    "📍 베트남 경로 습도 취약 구간 분석",
    "❄️ 영하 온도에서 발생한 충격 건수",
    "🏆 운송사별 배송 품질 벤치마킹",
    "🚨 최근 1주일 High Risk 등급 운송 건"
]

print("🔍 Validating Suggested Questions...\n")

failed_indices = []

for i, q in enumerate(suggestions):
    print(f"[{i+1}/{len(suggestions)}] Testing: {q}")
    try:
        # Generate SQL and Execute
        response = agent.process_query(q)
        sql = response.get("generated_sql", "").strip()
        df = response.get("result")
        error = response.get("error")
        
        if not sql:
             print(f"  ❌ No SQL Generated")
             failed_indices.append(i)
        elif error:
            print(f"  ❌ Execution Error: {error}")
            failed_indices.append(i)
        elif df is None:
             print(f"  ❌ API/Connection Error (df is None)")
             failed_indices.append(i)
        elif df.empty:
            print(f"  ⚠️ Empty Result (0 rows) - Data might effectively not exist")
            # Empty is not necessarily an error, but for "suggestions" it's bad UX.
            # We will mark it as failed for recommendation purposes.
            failed_indices.append(i)
        else:
            print(f"  ✅ Success ({len(df)} rows)")
            # print(df.head(1).to_string())
            
    except Exception as e:
        print(f"  ❌ Critical Exception: {e}")
        failed_indices.append(i)
    print("-" * 30)

print("\n📋 Summary:")
print(f"Total: {len(suggestions)}")
print(f"Passed: {len(suggestions) - len(failed_indices)}")
print(f"Failed: {len(failed_indices)}")

if failed_indices:
    print("\n❌ Failed Questions:")
    for idx in failed_indices:
        print(f"- {suggestions[idx]}")
