
# Google Cloud 자격 증명(Credentials) 설정 가이드

이 프로젝트는 BigQuery와 Vertex AI에 접근하기 위해 Google Cloud 인증이 필요합니다.
현재 시스템에 `gcloud` CLI가 설치되어 있지 않은 것으로 확인됩니다. 다음 두 가지 방법 중 하나를 선택하여 설정해 주세요.

## 방법 1: 서비스 계정 키 (Service Account Key) 사용 (가장 빠름)

Google Cloud 콘솔에서 JSON 키 파일을 다운로드하여 설정하는 방법입니다.

1. **Google Cloud Console 접속**: [GCP Console](https://console.cloud.google.com/iam-admin/serviceaccounts)로 이동합니다.
2. **프로젝트 선택**: `willog-prod-data-gold` 프로젝트를 선택합니다.
3. **서비스 계정 생성/선택**:
    - 기존 서비스 계정을 선택하거나 새로 만듭니다.
    - 해당 계정에 **BigQuery Data Editor**, **BigQuery Job User**, **Vertex AI User** 권한이 있는지 확인하세요.
4. **키 생성**:
    - '키(Keys)' 탭 -> '키 추가(Add Key)' -> '새 키 만들기(Create new key)' -> **JSON** 선택.
    - 다운로드된 파일을 프로젝트 루트 폴더(`ds_intelligent_assistant/`)에 `credentials.json` 이름으로 저장합니다. (보안을 위해 `.gitignore`에 추가하는 것이 좋습니다.)
5. **환경 변수 설정**:
    터미널에서 다음 명령어를 실행하여 인증 파일을 연결합니다.
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"
    ```
    (매번 실행하기 번거롭다면 `.env` 파일에 경로를 적거나 `~/.zshrc`에 추가하세요.)

---

## 방법 2: gcloud CLI 설치 및 로그인 (권장)

Google Cloud SDK를 설치하여 개발자 본인의 계정으로 인증하는 방법입니다.

1. **설치**:
    Homebrew를 사용하신다면:
    ```bash
    brew install --cask google-cloud-sdk
    ```
    또는 [공식 문서](https://cloud.google.com/sdk/docs/install)를 참조하여 직접 설치합니다.

2. **로그인**:
    설치 후 터미널에서 다음을 실행합니다:
    ```bash
    gcloud auth application-default login
    ```
    브라우저가 열리면 Google 계정으로 로그인하고 권한을 허용합니다.

3. **프로젝트 설정** (선택):
    ```bash
    gcloud config set project willog-prod-data-gold
    ```

## 확인
설정이 완료되면 다시 테스트 스크립트를 실행해 보세요:
```bash
python3 app/agents/orchestrator.py "지난달 베트남행 물량 알려줘"
```
