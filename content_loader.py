# content_loader.py
import os
from openai import OpenAI
import streamlit as st

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
# pip install --upgrade google-api-python-client
from googleapiclient.discovery import build

os.environ["YOUTUBE_API_KEY"] = st.secrets["YOUTUBE_KEY"]

RSS_FEEDS = [
    "https://seekingalpha.com/etfs-and-funds/etf-articles.xml",
    "https://www.hani.co.kr/rss/economy/",
    "https://www.boannews.com/media/news_rss.xml",
    "https://www.yna.co.kr/finance/all?site=rss"
]

#KEYWORDS = ["ETF", "리스크", "위험", "변동성", "금융", "파생", "자산운용"]

def fetch_filtered_rss_articles(keyword_list):
    results = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            content = title + " " + summary

            if any(kw.lower() in content.lower() for kw in keyword_list):
                results.append({
                    "title": title,
                    "summary": summary,
                    "link": getattr(entry, "link", "#")
                })

    return results


def search_youtube_video(query, max_results=1):
    youtube = build("youtube", "v3", developerKey=os.environ["YOUTUBE_API_KEY"])
    search_response = youtube.search().list(
        q=query,
        part="snippet",
        maxResults=max_results,
        type="video"
    ).execute()

    videos = []
    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"  # ✅ 요 줄 추가
        videos.append({"video_id": video_id, "title": title, "url" : url})
    return videos

def get_video_captions(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko", "en"])
        text = " ".join([entry["text"] for entry in transcript])
        return text
    except Exception as e:
        return f"❌ 자막 수집 실패: {str(e)}"
    
def get_video_captions_by_keyword(keyword):
    search_results = search_youtube_video(keyword)
    if not search_results:
        return "❌ 관련 영상을 찾을 수 없습니다."

    video_id = search_results[0]["video_id"]
    title = search_results[0]["title"]
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        text = " ".join([entry['text'] for entry in transcript])
        return f"🎥 제목: {title}\n\n{text}"
    except Exception as e:
        return f"⚠ 자막 불러오기 실패: {str(e)}"

