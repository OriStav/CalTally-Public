# from methods.g_cal import get_all_calendar_names
get_all_calendar_names = None  # Placeholder for the actual import or function definition
import streamlit as st

DEMO = True
WISH_COL_CONFIG = {#25, 15, 70, 20
                  "purchased": st.column_config.CheckboxColumn(label="🏁", width="small", help="Check if the item has been purchased"),
                  "priority": st.column_config.NumberColumn(label="🎖️", width="small", help="Priority of the item"),
                  "name": st.column_config.TextColumn(label="🧸", width=100, help="Name of the item"),
                  "price": st.column_config.NumberColumn(label="💲", width="small", help="Price of the item"),
                  "progress": st.column_config.ProgressColumn(label="🏃‍➡️", width="small", min_value=0, max_value=100, help="Progress of the item"),
                  "purchase_date": st.column_config.DateColumn(label="📅", width="small", format="DD/MM/YYYY", help="Date of the purchase"),
                  "link": st.column_config.LinkColumn(label="🔗", width="small", help="Link to the item"),
              }#💰🎁🍯⏱️🧮⚖️⏳🏆🏅🔗🏁💲🏃‍➡️🧸📅🎖️

COL_CONFIG = {"start": st.column_config.DatetimeColumn("📅 Start",format="HH:mm",width="small"),
              "end": st.column_config.DatetimeColumn("📅 End",format="HH:mm",width="small"),#DD/MM/YYYY 
              "summary": st.column_config.TextColumn("📝 Summary",width="medium"),
            #   "location": st.column_config.TextColumn("📍 Location",width="medium"),
              "calendar": st.column_config.TextColumn("📋 Calendar",width="small"),
            #   "duration": st.column_config.TextColumn("⏱️ Duration",width="small"),
              "hours": st.column_config.NumberColumn("⏰ Hours",format="%.2f",width="small"),
            #   "score_per_hour": st.column_config.NumberColumn("⭐ Score/Hour",format="%.1f",width="small"),
              "score": st.column_config.NumberColumn("🏆 Score",format="%.1f",width="small"),
              "reward": st.column_config.NumberColumn("💰 Reward",format="%.2f ₪",width="small")}
if DEMO:
  SCORE_DCT = {
      "Personal Growth": 2,
      "Productivity": 2,
      "Social": 2,
      "Fitness": 2,
      "Errands": 2,
      "Entertainment": -2,
      "Shopping": -2,
  }
else:
  SCORE_DCT = {
      "Datomotive": 2,
      "Finance": 2,
      "Neutral": 0,
      "+ Raise": 2,
      "- Spend": -3,
  }

CALENDARS_DCT = SCORE_DCT if DEMO else get_all_calendar_names()

UNITS_DCT = {
    "Reward": "$",#₪
    "Score": "pts.",
    "Time": "hrs.",
}

BY_DCT = {
    "Time": "hours",
    "Score": "score",
    "Reward": "reward"
}

AGG_DCT = {
    "Week": "D",
    "Month": "W",
    "6 Months": "MS",
    # "year": "ME"
    # "Custom": "D"
}

TICK_DICT = {
    "D": "%a - %d/%m",
    "W": "Week %U",
    "MS": "%b",
    "ME": "%b",
    "Y": "%b"
}