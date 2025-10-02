"]

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
