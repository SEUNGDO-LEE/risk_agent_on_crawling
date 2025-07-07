
import os
from openai import OpenAI
import streamlit as st
import glob
from content_loader import fetch_filtered_rss_articles, copy_to_temp, download_audio, transcribe_audio, summarize_text, clear_tmp_audio, search_youtube_video
from risk_detector import detect_risk, generate_response

st.set_page_config(page_title="Augmented LLM 콘텐츠 대응 Agent", layout="wide")

st.title("📺 Augmented LLM 기반 디지털 콘텐츠 대응 Agent")

# API 키 설정
os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_KEY']
#os.environ["YOUTUBE_API_KEY"] = st.secrets["YOUTUBE_KEY"]

tab1, tab2 = st.tabs(["📰 RSS 뉴스 분석", "📹 YouTube 영상 분석"])

with tab1:
    st.title("📰 뉴스 기사 크롤링")
    raw_keywords = st.text_input("🔍 뉴스 검색 키워드를 입력하세요 (예: ETF, 리스크, 위험, 변동성, 금융, 파생, 자산운용)")

    if raw_keywords:
        keyword_list = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]
        st.write("📌 입력된 키워드 리스트:", raw_keywords)
    
        with st.expander("📡 RSS Feed 기반 관련 뉴스 수집"):
            etf_articles = fetch_filtered_rss_articles(keyword_list)
            for art in etf_articles:
                st.markdown(f"#### 🔗 [{art['title']}]({art['link']})")
                st.write(art['summary'])
        
            all_summaries = "\n\n".join([f"[{art['title']}]\n{art['summary']}" for art in etf_articles])

            if st.button("⚠ 전체 뉴스 요약 기반 GPT-4 리스크 분석"):
               
                if len(all_summaries) < 100:
                    st.error("⚠ 분석할 뉴스 요약이 부족합니다.")
   
                else:
                    with st.spinner('리스크 분석 중'):
                        try:
                            MAX_TOKENS = 3000
                            if len(all_summaries.split()) > MAX_TOKENS:
                                all_summaries = " ".join(all_summaries.split()[:MAX_TOKENS])
                            result = detect_risk(all_summaries)
                            st.markdown("🧠 **GPT-4 리스크 분석 결과 (전체 기사 요약 기반)**:")
                            st.warning(result)
                            clear_tmp_audio()
                        except Exception as e:
                            st.error(f"❌ GPT 분석 중 오류 발생: {str(e)}")
                            clear_tmp_audio()

with tab2:
    st.title("🎬 YouTube 영상 크롤링")

    keyword = st.text_input("🔍 YouTube 검색 키워드를 입력하세요 (예: ETF, 리스크, 위험, 변동성, 금융, 파생, 자산운용)")
    video_count = st.radio("🎯 수집할 영상 개수 선택", ["선택", 1, 3, 5], horizontal=True, index=0)
    full_caption_text = ''
    idx = 0
    
    if video_count == "선택":
        st.warning("🎬 영상 개수를 먼저 선택해주세요.")
    else:
        if not keyword:
            st.warning("키워드를 입력해주세요.")
        else:
            
            with st.spinner("YouTube 영상 검색 중..."):
                videos = search_youtube_video(keyword, max_results=video_count)
                if not videos:
                    st.error("❌ 자막이 있는 영상을 찾을 수 없습니다. 키워드를 바꿔보세요.")
                
                for idx, video in enumerate(videos):
                    
                    st.markdown(f"### 🎥 {idx+1}. [{video['title']}])")
                    st.markdown(f"🔗 URL: {video['url']}")
                    
                    if video['url']:
                        audio_file = download_audio(video['url'], idx)
                    else:
                        st.error("❌ 오디오를 추출할 Youtube 영상이 없습니다.")
                    if not audio_file:
                        st.error("❌ 오디오 다운로드 실패")
                        continue

                    # ✅ 경로 안전한 디렉터리로 복사
                    safe_audio_path = copy_to_temp(audio_file)
                    st.markdown(f"🗂️ 파일 경로: {safe_audio_path}")
                    with st.spinner("🧠 영상 내용 요약 중..."):
                        try:       # tmp_audio/audio_1.mp3
                            transcript = transcribe_audio(safe_audio_path)
                            summary = summarize_text(transcript, keyword, video['title'])

                            #preview = summary[:500] + "..." if len(summary) > 500 else summary
                            st.text_area("영상 요약내용", summary, height=250)

                            full_caption_text += f"\n\n[영상 {idx+1} - {video['title']}]\n{summary}"
                        except Exception as e:
                            st.error(f"❌ 영상 내용 요약 중 오류 발생: {str(e)}")

            if st.button("⚠ YouTube 영상 요약 기반 GPT-4 리스크 분석"):
                if full_caption_text:
                    
                    with st.spinner("🧠 GPT-4 기반 위험요소 분석 중..."):
                        risk_result = detect_risk(full_caption_text)

                        st.markdown("## ⚠️ GPT-4 리스크 탐지 결과")
                        st.warning(risk_result)
                else:
                    st.warning("수집된 영상 요약 정보가 없습니다.")
