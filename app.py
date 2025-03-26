import streamlit as st
import pandas as pd
import datetime
import sqlite3
import os
from dateutil.parser import parse

# Plotly를 선택적으로 가져오기
try:
    import plotly.express as px
    plotly_available = True
except ImportError:
    plotly_available = False
    st.error("Plotly 라이브러리가 설치되어 있지 않습니다. 'pip install plotly' 명령어로 설치하세요.")

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS schedules
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     title TEXT NOT NULL,
     description TEXT,
     date TEXT NOT NULL,
     time TEXT NOT NULL,
     priority TEXT NOT NULL)
    ''')
    conn.commit()
    conn.close()

# 일정 추가
def add_schedule(title, description, date, time, priority):
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('''
    INSERT INTO schedules (title, description, date, time, priority)
    VALUES (?, ?, ?, ?, ?)
    ''', (title, description, date, time, priority))
    conn.commit()
    conn.close()

# 일정 불러오기
def get_all_schedules():
    conn = sqlite3.connect('scheduler.db')
    schedules = pd.read_sql_query("SELECT * FROM schedules", conn)
    conn.close()
    return schedules

# 일정 삭제
def delete_schedule(schedule_id):
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()

# 일정 수정
def update_schedule(schedule_id, title, description, date, time, priority):
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('''
    UPDATE schedules
    SET title = ?, description = ?, date = ?, time = ?, priority = ?
    WHERE id = ?
    ''', (title, description, date, time, priority, schedule_id))
    conn.commit()
    conn.close()

# 앱 초기화
def main():
    init_db()
    
    st.set_page_config(page_title="일정 관리 앱", page_icon="📅", layout="wide")
    
    st.title("📅 일정 관리 앱")
    
    # 사이드바에 일정 추가 폼 생성
    with st.sidebar:
        st.header("새 일정 추가")
        with st.form(key="schedule_form"):
            title = st.text_input("제목", max_chars=100)
            description = st.text_area("설명", max_chars=500)
            col1, col2 = st.columns(2)
            date = col1.date_input("날짜", datetime.date.today())
            time = col2.time_input("시간", datetime.time(9, 0))
            priority = st.selectbox("우선순위", ["높음", "중간", "낮음"])
            
            submit_button = st.form_submit_button(label="추가")
            
            if submit_button and title:
                date_str = date.strftime("%Y-%m-%d")
                time_str = time.strftime("%H:%M")
                add_schedule(title, description, date_str, time_str, priority)
                st.success("일정이 추가되었습니다!")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["일정 목록", "캘린더 보기"])
    
    with tab1:
        st.header("일정 목록")
        schedules = get_all_schedules()
        
        if not schedules.empty:
            # 날짜별로 정렬
            try:
                schedules['date_time'] = schedules.apply(lambda x: parse(f"{x['date']} {x['time']}"), axis=1)
                schedules = schedules.sort_values('date_time')
            except Exception as e:
                st.error(f"날짜 정렬 중 오류 발생: {e}")
            
            for i, row in schedules.iterrows():
                col1, col2, col3 = st.columns([0.6, 0.3, 0.1])
                
                # 우선순위에 따른 배경색 설정
                priority_color = {
                    "높음": "#ffcccc",
                    "중간": "#ffffcc",
                    "낮음": "#ccffcc"
                }
                
                with col1:
                    with st.expander(f"{row['title']} ({row['date']} {row['time']})"):
                        st.markdown(f"**설명:** {row['description']}")
                        st.markdown(f"**우선순위:** {row['priority']}")
                        
                        # 일정 수정 폼
                        with st.form(key=f"edit_form_{row['id']}"):
                            edit_title = st.text_input("제목 수정", row['title'], key=f"title_{row['id']}")
                            edit_description = st.text_area("설명 수정", row['description'], key=f"desc_{row['id']}")
                            try:
                                edit_date = st.date_input("날짜 수정", parse(row['date']).date(), key=f"date_{row['id']}")
                                edit_time = st.time_input("시간 수정", parse(row['time']).time(), key=f"time_{row['id']}")
                            except:
                                st.error("날짜/시간 형식 오류. 기본값으로 설정합니다.")
                                edit_date = st.date_input("날짜 수정", datetime.date.today(), key=f"date_{row['id']}")
                                edit_time = st.time_input("시간 수정", datetime.time(9, 0), key=f"time_{row['id']}")
                                
                            edit_priority = st.selectbox("우선순위 수정", ["높음", "중간", "낮음"], 
                                                        index=["높음", "중간", "낮음"].index(row['priority']), 
                                                        key=f"priority_{row['id']}")
                            
                            col_update, col_delete = st.columns(2)
                            with col_update:
                                update_button = st.form_submit_button(label="수정")
                            with col_delete:
                                delete_button = st.form_submit_button(label="삭제", type="primary")
                            
                            if update_button:
                                date_str = edit_date.strftime("%Y-%m-%d")
                                time_str = edit_time.strftime("%H:%M")
                                update_schedule(row['id'], edit_title, edit_description, date_str, time_str, edit_priority)
                                st.success("일정이 수정되었습니다!")
                                st.experimental_rerun()
                            
                            if delete_button:
                                delete_schedule(row['id'])
                                st.success("일정이 삭제되었습니다!")
                                st.experimental_rerun()
                
                with col2:
                    st.markdown(f"**{row['date']}**  \n**{row['time']}**")
                
                with col3:
                    st.markdown(f"<div style='background-color:{priority_color[row['priority']]};padding:10px;border-radius:5px;text-align:center;'>{row['priority']}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.info("등록된 일정이 없습니다. 새 일정을 추가해 보세요!")
    
    with tab2:
        st.header("캘린더 보기")
        schedules = get_all_schedules()
        
        if not schedules.empty:
            # 날짜별로 일정 그룹화
            try:
                schedules['date'] = pd.to_datetime(schedules['date'])
                
                # Plotly 캘린더 뷰 (Plotly가 사용 가능한 경우)
                if plotly_available:
                    try:
                        fig = px.timeline(
                            schedules,
                            x_start='date',
                            y='title',
                            color='priority',
                            title='일정 타임라인'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"타임라인 생성 중 오류 발생: {e}")
                else:
                    st.warning("Plotly 라이브러리가 없어서 타임라인을 표시할 수 없습니다.")
                
                # 기본 캘린더 뷰
                today = datetime.date.today()
                calendar_month = st.date_input("월 선택", today, key="calendar_select")
                selected_month = calendar_month.month
                selected_year = calendar_month.year
                
                # 선택된 월의 일수 계산
                if selected_month == 12:
                    next_month = datetime.date(selected_year + 1, 1, 1)
                else:
                    next_month = datetime.date(selected_year, selected_month + 1, 1)
                
                last_day = (next_month - datetime.timedelta(days=1)).day
                
                # 캘린더 그리드 생성
                cols = st.columns(7)
                for i, day_name in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
                    cols[i].markdown(f"**{day_name}**", unsafe_allow_html=True)
                
                # 선택된 월의 첫 번째 날의 요일 계산
                first_day = datetime.date(selected_year, selected_month, 1)
                first_weekday = first_day.weekday()  # 0: 월요일, 6: 일요일
                
                # 캘린더 그리기
                day_counter = 1
                for week in range(6):  # 최대 6주 표시
                    cols = st.columns(7)
                    
                    for weekday in range(7):
                        if (week == 0 and weekday < first_weekday) or day_counter > last_day:
                            cols[weekday].markdown("&nbsp;", unsafe_allow_html=True)
                        else:
                            current_date = datetime.date(selected_year, selected_month, day_counter)
                            
                            # 해당 날짜의 일정 필터링
                            day_schedules = schedules[schedules['date'].dt.date == current_date]
                            
                            if not day_schedules.empty:
                                # 일정이 있는 날짜는 강조 표시
                                cols[weekday].markdown(f"**{day_counter}**", unsafe_allow_html=True)
                                
                                # 해당 날짜의 일정 표시
                                for _, row in day_schedules.iterrows():
                                    priority_color = {
                                        "높음": "#ffcccc",
                                        "중간": "#ffffcc",
                                        "낮음": "#ccffcc"
                                    }
                                    cols[weekday].markdown(
                                        f"<div style='background-color:{priority_color[row['priority']]};padding:5px;margin:2px;border-radius:3px;font-size:0.8em;'>{row['time']} {row['title']}</div>",
                                        unsafe_allow_html=True
                                    )
                            else:
                                cols[weekday].markdown(f"{day_counter}")
                            
                            day_counter += 1
                    
                    if day_counter > last_day:
                        break
            except Exception as e:
                st.error(f"캘린더 생성 중 오류 발생: {e}")
                st.dataframe(schedules[['title', 'date', 'time', 'priority']])
        else:
            st.info("등록된 일정이 없습니다. 새 일정을 추가해 보세요!")

if __name__ == "__main__":
    main() 