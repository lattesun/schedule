import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="다단계 스케줄러",
    page_icon="📅",
    layout="wide"
)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS schedules
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         title TEXT NOT NULL,
         description TEXT,
         start_date DATE NOT NULL,
         end_date DATE NOT NULL,
         schedule_type TEXT NOT NULL,
         notification BOOLEAN,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

# 사이드바 - 시간 단위 선택
def sidebar():
    st.sidebar.title("📅 다단계 스케줄러")
    schedule_type = st.sidebar.selectbox(
        "시간 단위 선택",
        ["연간", "반기", "분기", "월간", "주간"]
    )
    return schedule_type

# 일정 추가 폼
def add_schedule_form():
    with st.form("schedule_form"):
        st.subheader("새 일정 추가")
        title = st.text_input("제목")
        description = st.text_area("설명")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일")
        with col2:
            end_date = st.date_input("종료일")
        schedule_type = st.selectbox("일정 유형", ["연간", "반기", "분기", "월간", "주간"])
        notification = st.checkbox("알림 설정")
        
        submitted = st.form_submit_button("일정 추가")
        if submitted and title:
            save_schedule(title, description, start_date, end_date, schedule_type, notification)
            st.success("일정이 추가되었습니다!")

# 일정 저장
def save_schedule(title, description, start_date, end_date, schedule_type, notification):
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO schedules (title, description, start_date, end_date, schedule_type, notification)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, description, start_date, end_date, schedule_type, notification))
    conn.commit()
    conn.close()

# 일정 표시
def display_schedules(schedule_type):
    conn = sqlite3.connect('scheduler.db')
    df = pd.read_sql_query(
        "SELECT * FROM schedules WHERE schedule_type=?",
        conn,
        params=(schedule_type,)
    )
    conn.close()

    if not df.empty:
        st.subheader(f"{schedule_type} 일정")
        # Plotly를 사용한 간트 차트
        fig = px.timeline(
            df,
            x_start="start_date",
            x_end="end_date",
            y="title",
            title=f"{schedule_type} 일정 현황"
        )
        st.plotly_chart(fig, use_container_width=True)

        # 상세 일정 목록
        for _, row in df.iterrows():
            with st.expander(f"{row['title']} ({row['start_date']} ~ {row['end_date']})"):
                st.write(f"설명: {row['description']}")
                st.write(f"알림 설정: {'예' if row['notification'] else '아니오'}")
                if st.button(f"삭제 {row['id']}", key=f"del_{row['id']}"):
                    delete_schedule(row['id'])
                    st.experimental_rerun()

# 일정 삭제
def delete_schedule(schedule_id):
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id=?", (schedule_id,))
    conn.commit()
    conn.close()

def main():
    # 데이터베이스 초기화
    init_db()
    
    # 사이드바
    schedule_type = sidebar()
    
    # 메인 영역
    st.title("📅 다단계 스케줄러")
    
    # 2단 레이아웃
    col1, col2 = st.columns([2, 1])
    
    with col1:
        display_schedules(schedule_type)
    
    with col2:
        add_schedule_form()

if __name__ == "__main__":
    main() 