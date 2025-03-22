import os
import re
import subprocess
import requests
from bs4 import BeautifulSoup

# 環境変数から検索キーワードを取得（指定がなければ 'ナードコア' をデフォルトとする）
search_keyword = os.environ.get("SEARCH_KEYWORD", "ナードコア")
# Yahoo リアルタイム検索の URL（検索キーワードは URL エンコード済みである前提）
URL = f"https://search.yahoo.co.jp/realtime/search?p={search_keyword}&ei=UTF-8&ifr=tl_sc"

print(f"検索キーワード: {search_keyword}")
print(f"取得対象URL: {URL}")

# Yahoo のページを取得
response = requests.get(URL)
response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

results = []

# 「https://x.com/」で始まるリンクをすべて抽出
for a in soup.find_all("a", href=re.compile(r"^https://x\.com/")):
    account = a.get_text(strip=True)
    href = a.get("href")
    
    # ツイート本文の取得例:
    # ・まずは a タグの親要素内に、クラス名に "TweetText" を含む要素があれば取得
    tweet_message = ""
    parent = a.parent
    if parent:
        tweet_div = parent.find("div", class_=re.compile("TweetText"))
        if tweet_div:
            tweet_message = tweet_div.get_text(strip=True)
        else:
            # もしくは a タグの直後のテキストノードなどを試す（ページ構造に合わせて調整）
            next_elem = a.find_next(string=True)
            if next_elem:
                tweet_message = next_elem.strip()
    
    # 結果が空の場合、不要なリンクの可能性もあるのでスキップ
    if account or tweet_message:
        results.append((account, href, tweet_message))

# 結果を output.txt に書き出し
with open("output.txt", "w", encoding="utf-8") as f:
    for account, href, tweet in results:
        f.write(f"Account: {account}\n")
        f.write(f"URL: {href}\n")
        f.write(f"Tweet: {tweet}\n")
        f.write("----\n")

print("output.txt に結果を出力しました。")

# Git の設定・コミット・プッシュ処理
try:
    subprocess.run(["git", "config", "--global", "user.email", "action@github.com"], check=True)
    subprocess.run(["git", "config", "--global", "user.name", "GitHub Action"], check=True)
    subprocess.run(["git", "add", "output.txt"], check=True)
    
    # 変更がある場合のみコミット
    commit = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if commit.returncode != 0:
        subprocess.run(["git", "commit", "-m", f"Update output.txt for keyword: {search_keyword}"], check=True)
        # GITHUB_TOKEN を用いてリモートにプッシュ
        repo = os.environ.get("GITHUB_REPOSITORY")
        token = os.environ.get("GITHUB_TOKEN")
        push_url = f"https://{token}@github.com/{repo}.git"
        subprocess.run(["git", "push", push_url, "HEAD:refs/heads/main"], check=True)
        print("リポジトリにプッシュしました。")
    else:
        print("変更はありません。")
except Exception as e:
    print("Git コミットまたはプッシュに失敗しました:", e)
