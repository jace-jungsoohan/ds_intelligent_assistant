# 🏗️ [NEW] Hybrid RAG System Data Mart Design

본 설계 문서는 "물류 데이터 분석을 위한 하이브리드 RAG 시스템 Whitepaper"에 명시된 고급 분석 시나리오(누적 피로도, 복합 상관관계, 리스크 예측 등)를 지원하기 위한 BigQuery 데이터 마트 구조를 정의합니다.

## 1. 아키텍처 개요

*   **Raw Layer**: `scm.corning_merged` (IoT Raw Logs), `scm.corning_transport` (Master)
*   **Mart Layer**: RAG 에이전트가 조회하는 **분석 목적별 특화 테이블**.

---

## 2. Mart 테이블 상세 설계

### A. `mart_logistics_master` (운송 건별 종합 분석)
*   **목적**: 운송 건 단위의 성과 평가, 리스크 등급 산정, 거시적 통계.
*   **활용 시나리오**: "10G 이상 충격 건 요약", "최근 한 달 파손 원인 분석", "예측 및 시나리오(파손 확률)"
*   **Grain**: 운송 건(`code`) 당 1 Row
*   **Key Columns**:
    *   `code`, `departure_date`, `destination`, `product`
    *   `package_type`, `transport_mode`
    *   **고급 파생 지표 (Whitepaper 반영)**:
        *   `cumulative_shock_index` (누적 충격 지수: 미세 진동 누적 피로도 반영)
        *   `max_shock_g`, `avg_shock_g`
        *   `temp_excursion_duration_min` (온도 이탈 지속 시간)
        *   `is_damaged` (파손 여부)
        *   `risk_level` (종합 위험 등급: Low/Medium/High/Critical)

### B. `mart_sensor_detail` (심층 원인 분석용 Raw)
*   **목적**: "충격-온도 복합 상관관계", "방향성(Tilt) 기반 포장 유효성", "구체적인 발생 시점/원인 규명"
*   **활용 시나리오**: "영하일 때 충격이 더 컸어?", "측면 충격(Tilt Y)이 많았어?", "중국행 화물의 충격 건수"
*   **Grain**: 센서 로그 단위 (수십억 건, Partitioned by Date)
*   **Key Columns**:
    *   `event_date`, `event_timestamp`
    *   `code` (Join Key)
    *   `destination` (Port Code), `destination_country` (국가명: 'China', 'Japan', 'Vietnam' 등) ✨ NEW
    *   `transport_mode` ('Ocean', 'Air', 'Truck') ✨ NEW - JOIN 없이 직접 필터링 가능
    *   `shock_g` (합성 가속도)
    *   **방향성 데이터**: `acc_x`, `acc_y`, `acc_z` (3축 가속도), `tilt_x`, `tilt_y` (기울기)
    *   `temperature`, `humidity`
    *   `lat`, `lon` (위치)
    *   `status` (Move/Stop/Loading 판단용)

### C. `mart_risk_heatmap` (지리적 리스크 히트맵)
*   **목적**: "경로별 리스크 집중 관리", "상하차 구간 집중 분석".
*   **활용 시나리오**: "어느 항구 진입로에서 충격이 자주 발생해?", "상해항 작업 충격이 높아?"
*   **Grain**: 지역 클러스터(`lat_clustered`, `lon_clustered`) 또는 주요 거점 단위
*   **Key Columns**:
    *   `location_name` (e.g., 상해항, 부산항 - `view_category` 매핑 활용)
    *   `lat`, `lon` (Clustered Center)
    *   `avg_shock_g`, `max_shock_g`
    *   `shock_event_count` (충격 빈도)
    *   `damage_correlation` (해당 지점 경유 시 파손 확률)

### D. `mart_quality_matrix` (조건별 품질 비교)
*   **목적**: " 비교 및 성능 평가", "운송사/포장재 조합별 효율성 분석".
*   **활용 시나리오**: "A타입 포장이 해상 운송에서 수직 진동에 강해?", "운송사별 이탈률 차이는?"
*   **Grain**: 조합(`transport_mode` + `package_type` + `route`) 별 집계
*   **Key Columns**:
    *   `transport_mode`
    *   `package_type`
    *   `route_segment` (e.g., KR-CN)
    *   `avg_deviation_rate` (평균 이탈률)
    *   `damage_rate` (파손 발생률)
    *   `safety_score` (종합 안전 점수)

---

## 3. 구현 전략 (ETL Logic)

1.  **누적 피로도 계산**: `mart_logistics_master` 생성 시 `mart_sensor_detail`을 스캔하여 작은 진동(예: 2~3G)의 빈도를 가중 합산하는 로직 적용.
2.  **복합 조건 쿼리**: SQL Agent가 "저온 상태에서의 충격"을 물으면 `mart_sensor_detail`에서 `WHERE temperature < 0 AND shock_g > 5` 쿼리를 생성하도록 가이드.
3.  **지리 정보 매핑**: `lat/lon`을 사용하여 `mart_risk_heatmap` 생성 시 주요 항만/거점 이름(Geocoding 또는 매핑 테이블)과 연결.
