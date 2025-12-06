# 🗝️ Key-Pick: 프랜차이즈 방탈출 카페 예약 및 통합 운영 시스템

> `Key-Pick`은 다수의 지점을 보유한 프랜차이즈 방탈출 카페를 위한 `올인원(All-in-One) 솔루션`입니다.  
> 고객에게는 편리한 `실시간 예약 및 커뮤니티` 서비스를, 관리자에게는 `지점 운영 효율화 및 데이터 기반의 매출 분석` 기능을 제공합니다.

-----

## 목차

1.  [프로젝트 소개](#프로젝트-소개)
2.  [주요 기능](#주요-기능)
3.  [기술 스택](#기술-스택)
4.  [데이터베이스 구조 (ERD)](#데이터베이스-구조-erd)
5.  [설치 및 실행 방법](#설치-및-실행-방법)
6.  [팀원 및 역할](#팀원-및-역할)

-----

## 프로젝트 소개

기존 방탈출 카페 예약 시스템의 한계를 넘어, 본사(Admin) - 지점(Branch) - 테마(Theme)로 이어지는 체계적인 프랜차이즈 관리 구조를 구현했습니다.

### 프로젝트 특징

  * **계층적 권한 관리 (RBAC):** 고객, 테마 관리자(직원), 지점 관리자(점장), 총괄 관리자(본사) 4단계 권한 시스템
  * **데이터 무결성 보장:** 예약과 결제 과정에 Transaction(Atomic)을 적용하여 중복 예약 및 데이터 불일치 원천 차단
  * **시각화된 통계 대시보드:** Chart.js를 활용하여 일별 예약 추이, 지점별 매출 순위, 인기 테마 등을 시각적으로 분석
  * **강력한 검색 필터링:** 지점, 장르뿐만 아니라 난이도, 가격대별 상세 필터링 및 다양한 정렬(평점순, 리뷰순) 지원

-----

## 주요 기능

### 1. 고객 (Customer)

  * **테마 탐색:** 원하는 지역, 장르, 난이도, 가격대에 맞춰 테마를 검색하고 최신순/평점순으로 정렬
  * **실시간 예약:** 날짜와 시간을 선택하여 즉시 예약 및 (가상) 결제 진행
  * **마이페이지:** 나의 예약 내역 확인, 취소, 이용 완료 후 리뷰 작성 및 관리

### 2. 테마 관리자 (Theme Manager / 직원)

  * **운영 대시보드:** 담당 지점의 당일 예약 스케줄을 타임라인으로 확인
  * **입/퇴실 관리:** 고객 방문 시 입실(Check-in) 처리 및 노쇼(No-Show) 관리
  * **시설 점검:** 테마 내 소품 파손 등 이슈 발생 시 보고서 작성 및 테마 상태 변경(운영 중단)

### 3. 지점 관리자 (Branch Manager / 점장)

  * **지점 관리:** 테마의 기본 가격 및 이벤트 할인율 수정, 활성화 여부 설정
  * **스케줄링:** 소속 직원의 근무 스케줄 등록, 수정, 삭제
  * **매출 분석:** 이번 달 총 매출, 예약 건수, 객단가 등을 한눈에 파악

### 4. 총괄 관리자 (Admin / 본사)

  * **시스템 관리:** 신규 지점 개설 및 테마 등록/삭제
  * **전체 통계:** 전 지점 매출 비교, 브랜드 전체 성장 추이(가입자, 예약 수) 분석
  * **공지사항:** 전체 시스템 공지 발행

-----

## 기술 스택

| 분류 | 기술 |
| :--- | :--- |
| **Backend** | Python, Django |
| **Database** | PostgreSQL |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Library** | Chart.js (Data Visualization) |

-----

## 데이터베이스 구조 (ERD)

총 10개의 테이블로 구성된 정규화된 데이터베이스 설계를 따릅니다.

  - 주요 관계: `Branch` (1:N) `Theme` (1:N) `Reservation` (1:1) `Payment`
  - 특징: `BranchAssignment` 테이블을 통해 관리자와 지점 간의 N:M 배정 관계를 해소했습니다.

<img src="https://github.com/user-attachments/assets/96c238ee-1e1a-430d-8524-d9623fe2370a" width="100%" alt="">

-----

## 설치 및 실행 방법

이 프로젝트를 로컬 환경에서 실행하기 위한 단계입니다.

### 1. 프로젝트 클론 (Clone)

```bash
git clone https://github.com/HSHwan/key-pick.git
cd key-pick
```

### 2. 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
source venv/Scripts/activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

*(만약 `requirements.txt`가 없다면: `pip install django`)*

### 4. 데이터베이스 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. 슈퍼유저(총괄 관리자) 생성

관리자 페이지 및 전체 통계 접근을 위해 관리자 계정이 필요합니다.

```bash
python manage.py createsuperuser
# ID, Email, Password 입력
```

### 6. 서버 실행

```bash
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000/` 으로 접속합니다.

-----

## 테스트 가이드

1.  **초기 데이터 설정:**
      * `/admin`에 접속하여 `Branch`(지점)와 `Theme`(테마) 데이터를 먼저 생성해주세요.
2.  **관리자 배정:**
      * 회원가입 후, Admin 페이지의 `Branch Assignment` 메뉴에서 해당 회원을 특정 지점의 관리자로 배정해야 매니저 기능을 테스트할 수 있습니다.
3.  **예약 테스트:**
      * 로그아웃 후 일반 고객 계정으로 로그인하여 테마를 예약해보세요.

-----

## 팀원 및 역할

| 이름 | 역할 | 담당 업무 |
| :--- | :--- | :--- |
| [**황수환**](https://github.com/HSHwan) | **Backend / PM** | DB 설계, 예약/결제 트랜잭션 구현, 검색 알고리즘, 시스템 아키텍처 설계 |
| [**배성윤**](https://github.com/aeuyui) | **Frontend / Manager** | UI/UX 디자인, 관리자(지점/테마/총괄) 기능 구현, 대시보드 시각화|

-----

© 2025 Key-Pick Project. All Rights Reserved.