# Steam 게임 데이터 수집기

이 프로젝트는 Steam API를 사용하여 게임 데이터를 수집하고 MySQL 데이터베이스에 저장하는 도구입니다. Steam의 전체 게임 카탈로그에서 리뷰 수가 1000개 이상인 게임만 선별하여 수집합니다. DLC나 비게임 콘텐츠는 제외하고 기본 게임만 수집합니다.

## 기능

- Steam 전체 게임 목록 조회
- 게임 상세 정보 수집 (이름, 개발사, 배급사, 출시일, 설명, 가격 등)
- 게임 장르 및 태그 정보 수집
- 리뷰 수가 1000개 이상인 게임만 필터링
- DLC, 소프트웨어, 데모 등 비게임 콘텐츠 제외
- MySQL 데이터베이스에 수집된 정보 저장

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. Steam API 키 및 데이터베이스 설정:
   - `.env` 파일을 열고 `STEAM_API_KEY` 값을 자신의 Steam API 키로 변경하세요.
   - 데이터베이스 연결 정보도 `.env` 파일에 설정하세요.
   - Steam API 키는 [Steam Web API Key](https://steamcommunity.com/dev/apikey)에서 발급받을 수 있습니다.

3. 데이터베이스 테이블 생성:
```bash
mysql -u 사용자명 -p < create_tables.sql
```

## 사용 방법

스크립트를 실행하려면 다음 명령어를 사용하세요:

```bash
python steam_data_collector.py
```

## 수집되는 정보

- **기본 정보**: 게임 ID, 이름, 개발사, 배급사, 출시일, 가격, 메타크리틱 점수
- **상세 설명**: 짧은 설명과 상세 설명
- **장르 및 태그**: 게임의 장르와 사용자 태그
- **리뷰 정보**: 리뷰 수
- **시스템 요구사항**: 최소 시스템 요구사항

## 필터링 설정

기본적으로 리뷰 수가 1000개 이상인 게임만 수집합니다. 이 설정은 `steam_data_collector.py` 파일의 `MIN_REVIEWS` 변수를 수정하여 변경할 수 있습니다.

```python
MIN_REVIEWS = 1000  # 최소 리뷰 수 설정
```

또한 수집할 최대 게임 수도 변경할 수 있습니다:

```python
max_games = 100  # 수집할 최대 게임 수
```

## 콘텐츠 필터링

다음과 같은 콘텐츠는 자동으로 제외됩니다:

- DLC(다운로드 가능 콘텐츠)
- 소프트웨어
- 데모
- 사운드트랙
- 기타 비게임 콘텐츠

## 참고사항

- Steam API는 약 15만개 이상의 게임 목록을 제공하며, 그 중 리뷰 수가 많은 게임만 필터링합니다.
- 대량의 데이터 검사 시 시간이 상당히 오래 걸릴 수 있습니다. 
- 모든 게임을 검사하는 대신 무작위로 섞어서 다양한 게임을 검사합니다.
- API 요청 제한을 고려하여 각 게임 정보 요청 사이에 1초의 대기 시간이 있습니다. 