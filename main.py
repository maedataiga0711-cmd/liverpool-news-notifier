import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import requests
from bs4 import BeautifulSoup
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
import schedule
import time
from datetime import datetime

# ========== 設定 ==========
CHANNEL_ACCESS_TOKEN = "".strip()
USER_ID = "".strip()

# 通知時刻の設定（好きな時間に変更できます）
NOTIFICATION_TIMES = ["08:00", "12:00", "20:00"]
# ==========================

def send_line_message(message):
    """LINEにメッセージを送信"""
    try:
        configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=USER_ID,
                    messages=[TextMessage(text=message)]
                )
            )
        print("✅ LINE送信成功")
        return True
    except Exception as e:
        print(f"❌ LINE送信エラー: {e}")
        return False

def get_liverpool_news():
    """リヴァプール関連ニュースを取得"""
    url = "https://www.bbc.com/sport/football/teams/liverpool"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print(f"📡 アクセス中: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✅ ページ取得成功（ステータス: {response.status_code}）")
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        news_list = []
        headlines = soup.find_all(['h1', 'h2', 'h3'])
        print(f"🔍 見出しを{len(headlines)}件発見")
        
        for headline in headlines:
            title = headline.get_text(strip=True)
            
            if len(title) < 10:
                continue
            
            link_tag = headline.find_parent('a')
            if link_tag and link_tag.get('href'):
                link = link_tag['href']
                if link.startswith('/'):
                    link = "https://www.bbc.com" + link
            else:
                link = url
            
            news_item = {"title": title, "url": link}
            
            if news_item not in news_list:
                news_list.append(news_item)
                print(f"  📰 追加: {title[:50]}...")
        
        return news_list
        
    except Exception as e:
        print(f"❌ ニュース取得エラー: {e}")
        return []

def run_notification():
    """通知を実行する関数（スケジュールから呼ばれる）"""
    print("\n" + "=" * 60)
    print(f"⏰ スケジュール実行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # ニュース取得
    print("\n🔍 ニュース取得中...")
    all_news = get_liverpool_news()
    print(f"\n📊 合計 {len(all_news)} 件のニュース候補を発見")
    
    if not all_news:
        print("⚠️ ニュースが取得できませんでした")
        return
    
    # キーワードフィルタリング
    print("\n🔍 キーワードフィルタリング中...")
    KEYWORDS = ["Liverpool", "LFC", "Klopp", "Salah", "Anfield", "リヴァプール"]
    
    matched_news = []
    for item in all_news:
        if any(kw.lower() in item['title'].lower() for kw in KEYWORDS):
            matched_news.append(item)
            print(f"  ✅ マッチ: {item['title'][:50]}...")
    
    print(f"\n📊 {len(matched_news)} 件がキーワードにマッチ")
    
    if not matched_news:
        print("⚠️ キーワードマッチなし")
        matched_news = all_news[:3]
    
    # 最新3件に絞る
    final_news = matched_news[:3]
    
    # メッセージ作成
    now = datetime.now()
    message = f"🔴 リヴァプール 最新ニュース\n"
    message += f"📅 {now.strftime('%Y/%m/%d %H:%M')}\n\n"
    
    for i, news in enumerate(final_news, 1):
        message += f"{i}. {news['title']}\n"
        message += f"🔗 {news['url']}\n\n"
    
    # LINE送信
    print("\n📤 LINE送信中...")
    success = send_line_message(message)
    
    if success:
        print("✅ 通知完了！")
    else:
        print("❌ 送信失敗")
    
    print("=" * 60)
    print("次の実行を待機中...\n")

def main():
    """メイン関数"""
    print("\n" + "=" * 60)
    print("🔴 リヴァプール ニュース自動通知システム")
    print("=" * 60)
    print("このプログラムは設定された時間に自動でニュースを通知します")
    print(f"通知時刻: {', '.join(NOTIFICATION_TIMES)}")
    print("終了するには Ctrl+C を押してください")
    print("=" * 60)
    
    # スケジュール設定
    for time_str in NOTIFICATION_TIMES:
        schedule.every().day.at(time_str).do(run_notification)
        print(f"⏰ {time_str} に通知を設定")
    
    print("=" * 60)
    
    # 初回実行するか確認
    response = input("\n今すぐテスト実行しますか？ (y/n): ")
    if response.lower() == 'y':
        run_notification()
    
    print("\n⏰ スケジューラー起動中...")
    print("設定時刻になると自動で通知します\n")
    
    # 無限ループでスケジュール実行
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    except KeyboardInterrupt:
        print("\n\n👋 プログラムを終了します")

if __name__ == "__main__":
    main()
