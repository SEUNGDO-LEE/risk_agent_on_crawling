# content_loader.py
import os
import subprocess
from openai import OpenAI
# pip install yt-dlp openai
import streamlit as st
import isodate  # pip install isodate
import assemblyai as aai

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
# pip install --upgrade google-api-python-client
from googleapiclient.discovery import build
import shutil

os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_KEY']
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
os.environ["YOUTUBE_API_KEY"] = st.secrets["YOUTUBE_KEY"]

os.environ["ASSEMBLY_API_KEY"] = st.secrets["ASSEMBLYAI_KEY"]
aai.settings.api_key = os.environ["ASSEMBLY_API_KEY"] 

RSS_FEEDS = [
    "https://seekingalpha.com/etfs-and-funds/etf-articles.xml",
    "https://www.hani.co.kr/rss/economy/",
    "https://www.boannews.com/media/news_rss.xml",
    "https://www.yna.co.kr/finance/all?site=rss"
]


@st.cache_resource
def get_youtube_api():
    return build("youtube", "v3", developerKey=os.environ["YOUTUBE_KEY"])

youtube = get_youtube_api()

def get_video_metadata(video_id):
    get_youtube_api()
    res = youtube.videos().list(part="snippet", id=video_id).execute()
    snippet = res["items"][0]["snippet"]
    return snippet["title"], snippet["description"]

def summarize_with_gpt(title, description, transcript):
    prompt = f"""다음은 유튜브 영상의 제목과 설명과 자막이야:

제목: {title}
설명: {description}
자막: {transcript}

이 내용을 500자 이내로 요약해줘. 사회적·정치적·윤리적 또는 법적 리스크가 있다면 함께 알려줘.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_transcript(video_id, lang_list=["ko", "en"]):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_list)
        text = " ".join([seg["text"] for seg in transcript])
        return text
    except Exception as e:
        return f"❌ 자막 불러오기 실패: {str(e)}"
    

def copy_to_temp(filepath):
    filename = os.path.basename(filepath)
    safe_dir = "tmp_audio"

    if not os.path.exists(safe_dir):
        os.makedirs(safe_dir)

    safe_path = os.path.join(safe_dir, filename)
    shutil.copyfile(filepath, safe_path)
    return safe_path

#KEYWORDS = ["ETF", "리스크", "위험", "변동성", "금융", "파생", "자산운용"]
def download_audio(youtube_url, idx):
    filename = f"audio_{idx}.m4a"
    try:
        subprocess.run([
            "yt-dlp",
            "-f", "bestaudio[ext=m4a]",
            "-o", filename,
            youtube_url
        ], check=True)
        return filename
    except subprocess.CalledProcessError:
        return None
    
def transcribe_audio(filepath):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(filepath, config=aai.TranscriptionConfig(
        auto_highlights=True,
        summarization=True,
        summary_type="bullets",
        summary_model="informative"      # 필수 값!
    ))
    return transcript.text
    
def summarize_text(text, keyword, title):
    prompt = (
        f"다음은 유튜브 영상의 전사 내용이야\n"
        f"전사 내용: {text}\n"
        f"이 영상 검색에 사용된 키워드는 {keyword}이고 영상의 제목은 {title}이야. 이 내용을 400자 이내로 요약해줘.\n"
        "가능하다면 사회적·정치적·윤리적 또는 법적 리스크 요소가 있는지도 추정해줘.\n"
    )   
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def clear_tmp_audio():
    shutil.rmtree("tmp_audio", ignore_errors=True)
                              
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

def get_video_duration_seconds(video_id):
    
    response = youtube.videos().list(
        part="contentDetails",
        id=video_id
    ).execute()

    duration_iso = response["items"][0]["contentDetails"]["duration"]
    duration = isodate.parse_duration(duration_iso)
    return duration.total_seconds()

def search_youtube_video(query):
    max_attempts = 5  # 무한루프 방지를 위한 안전장치
    attempts = 0

    while attempts < max_attempts:
        attempts += 1

        search_response = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=10,
            type="video"
        ).execute()

        for item in search_response["items"]:
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                duration_sec = get_video_duration_seconds(video_id)
                if duration_sec >= 200:
                    return [{
                        "video_id": video_id,
                        "title": title,
                        "url": url
                    }]
            except Exception as e:
                print(f"⛔ duration 조회 실패: {e}")
                continue

    return []  # 조건을 만족하는 영상이 없을 경우
