
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
                            
                        except Exception as e:
                            st.error(f"❌ GPT 분석 중 오류 발생: {str(e)}")
                           
            

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
    st.title("🎬 YouTube 영상 크롤링")

    keyword = st.text_input("🔍 YouTube 검색 키워드를 입력하세요 (예: ETF, 리스크, 위험, 변동성, 금융, 파생, 자산운용)")
    video_count = st.radio("🎯 수집할 영상 개수 선택", ["선택", 1, 2, 3], horizontal=True, index=0)
    full_caption_text = ''
    idx = 0
    
    if video_count == "선택":
        st.warning("🎬 영상 개수를 먼저 선택해주세요.")
    else:
        if not keyword:
            st.warning("키워드를 입력해주세요.")
        else:
            if video_count and int(video_count) > 3:
                st.warning("⚠ 메모리 문제로 영상은 최대 3개까지만 선택해주세요.")
            else:
                with st.spinner("YouTube 영상 검색 중..."):
                    videos = search_youtube_video(keyword, max_results=video_count)
                    if not videos:
                        st.error("❌ 자막이 있는 영상을 찾을 수 없습니다. 키워드를 바꿔보세요.")
                    
                    summary_list = []
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
                        try:
                            os.remove(audio_file)
                        except: pass
                        st.markdown(f"🗂️ 파일 경로: {safe_audio_path}")
                       
                        try:       # tmp_audio/audio_1.mp3
                            transcript = transcribe_audio(safe_audio_path)
                        
                            summary_list.append(f"[{idx+1}번째 영상 - 제목: {video['title']}]의 요약 및 분석 결과입니다.\n")
                            summary_list.append(summarize_text(transcript, keyword, video['title'])[:600])
                            summary_list.append("\n\n")
                            
                            del transcript  
                            try:
                                os.remove(safe_audio_path)
                            except: pass
                            #preview = summary[:500] + "..." if len(summary) > 500 else summary
                            #st.text_area("영상 요약내용", summary[:300] + "..." if len(summary) > 300 else summary, height=200)

                            #summary_list.append(f"[{idx+1} - {video['title']}]\n{summary}")

                            full_caption_text = "\n\n".join(summary_list)  
                        except Exception as e:
                            st.error(f"❌ 영상 내용 요약 중 오류 발생: {str(e)}")
                            
                        #with st.spinner("자막 수집 중..."):
                        #caption = get_video_captions(video['video_id'])
                        #if caption.startswith("❌"):
                        #    st.error(caption)
                        #    continue
                        #st.text_area("📝 자막", captions[:1500] + "..." if len(captions) > 1500 else captions, height=300)
                        #st.markdown("---")
                        
                        #preview = caption[:500] + "..." if len(caption) > 500 else caption
                        #st.text_area("자막 미리보기", preview, height=200)
                    
                        #full_caption_text += f"\n\n[영상 {idx+1} - {video['title']}]\n{caption}"

                if st.button("⚠ YouTube 영상 요약 기반 GPT-4 리스크 분석"):
                    if full_caption_text:
                        full_caption_text = full_caption_text[:3000]

                        with st.spinner("🧠 GPT-4 기반 위험요소 분석 중..."):
                            try:
                                risk_result = detect_risk(full_caption_text)
                                st.markdown("## ⚠️ GPT-4 리스크 탐지 결과")
                                st.warning(risk_result)
                                clear_tmp_audio()
                            except Exception as e:
                                st.error(f"❌ GPT 분석 실패: {str(e)}")
                                clear_tmp_audio()

                    else:
                        st.warning("수집된 영상 요약 정보가 없습니다.")
                        clear_tmp_audio()
            
            
   

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
