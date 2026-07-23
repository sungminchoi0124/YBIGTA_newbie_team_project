### 영화 <백룸> 리뷰 데이터 (IMDb)
* **데이터 소개:**
  * **크롤링 사이트 링크:** [IMDb The Backrooms User Reviews](https://www.imdb.com/title/tt26657236/reviews/?sort=submissionDate&dir=desc)
  * **데이터 형식:** 별점(10점 만점), 날짜(MMM DD, YYYY), 내용(텍스트, 최대 300자)이 포함된 CSV 형태
  * **수집 개수:** 약 500개 이상
* **실행 방법:**
  * review_analysis 터미널에서 다음 명령어를 실행
  * python crawling/main.py -o ../database --all
  * 만약 경로 문제 때문에 모듈을 찾을 수 없다고 뜨면, 대신 python -m review_analysis.crawling.main -o ./database --all 실행
  * 중요) 웹페이지가 켜지면, 30초 이내에 로그인해야 리뷰를 볼 수 있음. 실패시 로그인 할 준비하고 다시 명령어 실행
 

### 영화 <백룸> 리뷰 데이터 (Naver)
* **데이터 소개:**
  * **크롤링 사이트 링크:** [네이버 - 백룸 평점](https://search.naver.com/search.naver?where=nexearch&query=%EB%B0%B1%EB%A3%B8+%ED%8F%89%EC%A0%90)
  * **수집 방식:** 네이버 검색결과 관람평 위젯이 내부적으로 호출하는 JSON API(`nqapirender.nhn`, fileKey=movieKBPointAPI)를 직접 호출. 관람객(티켓 인증) 리뷰와 네티즌(비인증) 리뷰가 서로 다른 API 파라미터로 제공되어, 두 풀을 모두 수집한 뒤 `data-rating-id` 기준 중복 제거 후 합침
  * **데이터 형식:** 별점(score, 10점 만점), 작성일(date, YYYY.MM.DD HH:MM), 리뷰 내용(content), 작성자 ID(writer_id), 공감/비공감 수(like_count/dislike_count), 출처(source, 관람객/네티즌)가 포함된 CSV 형태
  * **수집 개수:** 507개 (관람객 리뷰 + 네티즌 리뷰 합산, 중복 제거)
 







### 웹 과제 실행 방법
1. pip install -r requirements.txt
2. uvicorn app.main:app --reload
3. http://localhost:8000/static/index.html 접속 후 UI 확인

### 팀 소개
* 7조
* 팀장: 최성민
* 팀원: 박소영, 송지훈

### 자기소개
**최성민 (22, 응용통계학과)**
**박소영**
**송지훈**
