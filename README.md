### 영화 <백룸> 리뷰 데이터 (IMDb)
* **데이터 소개:**
  * **크롤링 사이트 링크:** [IMDb The Backrooms User Reviews](https://www.imdb.com/title/tt26657236/reviews/?sort=submissionDate&dir=desc)
  * **데이터 형식:** 별점(10점 만점), 날짜(MMM DD, YYYY), 내용(텍스트, 최대 300자)이 포함된 CSV 형태
  * **수집 개수:** 약 500개 이상
* **실행 방법:**
  * review_analysis 터미널에서 다음 명령어를 실행
  * python crawling/main.py -o ../database --all
 











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
