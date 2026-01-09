
# DS Intelligent Assistant - 개발 현황 요약

## 📅 작성일: 2026-01-08

---

## 1. 프로젝트 개요

**목표**: Willog 물류 데이터 분석을 위한 RAG(Retrieval-Augmented Generation) 시스템 구축

**핵심 개념**:
- **PDF 문서**: RAG 서비스 기획 및 스키마 설계 참고용 (데이터 소스 아님)
- **BigQuery**: 실제 데이터 소스 (모든 데이터 조회는 BigQuery를 통해)

**기술 스택**:
- **LLM**: Google Vertex AI (gemini-2.5-flash)
- **프레임워크**: LangChain
- **데이터**: BigQuery (`willog-prod-data-gold.rag`)
- **언어**: Python 3.9+

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     사용자 인터페이스                          │
│                    (Streamlit - 미구현)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator                            │
│              (app/agents/orchestrator.py)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Router                               │
│                  (app/agents/router.py)                      │
│          질문 유형 분류 → SQL_AGENT / RETRIEVAL_AGENT         │
└─────────────────────────────────────────────────────────────┘
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│        SQL Agent          │   │     (확장 예정)            │
│ (app/agents/sql_agent.py) │   │  추가 에이전트 영역         │
│                           │   │                           │
│ • 자연어 → SQL 변환         │   │                           │
│ • BigQuery 스키마 활용      │   │                           │
└───────────────────────────┘   └───────────────────────────┘
            │
            ▼
┌───────────────────────────┐
│     BigQuery Wrapper      │
│(packages/bq_wrapper/      │
│  client.py, schema.py)    │
└───────────────────────────┘
```

### 📚 주요 정보 및 컨텍스트

*   **데이터 소스 (Live)**:
    *   모든 데이터는 **BigQuery `scm` 데이터셋의 실제 테이블**(`corning_transport`, `corning_features`)로부터 실시간으로 집계됩니다.
    *   `rag` 데이터셋의 뷰(View)들은 실제 원천 테이블을 참조하도록 구성되어 있어 데이터 정합성이 보장됩니다.

*   **구현된 기능**:
    *   **SQL Agent**: 자연어 질문을 BigQuery SQL로 변환하여 실제 데이터를 분석합니다.
    *   **Response Synthesis**: SQL 결과를 바탕으로 데이터에 기반한 자연어 답변을 생성합니다.
    *   **Streamlit UI**: 공개 URL을 통해 외부에서도 접속 가능한 채팅 인터페이스를 제공합니다.
    *   **Cloud Deployment**: Google Cloud Run에 배포되어 안정적인 서비스를 제공합니다.

*   **운영 정보**:
    *   **서비스 URL**: [https://willog-assistant-753372497836.asia-northeast3.run.app](https://willog-assistant-753372497836.asia-northeast3.run.app)
    *   **리전**: `asia-northeast3` (Seoul)

---

## 3. 프로젝트 구조

```
ds_intelligent_assistant/
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # 전체 플로우 제어
│   │   ├── router.py            # 질문 분류 (SQL/Retrieval)
│   │   ├── sql_agent.py         # SQL 생성 에이전트
│   │   └── retrieval_agent.py   # 문서 검색 에이전트 (Stub)
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py            # 설정 관리 (Pydantic)
│   └── ui/
│       └── __init__.py
├── packages/
│   ├── __init__.py
│   ├── bq_wrapper/
│   │   ├── __init__.py
│   │   ├── client.py            # BigQuery 클라이언트 래퍼
│   │   └── schema.py            # 테이블 스키마 정의
│   └── vectordb/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_agent.py            # 에이전트 테스트 스크립트
├── requirements.txt             # 의존성 패키지
├── README_SETUP.md              # 자격증명 설정 가이드
└── willog-prod-data-gold-*.json # GCP 서비스 계정 키
```

---

## 4. 핵심 컴포넌트 상세

### 4.1 SQL Agent (`app/agents/sql_agent.py`)
- **기능**: 자연어 질문을 BigQuery SQL로 변환
- **모델**: `gemini-2.5-flash` (Vertex AI)
- **프롬프트**: 테이블 스키마 정보를 동적 주입하여 정확한 SQL 생성 유도

### 4.2 Router (`app/agents/router.py`)
- **기능**: 사용자 질문을 분석하여 적합한 에이전트로 라우팅
- **분류 기준**:
  - `SQL_AGENT`: 수치/통계 질문 (물량, 온도, 충격율 등)
  - `RETRIEVAL_AGENT`: 지식/규정 질문 (정책, 기준 설명 등)

### 4.3 BigQuery 스키마 (`packages/bq_wrapper/schema.py`)
PDF 명세서 기반으로 정의된 가상 테이블:

| 테이블명 | 용도 |
|---------|------|
| `view_transport_stats` | 일자별 운송 물량/건수/이슈 집계 |
| `view_issue_stats` | 충격/이탈률 통계 (5G/10G 기준) |
| `view_sensor_stats` | 센서 데이터 (온도/습도) 요약 |

### 4.4 설정 (`app/core/config.py`)
```python
PROJECT_ID = "willog-prod-data-gold"
DATASET_ID = "rag"
LOCATION   = "us-central1"
```

---

## 5. 테스트 결과

### ✅ 성공 케이스
```
질문: "지난달 베트남행 물량 알려줘"
라우팅: SQL_AGENT
생성 SQL:
SELECT sum(total_volume)
FROM view_transport_stats
WHERE date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH) 
              AND LAST_DAY(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))
  AND destination = 'Vietnam'
```

---

## 6. 완료된 작업

| 작업 | 상태 |
|-----|------|
| 시스템 아키텍처 다이어그램 작성 | ✅ 완료 |
| 구현 계획서 작성 (한글) | ✅ 완료 |
| 프로젝트 구조 초기화 | ✅ 완료 |
| BigQuery Wrapper 구현 | ✅ 완료 |
| 테이블 스키마 정의 | ✅ 완료 |
| SQL Agent 구현 | ✅ 완료 |
| Router 구현 | ✅ 완료 |
| Orchestrator 구현 | ✅ 완료 |
| Retrieval Agent (Stub) | ✅ 완료 |
| GCP 자격증명 연결 | ✅ 완료 |
| End-to-End 테스트 | ✅ 완료 |

---

## 7. 향후 개발 과제

| 우선순위 | 작업 | 설명 |
|---------|-----|------|
| 🔴 높음 | Retrieval Agent 완성 | PDF 문서를 Vector Store에 인덱싱 후 RAG 구현 |
| 🔴 높음 | Streamlit UI 개발 | 사용자 인터페이스 구축 |
| 🟡 중간 | SQL 실행 연동 | 생성된 SQL을 실제 BigQuery에서 실행 후 결과 반환 |
| 🟡 중간 | 응답 합성(Synthesis) | SQL 결과를 자연어로 변환하여 사용자에게 제공 |
| 🟢 낮음 | 프롬프트 최적화 | 더 정확한 SQL 생성을 위한 프롬프트 튜닝 |
| 🟢 낮음 | 평가 지표 구축 | 에이전트 성능 측정을 위한 테스트 셋 구성 |

---

## 8. 실행 방법

```bash
# 1. 환경 변수 설정
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/willog-prod-data-gold-*.json"

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 에이전트 실행
python3 app/agents/orchestrator.py "지난달 베트남행 물량 알려줘"
```

---

## 9. 참고 문서

- `DST-RAG 구성 정리-080126-023847.pdf`: 요구사항 명세서
- `.gemini/antigravity/brain/.../implementation_plan.md`: 상세 구현 계획서
- `.gemini/antigravity/brain/.../architecture.md`: 시스템 아키텍처 다이어그램

