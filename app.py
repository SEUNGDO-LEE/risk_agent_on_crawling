
import os
from openai import OpenAI
import streamlit as st

from content_loader import fetch_filtered_rss_articles  , get_video_captions_by_keyword, search_youtube_video, get_video_captions
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
                with st.spinner('리스크 분석 중'):
                    result = detect_risk(all_summaries)
                    st.markdown("🧠 **GPT-4 리스크 분석 결과 (전체 기사 요약 기반)**:")
                    st.warning(result)
            

#with tab1:
#    st.subheader("🔍 RSS Feed 기반 뉴스 수집 및 위험 탐지")
#   feed_url = st.text_input("RSS Feed URL", value="https://www.boannews.com/media/news_rss.xml")
#   if st.button("RSS 분석 시작"):
#       articles = fetch_rss_articles(feed_url)
#       for article in articles:
#           st.markdown(f"### 📰 {article['title']}")
#          st.write(article['summary'])
#         with st.expander("📛 GPT-4 기반 리스크 탐지 결과"):
#            result = detect_risk(article['summary'])
#           st.warning(result)

with tab2:
    st.title("🎬 유튜브 자막 크롤링")

    keyword = st.text_input("🔍 Youtube 검색 키워드를 입력하세요 (예: ETF, 리스크, 위험, 변동성, 금융, 파생, 자산운용)")
    video_count = st.radio("🎯 수집할 영상 개수 선택", ["선택", 1, 3, 5], horizontal=True, index=0)
    full_caption_text = ""
    
    if video_count == "선택":
        st.warning("🎬 영상 개수를 먼저 선택해주세요.")
    else:
        if not keyword:
            st.warning("키워드를 입력해주세요.")
        else:
            
            with st.spinner("유튜브 영상 검색 중..."):
                videos = search_youtube_video(keyword, max_results=video_count)

                
                for idx, video in enumerate(videos):
                    st.markdown(f"### 🎥 {idx+1}. [{video['title']}])")
                    st.markdown(f"🔗URL: [{video['url']})")
                    #with st.spinner("자막 수집 중..."):
                    caption = get_video_captions(video['video_id'])
                    #st.text_area("📝 자막", captions[:1500] + "..." if len(captions) > 1500 else captions, height=300)
                    #st.markdown("---")
                    
                    preview = caption[:500] + "..." if len(caption) > 500 else caption
                    st.text_area("자막 미리보기", preview, height=200)
                
                    full_caption_text += f"\n\n[영상 {idx+1} - {video['title']}]\n{caption}"

    if full_caption_text:
    
        if st.button("⚠ Youtube 자막 기반 GPT-4 리스크 분석", key="video_risk"):
                
            with st.spinner("🧠 GPT-4 기반 위험요소 분석 중..."):
                risk_result = detect_risk(full_caption_text)

                st.markdown("## ⚠️ GPT-4 리스크 탐지 결과")
                st.warning(risk_result)
            
   

    #if keyword:
    #     with st.spinner('자막 크롤링 중'):
    #        captions = get_video_captions_by_keyword(keyword)
    #        st.text_area("🎙 자막 내용", captions, height=400)
    #        
    #        if st.button("⚠ Youtube 자막 기반 GPT-4 리스크 분석"):
    #             
    #            with st.spinner('리스크 분석 중'):
    #                result = detect_risk(all_summaries)
    #                st.markdown("🧠 **GPT-4 리스크 분석 결과 (Youtube 자막 기반)**:")
    #                st.warning(result)

    #st.subheader("📼 YouTube 자막 수집 및 질의응답")
    #youtube_id = st.text_input("YouTube Video ID 입력", value="Ks-_Mh1QhMc")
    #if st.button("자막 수집 및 분석"):
    #    caption = get_video_captions(youtube_id)
    #    st.text_area("🎬 자막 일부", caption[:1000])
    #    with st.expander("📛 GPT-4 기반 자막 리스크 분석"):
    #        result = detect_risk(caption[:1000])
    #        st.warning(result)

    # user_question = st.text_input("💬 사용자 질문 입력")
    # if st.button("💡 GPT-4 응답 생성"):
    #    if caption:
    #        answer = generate_response(user_question, caption[:2000])
    #        st.success(answer)
    #    else:
    #        st.error("먼저 자막을 수집해주세요.")