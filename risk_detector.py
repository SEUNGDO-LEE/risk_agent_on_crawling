# risk_detector.py
import streamlit as st
import pandas as pd
import numpy as np
import os
from openai import OpenAI

def detect_risk(text: str) -> str:
    prompt = (
        "다음 콘텐츠에서 사회적, 정치적, 윤리적 또는 법적 리스크 요소를 요약해줘. "
        "리스크가 있는 경우 해당 문장을 직접 인용해서 표시해줘.\n\n"
        f"{text}"
    )
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_response(user_question: str, content_context: str) -> str:
    prompt = (
        "아래 콘텐츠 내용을 참고하여 사용자의 질문에 대해 중립적이고 신뢰성 있는 답변을 해줘.\n\n"
        f"[콘텐츠 요약]: {content_context}\n"
        f"[질문]: {user_question}"
    )
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
