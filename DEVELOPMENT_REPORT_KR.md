# 🚀 Willog Intelligent Assistant 개발 현황 보고서

## 📅 2026년 1월 10일 기준

본 문서는 현재까지 개발된 **Willog 물류 데이터 지능형 비서** 서비스의 주요 기능, 아키텍처 개선 사항, 그리고 배포 현황을 정리한 것입니다.

---

## 1. 🏗️ 주요 기능 구현 요약

### A. 🧠 지능형 에이전트 시스템 (Triple Agent Architecture)
사용자의 의도를 파악하여 최적의 에이전트가 답변을 제공하도록 **라우팅 시스템**을 구축했습니다.

1.  **SQL Agent (데이터 분석가)**
    *   **역할**: 자연어를 BigQuery SQL로 변환하여 수치, 통계, 물량 등 정량적 데이터를 분석합니다.
    *   **개선점**:
        *   운송 모드(`Air`, `Truck`, `Ocean+Ferry`, `Ocean+Rail`)를 세밀하게 구분하여 처리.
        *   국가별 필터링(`destination_country`) 및 시간 분석(`departure_date`) 능력 강화.
        *   `gemini-3.0-flash` 모델을 사용하여 정확도 높은 SQL 작성.
2.  **General Agent (대화형 비서)**
    *   **역할**: 인사말("안녕"), 기능 문의("너 뭐 할 수 있어?"), 일반적인 물류 용어 정의 등 SQL 실행이 불필요한 대화를 처리합니다.
    *   **효과**: 불필요한 데이터베이스 조회를 방지하고 자연스러운 사용자 경험(UX) 제공.
3.  **Router (지휘자)**
    *   **역할**: 사용자 질문을 분석하여 위 두 에이전트(또는 문서 검색 에이전트) 중 누구에게 보낼지 결정합니다.

### B. 📊 데이터 마트 고도화 (BigQuery)
Whitepaper 시나리오 분석을 지원하기 위해 Raw 데이터를 목적에 맞게 가공한 **Data Mart**를 구축했습니다.

*   **`mart_logistics_master`**: 운송 건별 종합 분석 (누적 피로도, 리스크 레벨, 파손 여부 등).
*   **`mart_sensor_detail`**: 센서 단위 심층 분석. `destination_country`, `transport_mode` 컬럼을 정규화하여 조인 없이 빠른 분석 가능.
*   **`mart_risk_heatmap`**: 경로 및 지역별 리스크 히트맵 분석 지원.

### C. 🎨 UI/UX 및 데이터 시각화 (Streamlit)
단순 텍스트 응답을 넘어, 데이터의 패턴을 즉관적으로 이해할 수 있는 **자동 시각화 기능**을 구현했습니다.

*   **자동 차트 생성**: 데이터 특성에 따라 최적의 차트를 자동으로 선택하여 그려줍니다.
    *   📈 **Time Series (Line)**: "일별 충격 발생 추이" 등 시계열 데이터.
    *   📊 **Compare (Bar)**: "포장 타입별 파손율" 등 범주 비교.
    *   🌍 **Map (Geospatial)**: "리스크 히트맵" 요청 시 지도 시각화 (Plotly Mapbox).
*   **사용자 편의성**:
    *   **추천 질문 3x4 그리드**: 클릭 한 번으로 복잡한 분석 실행.
    *   **채팅 인터페이스**: 사용자/AI 아바타 및 말풍선 스타일 적용.
    *   **사이드바**: 연결 상태 및 모델 버전 정보 표시.

### D. ☁️ 클라우드 배포 (GCP Cloud Run)
*   Google Cloud Run을 통해 완전 관리형 서버리스 환경에 배포되었습니다.
*   CI/CD: GitHub 로컬 커밋 -> Cloud Build -> Cloud Run 배포 파이프라인 구축.

---

## 2. 📝 변경 이력 (Last Sprint)

1.  **Transport Mode 세분화**: 사용자의 요청에 따라 `Ocean` 단일 모드를 `Ocean+Ferry`, `Ocean+Rail` 등 복합 모드로 세분화하여 정확한 분석 지원.
2.  **LLM 모델 업그레이드**: 최신 성능 확보 및 추론 능력 강화를 위해 **`gemini-3.0-flash`** 모델로 전체 시스템 업그레이드 완료.
3.  **Fallback Logic 강화**: 라우터가 대화형 질문을 SQL로 잘못 인식하지 않도록 키워드 기반 안전장치(Fallback) 추가.

---

## 3. 🔗 접속 정보

*   **서비스 URL**: [Willog Assistant 바로가기](https://willog-assistant-753372497836.asia-northeast3.run.app)
*   **연동 데이터**: Willog Production Gold Data (`bigquery.willog-prod-data-gold`)

---

## 4. 향후 계획

1.  **Retrieval Agent 완성**: 실제 PDF 문서(Whitepaper 등)를 벡터 데이터베이스에 인덱싱하여 RAG 완전체 구현.
2.  **Dashboard 고도화**: 대화형 인터페이스 외에 상시 모니터링 가능한 대시보드 페이지 추가 검토.
