import streamlit as st
import pandas as pd
from datetime import date, timedelta
import requests
from dateutil.relativedelta import relativedelta

# ------------------- CONFIG -------------------
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_API_KEY = st.secrets["NOTION_API_KEY"]
NOTION_DATABASE_ID = st.secrets["NOTION_DATABASE_ID"]

# Chatwork設定（st.secretsに追加してください）
CHATWORK_API_TOKEN = st.secrets["CHATWORK_API_TOKEN"]
CHATWORK_ROOM_ID = st.secrets["CHATWORK_ROOM_ID"]

HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ------------------- FUNCTIONS -------------------

# --- デバッグ版 FUNCTIONS ---

def post_to_notion(date_str, staff, shop, memo):
    try:
        data = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "タイトル": {"title": [{"text": {"content": f"{staff}"}}]},
                "日付": {"date": {"start": date_str}},
                "スタッフ名": {"select": {"name": staff}},
                "店舗": {"select": {"name": shop}},
                "備考": {"rich_text": [{"text": {"content": memo}}]}
            }
        }
        res = requests.post(NOTION_API_URL, headers=HEADERS_NOTION, json=data)
        
        # 成功以外は画面に詳細を出す
        if res.status_code not in [200, 201]:
            st.error(f"Notionエラー ({res.status_code}): {res.text}")
            return False
        return True
    except Exception as e:
        st.error(f"Notion通信エラー: {e}")
        return False

def post_to_chatwork(staff, selected_data, memo):
    try:
        url = f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages"
        headers = {
            "X-ChatWorkToken": CHATWORK_API_TOKEN,
            # 「フォーム形式で送ります」と明示的に宣言するのがコツです
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # 1. シフト内容を組み立て（空の日は除外）
        summary_lines = [f"・{d} : {', '.join(shops)}" for d, shops in selected_data.items() if shops]
        
        if not summary_lines:
            shift_summary = "（勤務希望日の選択なし）"
        else:
            shift_summary = "\n".join(summary_lines)
            
        # 2. メッセージ本文を作成（空文字にならないようガード）
        message_body = (
            f"[info][title]シフト申請（送信者: {staff}）[/title]"
            f"{shift_summary}\n\n"
            f"【備考】\n{memo if memo else 'なし'}[/info]"
        )
        
        # 3. データを辞書形式で渡す（requestsが自動でエンコードしてくれます）
        payload = {"body": message_body}
        res = requests.post(url, headers=headers, data=payload)
        
        if res.status_code in [200, 201]:
            return True
        else:
            st.error(f"Chatworkエラー ({res.status_code}): {res.text}")
            return False
            
    except Exception as e:
        st.error(f"Chatwork通信エラー: {e}")
        return False

# ------------------- SESSION STATE -------------------
# ページ遷移の状態を管理
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "last_submission" not in st.session_state:
    st.session_state.last_submission = None

# ------------------- UI -------------------

# 1. サンクスページ（送信完了後）
# --- 戻るための関数を定義（コードの最初の方に書いてもOK） ---
def reset_for_new_entry():
    # 1. 状態フラグをリセット
    st.session_state.submitted = False
    st.session_state.last_submission = None
    # 2. フォームの入力値（マルチセレクトなど）の残骸をすべて削除
    for key in list(st.session_state.keys()):
        # 設定情報(st.secretsにないもの)だけを消す
        if key not in ["NOTION_API_KEY", "NOTION_DATABASE_ID", "CHATWORK_API_TOKEN", "CHATWORK_ROOM_ID"]:
            del st.session_state[key]

# --- UI: サンクスページ ---
if st.session_state.submitted:
    st.title("✅ 送信が完了しました！")
    st.success("シフト申請を受け付けました。")
    
    st.subheader("今回申請した内容")
    
    # データの表示
    if "last_submission" in st.session_state and st.session_state.last_submission:
        display_list = []
        for d, shops in st.session_state.last_submission.items():
            if shops:
                display_list.append({"日付": d, "店舗": ", ".join(shops)})
        
        if display_list:
            st.table(pd.DataFrame(display_list))
        else:
            st.warning("申請内容が表示できませんでした。")
    
    st.divider()

    # 【ここが解決策】on_click を使うことで、確実にリセット関数を実行させる
    st.button("別の申請を行う", on_click=reset_for_new_entry, type="primary", use_container_width=True)

# 2. 入力ページ
else:
    st.title("アルバイト シフト申請フォーム")
    
    staff_list = ["加藤", "加川", "藪下", "香坂", "細野", "土佐", "田中","大高","中森","稲葉","村田","徳山","冨澤","朝日","三浦","蓜島","早坂","関口","向井原","伊丹","上大迫","永田","西野","松本","飯田","石井","塚原","前田"] # 実際はフルリスト
    shops = ["渋谷", "上野", "秋葉原", "新橋", "新宿西", "池袋", "新宿東", "学大", "飯田橋", "銀座", "八重洲", "立川", "恵比寿" , "武蔵小山","白楽"]
    
    staff_name = st.selectbox("スタッフ名を選んでください", staff_list)

    today = date.today()
    month_options = [(today.replace(day=1) + relativedelta(months=i)) for i in range(3)]
    month_labels = [d.strftime("%Y-%m") for d in month_options]
    selected_month = st.selectbox("申請する月を選んでください", month_labels)

    start_date = date.fromisoformat(selected_month + "-01")
    days = [(start_date + timedelta(days=i)) for i in range(31) if (start_date + timedelta(days=i)).month == start_date.month]

    st.markdown("---")
    
    shift_data = {}
    for d in days:
        selected = st.multiselect(f"{d.strftime('%m/%d (%a)')}", shops, key=str(d))
        shift_data[d.isoformat()] = selected

    remarks = st.text_area("備考欄（任意）")

# --- 送信ボタン周辺の正しい書き方 ---
    if st.button("シフト申請を送信", type="primary"):
        # ボタンが押されたときだけ、この中身が実行される
        if "CHATWORK_API_TOKEN" not in st.secrets:
            st.error("設定ファイル(secrets.toml)が読み込めていません。")
        else:
            with st.spinner("送信中..."):
                try:
                    # --- Notion送信ループ ---
                    for date_str, shop_list in shift_data.items():
                        for shop in shop_list:
                            ok = post_to_notion(date_str, staff_name, shop, remarks)
                            if not ok:
                                raise Exception(f"Notionへの送信に失敗しました ({date_str} {shop})")
                    
                    # --- Chatwork送信 ---
                    cw_ok = post_to_chatwork(staff_name, shift_data, remarks)
                    if not cw_ok:
                        raise Exception("Chatworkへのログ送信に失敗しました")

                    # すべて成功したら、ここでフラグを立てて再描画
                    st.session_state.last_submission = dict(shift_data)
                    st.session_state.submitted = True
                    st.rerun()

                except Exception as e:
                    st.error(f"🚨 送信エラーが発生しました: {e}")
