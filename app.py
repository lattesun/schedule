# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import datetime
import os
from dateutil.parser import parse

# Import Plotly conditionally
try:
    import plotly.express as px
    plotly_available = True
except ImportError:
    plotly_available = False
    st.error("Plotly library is not installed. Install it with 'pip install plotly'.")

# Initialize session state
if 'schedules' not in st.session_state:
    st.session_state.schedules = pd.DataFrame(columns=['id', 'title', 'description', 'date', 'time', 'priority'])
    st.session_state.next_id = 1

# Add schedule
def add_schedule(title, description, date, time, priority):
    new_schedule = pd.DataFrame([{
        'id': st.session_state.next_id,
        'title': title,
        'description': description,
        'date': date,
        'time': time,
        'priority': priority
    }])
    
    st.session_state.schedules = pd.concat([st.session_state.schedules, new_schedule], ignore_index=True)
    st.session_state.next_id += 1

# Get all schedules
def get_all_schedules():
    return st.session_state.schedules

# Delete schedule
def delete_schedule(schedule_id):
    st.session_state.schedules = st.session_state.schedules[st.session_state.schedules['id'] != schedule_id]

# Update schedule
def update_schedule(schedule_id, title, description, date, time, priority):
    idx = st.session_state.schedules.index[st.session_state.schedules['id'] == schedule_id].tolist()
    if idx:
        st.session_state.schedules.loc[idx[0], 'title'] = title
        st.session_state.schedules.loc[idx[0], 'description'] = description
        st.session_state.schedules.loc[idx[0], 'date'] = date
        st.session_state.schedules.loc[idx[0], 'time'] = time
        st.session_state.schedules.loc[idx[0], 'priority'] = priority

# Initialize app
def main():
    st.set_page_config(page_title="Schedule Manager", page_icon="📅", layout="wide")
    
    st.title("📅 Schedule Manager")
    
    # Create schedule form in sidebar
    with st.sidebar:
        st.header("Add New Schedule")
        with st.form(key="schedule_form"):
            title = st.text_input("Title", max_chars=100)
            description = st.text_area("Description", max_chars=500)
            col1, col2 = st.columns(2)
            date = col1.date_input("Date", datetime.date.today())
            time = col2.time_input("Time", datetime.time(9, 0))
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            
            submit_button = st.form_submit_button(label="Add")
            
            if submit_button and title:
                date_str = date.strftime("%Y-%m-%d")
                time_str = time.strftime("%H:%M")
                add_schedule(title, description, date_str, time_str, priority)
                st.success("Schedule added successfully!")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Schedule List", "Calendar View"])
    
    with tab1:
        st.header("Schedule List")
        schedules = get_all_schedules()
        
        if not schedules.empty:
            # Sort by date
            try:
                schedules['date_time'] = schedules.apply(lambda x: parse(f"{x['date']} {x['time']}"), axis=1)
                schedules = schedules.sort_values('date_time')
            except Exception as e:
                st.error(f"Error sorting dates: {e}")
            
            for i, row in schedules.iterrows():
                col1, col2, col3 = st.columns([0.6, 0.3, 0.1])
                
                # Set background color based on priority
                priority_color = {
                    "High": "#ffcccc",
                    "Medium": "#ffffcc",
                    "Low": "#ccffcc"
                }
                
                with col1:
                    with st.expander(f"{row['title']} ({row['date']} {row['time']})"):
                        st.markdown(f"**Description:** {row['description']}")
                        st.markdown(f"**Priority:** {row['priority']}")
                        
                        # Edit form
                        with st.form(key=f"edit_form_{row['id']}"):
                            edit_title = st.text_input("Edit Title", row['title'], key=f"title_{row['id']}")
                            edit_description = st.text_area("Edit Description", row['description'], key=f"desc_{row['id']}")
                            try:
                                edit_date = st.date_input("Edit Date", parse(row['date']).date(), key=f"date_{row['id']}")
                                edit_time = st.time_input("Edit Time", parse(row['time']).time(), key=f"time_{row['id']}")
                            except:
                                st.error("Date/time format error. Setting default values.")
                                edit_date = st.date_input("Edit Date", datetime.date.today(), key=f"date_{row['id']}")
                                edit_time = st.time_input("Edit Time", datetime.time(9, 0), key=f"time_{row['id']}")
                                
                            edit_priority = st.selectbox("Edit Priority", ["High", "Medium", "Low"], 
                                                        index=["High", "Medium", "Low"].index(row['priority']), 
                                                        key=f"priority_{row['id']}")
                            
                            col_update, col_delete = st.columns(2)
                            with col_update:
                                update_button = st.form_submit_button(label="Update")
                            with col_delete:
                                delete_button = st.form_submit_button(label="Delete", type="primary")
                            
                            if update_button:
                                date_str = edit_date.strftime("%Y-%m-%d")
                                time_str = edit_time.strftime("%H:%M")
                                update_schedule(row['id'], edit_title, edit_description, date_str, time_str, edit_priority)
                                st.success("Schedule updated successfully!")
                                st.experimental_rerun()
                            
                            if delete_button:
                                delete_schedule(row['id'])
                                st.success("Schedule deleted successfully!")
                                st.experimental_rerun()
                
                with col2:
                    st.markdown(f"**{row['date']}**  \n**{row['time']}**")
                
                with col3:
                    st.markdown(f"<div style='background-color:{priority_color[row['priority']]};padding:10px;border-radius:5px;text-align:center;'>{row['priority']}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.info("No schedules found. Add a new schedule!")
    
    with tab2:
        st.header("Calendar View")
        schedules = get_all_schedules()
        
        if not schedules.empty:
            # Group schedules by date
            try:
                schedules['date'] = pd.to_datetime(schedules['date'])
                
                # Plotly timeline view (if Plotly is available)
                if plotly_available:
                    try:
                        fig = px.timeline(
                            schedules,
                            x_start='date',
                            y='title',
                            color='priority',
                            title='Schedule Timeline'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating timeline: {e}")
                else:
                    st.warning("Plotly library is not available. Timeline cannot be displayed.")
                
                # Basic calendar view
                today = datetime.date.today()
                calendar_month = st.date_input("Select Month", today, key="calendar_select")
                selected_month = calendar_month.month
                selected_year = calendar_month.year
                
                # Calculate days in selected month
                if selected_month == 12:
                    next_month = datetime.date(selected_year + 1, 1, 1)
                else:
                    next_month = datetime.date(selected_year, selected_month + 1, 1)
                
                last_day = (next_month - datetime.timedelta(days=1)).day
                
                # Create calendar grid
                cols = st.columns(7)
                for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                    cols[i].markdown(f"**{day_name}**", unsafe_allow_html=True)
                
                # Calculate first day of month
                first_day = datetime.date(selected_year, selected_month, 1)
                first_weekday = first_day.weekday()  # 0: Monday, 6: Sunday
                
                # Draw calendar
                day_counter = 1
                for week in range(6):  # Maximum 6 weeks
                    cols = st.columns(7)
                    
                    for weekday in range(7):
                        if (week == 0 and weekday < first_weekday) or day_counter > last_day:
                            cols[weekday].markdown("&nbsp;", unsafe_allow_html=True)
                        else:
                            current_date = datetime.date(selected_year, selected_month, day_counter)
                            
                            # Filter schedules for current date
                            day_schedules = schedules[schedules['date'].dt.date == current_date]
                            
                            if not day_schedules.empty:
                                # Highlight dates with schedules
                                cols[weekday].markdown(f"**{day_counter}**", unsafe_allow_html=True)
                                
                                # Display schedules for the date
                                for _, row in day_schedules.iterrows():
                                    priority_color = {
                                        "High": "#ffcccc",
                                        "Medium": "#ffffcc",
                                        "Low": "#ccffcc"
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
                st.error(f"Error creating calendar: {e}")
                st.dataframe(schedules[['title', 'date', 'time', 'priority']])
        else:
            st.info("No schedules found. Add a new schedule!")

if __name__ == "__main__":
    main() 
