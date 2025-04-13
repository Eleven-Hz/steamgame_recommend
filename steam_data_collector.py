import os
import requests
import mysql.connector
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수 로드
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))  # 포트 정보 추가
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'steam_games')
MIN_REVIEWS = 1000  # 최소 리뷰 수 설정

def get_db_connection():
    """데이터베이스 연결을 생성합니다."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,  # 포트 정보 추가
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def insert_game(cursor, game_data):
    """게임 정보를 데이터베이스에 삽입합니다."""
    try:
        # 게임 기본 정보 삽입
        cursor.execute("""
            INSERT INTO games (
                game_id, name, developer, publisher, release_date,
                short_description, detailed_description, price,
                metacritic_score, minimum_requirements, review_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                developer = VALUES(developer),
                publisher = VALUES(publisher),
                release_date = VALUES(release_date),
                short_description = VALUES(short_description),
                detailed_description = VALUES(detailed_description),
                price = VALUES(price),
                metacritic_score = VALUES(metacritic_score),
                minimum_requirements = VALUES(minimum_requirements),
                review_count = VALUES(review_count)
        """, (
            game_data['game_id'],
            game_data['name'],
            game_data['developer'],
            game_data['publisher'],
            game_data['release_date'],
            game_data['short_description'],
            game_data['detailed_description'],
            game_data['price'],
            game_data['metacritic_score'],
            game_data['minimum_requirements'],
            game_data['review_count']
        ))

        # 장르 정보 삽입
        for genre in game_data['genres']:
            # 장르가 존재하는지 확인하고 없으면 추가
            cursor.execute("INSERT IGNORE INTO genres (name) VALUES (%s)", (genre,))
            
            # 장르 ID 가져오기
            cursor.execute("SELECT genre_id FROM genres WHERE name = %s", (genre,))
            genre_id = cursor.fetchone()[0]
            
            # 게임-장르 관계 추가
            cursor.execute("""
                INSERT IGNORE INTO game_genres (game_id, genre_id)
                VALUES (%s, %s)
            """, (game_data['game_id'], genre_id))

    except mysql.connector.Error as err:
        print(f"데이터베이스 오류: {err}")

def get_game_reviews_count(app_id):
    """게임의 리뷰 수를 가져옵니다."""
    url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all&purchase_type=all&num_per_page=0"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # 리뷰 총 개수
        review_count = data.get('query_summary', {}).get('total_reviews', 0)
        return review_count
        
    except requests.exceptions.RequestException as e:
        print(f"리뷰 정보 요청 중 오류 발생: {e}")
        return 0

def get_game_details(app_id):
    """게임 상세 정보를 가져옵니다."""
    base_url = f"https://store.steampowered.com/api/appdetails"
    params = {
        'appids': app_id,
        'cc': 'us',
        'l': 'english'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        game_data = data.get(str(app_id), {}).get('data', {})
        
        if game_data:
            # 앱 유형 확인
            app_type = game_data.get('type', '').lower()
            
            # DLC, 데모, 소프트웨어 등 제외하고 게임만 수집
            if app_type != 'game':
                print(f"앱 ID {app_id} ({game_data.get('name', 'N/A')})는 게임이 아닌 {app_type}입니다. 건너뜁니다.")
                return None
                
            # DLC 확인 (일부 DLC는 type이 game으로 표시될 수 있음)
            categories = game_data.get('categories', [])
            for category in categories:
                if category.get('id') == 21:  # 21은 DLC 카테고리 ID
                    print(f"앱 ID {app_id} ({game_data.get('name', 'N/A')})는 DLC입니다. 건너뜁니다.")
                    return None
            
            # 리뷰 수 가져오기
            review_count = get_game_reviews_count(app_id)
            
            # 최소 리뷰 수 확인
            if review_count < MIN_REVIEWS:
                print(f"게임 '{game_data.get('name')}' 리뷰 수가 부족합니다 ({review_count}/{MIN_REVIEWS})")
                return None
            
            # 날짜 형식 변환
            release_date = game_data.get('release_date', {}).get('date', '')
            try:
                release_date = datetime.strptime(release_date, '%d %b, %Y').date()
            except:
                release_date = None

            return {
                'game_id': app_id,
                'name': game_data.get('name', 'N/A'),
                'developer': ', '.join(game_data.get('developers', ['N/A'])),
                'publisher': ', '.join(game_data.get('publishers', ['N/A'])),
                'release_date': release_date,
                'short_description': game_data.get('short_description', 'N/A'),
                'detailed_description': game_data.get('detailed_description', 'N/A'),
                'genres': [genre['description'] for genre in game_data.get('genres', [])],
                'price': game_data.get('price_overview', {}).get('final_formatted', 'Free'),
                'metacritic_score': game_data.get('metacritic', {}).get('score'),
                'minimum_requirements': str(game_data.get('pc_requirements', {}).get('minimum', 'N/A')),
                'review_count': review_count
            }
            
    except requests.exceptions.RequestException as e:
        print(f"게임 정보 요청 중 오류 발생: {e}")
        return None

def get_game_tags(app_id):
    """게임의 태그 정보를 가져옵니다."""
    base_url = f"https://store.steampowered.com/app/{app_id}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        # Extract tag information from HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find elements containing tag information
        tag_elements = soup.select('.glance_tags.popular_tags a')
        tags = [tag.text.strip() for tag in tag_elements]
        
        return tags
        
    except requests.exceptions.RequestException as e:
        print(f"태그 정보 요청 중 오류 발생: {e}")
        return []

def get_all_games():
    """Steam의 모든 게임 목록을 가져옵니다."""
    base_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        
        data = response.json()
        games = data.get('applist', {}).get('apps', [])
        
        print(f"총 {len(games)}개의 게임을 가져왔습니다.")
        return games
        
    except requests.exceptions.RequestException as e:
        print(f"게임 목록 요청 중 오류 발생: {e}")
        return []

def collect_games():
    """Steam의 전체 게임 중에서 리뷰 수가 많은 게임을 수집합니다."""
    try:
        # 모든 게임 목록 가져오기
        all_games = get_all_games()
        
        if not all_games:
            print("게임 목록을 가져오지 못했습니다.")
            return
        
        # 데이터베이스 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n게임 정보 수집 시작:")
        collected_count = 0
        processed_count = 0
        max_games = 100  # 수집할 최대 게임 수
        
        # 게임 목록을 무작위로 섞어서 다양한 게임을 검사
        random.shuffle(all_games)
        
        for game in all_games:
            if collected_count >= max_games:  # 지정된 수만큼 수집
                break
                
            # 처리한 게임 수 표시 (5000개마다)
            processed_count += 1
            if processed_count % 5000 == 0:
                print(f"{processed_count}개의 게임 처리 완료, 현재까지 {collected_count}개 수집됨")
            
            app_id = game.get('appid')
            
            # 정보를 수집할 때마다 게임 이름 출력
            if game.get('name'):
                print(f"\n게임 ID {app_id} ({game.get('name')}) 정보 수집 중...")
            else:
                print(f"\n게임 ID {app_id} 정보 수집 중...")
            
            game_data = get_game_details(app_id)
            if game_data:
                # 태그 정보 추가
                game_data['tags'] = get_game_tags(app_id)
                
                insert_game(cursor, game_data)
                print(f"게임 '{game_data['name']}' 정보 저장 완료 (리뷰 수: {game_data['review_count']})")
                collected_count += 1
                
                # 변경사항 저장 (10개마다)
                if collected_count % 10 == 0:
                    conn.commit()
                    print(f"현재까지 {collected_count}개 게임 정보 저장됨")
            
            # API 요청 제한을 고려하여 잠시 대기
            time.sleep(1)
        
        # 최종 변경사항 저장
        conn.commit()
        print(f"\n총 {collected_count}개 게임 정보 수집 완료!")
        
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
    except mysql.connector.Error as err:
        print(f"데이터베이스 오류: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    collect_games() 