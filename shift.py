import streamlit as st
import pandas as pd
from datetime import date, timedelta
import requests
from dateutil.relativedelta import relativedelta

# ------------------- CONFIG -------------------
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_API_KEY = st.secrets["NOTION_API_KEY"]
NOTION_DATABASE_ID = st.secrets["NOTION_DATABASE_ID"]
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2025-09-03"
}

# ------------------- SETTINGS -------------------
shops = [
    "渋谷", "上野", "秋葉原", "新橋", "新宿西", "池袋", "新宿東", "学大",
    "飯田橋", "銀座", "八重洲", "立川", "恵比寿" , "武蔵小山","白楽","銀座イベントスペース",
    "八重洲イベントスペース", "立川イベントスペース"
]

staff_list = ["加藤", "加川", "藪下", "香坂", "細野", "土佐", "田中", "大高", "中森", "稲葉" , "村田", "徳山", "冨澤", "朝日","三浦" , "早坂", "蓜島", "向井原" , "関口" , "伊丹", "上大迫" , "西野" , "永田","松本","飯田","石井","塚原","前田"]

# ------------------- UI INPUT -------------------
st.title("アルバイト シフト申請フォーム")

staff_name = st.selectbox("スタッフ名を選んでください", staff_list)

# 申請月の選択肢：当月から3ヶ月分を正確に生成
today = date.today()
month_options = [(today.replace(day=1) + relativedelta(months=i)) for i in range(3)]
month_labels = [d.strftime("%Y-%m") for d in month_options]
selected_month = st.selectbox("申請する月を選んでください", month_labels)

start_date = date.fromisoformat(selected_month + "-01")
days = [(start_date + timedelta(days=i)) for i in range(31) if (start_date + timedelta(days=i)).month == start_date.month]

st.markdown("---")

shift_data = {}
for d in days:
    selected = st.multiselect(f"{d.strftime('%m/%d (%a)')} の勤務希望店舗", shops, key=str(d))
    shift_data[d.isoformat()] = selected

remarks = st.text_area("備考欄（任意）")

# ------------------- FUNCTION -------------------
def post_to_notion(date_str, staff, shop, memo):
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "タイトル": {"title": [{"text": {"content": staff}}]},
            "日付": {"date": {"start": date_str}},
            "スタッフ名": {"select": {"name": staff}},
            "店舗": {"select": {"name": shop}},
            "備考": {"rich_text": [{"text": {"content": memo}}]}
        }
    }
    response = requests.post(NOTION_API_URL, headers=HEADERS, json=data)


    if response.status_code in [200, 201]:
        return True

    # 失敗した場合は詳細をログに出す
    print("送信失敗:", response.status_code, response.text)
    return False

# ------------------- SUBMIT -------------------
if st.button("シフト申請を送信"):
    success = True
    for date_str, shop_list in shift_data.items():
        for shop in shop_list:
            ok = post_to_notion(date_str, staff_name, shop, remarks)
            if not ok:
                success = False
                st.error(f"{date_str} の {shop} への送信に失敗しました")
    if success:
        st.success("すべてのシフト申請が正常に送信されました！")
