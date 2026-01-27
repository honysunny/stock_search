import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="주식 검색기", layout="wide")
st.title("⚡ 슈퍼 주식 검색기")

# --- 파일 기반 기록 관리 함수 ---
HISTORY_FILE = 'search_history.csv'

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            df = pd.read_csv(HISTORY_FILE)
            return df['log'].tolist()
        except:
            return []
    return []

def save_history(history_list):
    df = pd.DataFrame({'log': history_list})
    df.to_csv(HISTORY_FILE, index=False)

# --- 초기화 ---
if 'search_history' not in st.session_state:
    st.session_state['search_history'] = load_history()

if 'search_keyword' not in st.session_state:
    st.session_state['search_keyword'] = ""

# -----------------------------------------------------------
# 데이터 가져오기 (파일 읽기 방식)
# -----------------------------------------------------------
# -----------------------------------------------------------
# 데이터 가져오기 (디버깅 모드: 파일 목록을 눈으로 확인)
# -----------------------------------------------------------
@st.cache_data(ttl=3600) 
def get_safe_data():
    try:
        # 1. 시도: 그냥 읽어본다
        df = pd.read_csv('krx_list.csv')
        if 'Code' in df.columns:
            df['Code'] = df['Code'].astype(str).str.zfill(6)
        return df

    except Exception as e:
        # 2. 실패 시: 현재 폴더 상황을 화면에 다 까발린다
        import os
        
        st.error(f"❌ 읽기 실패! 에러 메시지: {e}")
        
        # 현재 위치는 어디?
        cwd = os.getcwd()
        st.warning(f"📍 현재 서버 위치: {cwd}")
        
        # 내 주변에 있는 파일들은?
        files = os.listdir(cwd)
        st.info(f"📂 내 주변 파일 목록: {files}")
        
        return pd.DataFrame()

# 데이터를 불러옵니다
with st.spinner('데이터 파일 로딩 중...'):
    df = get_safe_data()

# 2. 데이터가 정상적으로 있으면 화면 그리기 시작
if not df.empty:
    # 숫자 변환 (문자로 된 숫자를 진짜 숫자로)
    target_cols = ['Close', 'Marcap', 'Stocks']
    for col in target_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    if 'Dept' not in df.columns:
        df['Dept'] = '기타'

    # 3. 사이드바 검색 옵션
    st.sidebar.header("🔍 검색 옵션")

    # --- [검색 기록 표시] ---
    if st.session_state['search_history']:
        st.sidebar.markdown("### 🕒 최근 검색")
        
        for i, record in enumerate(st.session_state['search_history'][:10]): 
            try:
                keyword = record.split('] ')[1] 
            except:
                keyword = record

            # 레이아웃 비율 (0.7 : 0.3)
            col_search, col_del = st.sidebar.columns([0.7, 0.3])
            
            with col_search:
                if st.button(keyword, key=f"hist_{i}", use_container_width=True):
                    st.session_state['search_keyword'] = keyword
                    st.rerun()
            
            with col_del:
                if st.button("🗑️", key=f"del_{i}", help="기록 삭제", use_container_width=True):
                    st.session_state['search_history'].pop(i) 
                    save_history(st.session_state['search_history'])
                    st.rerun()
        
        if st.sidebar.button("🗑️ 기록 전체 비우기", use_container_width=True):
            st.session_state['search_history'] = []
            save_history([]) 
            st.rerun()
        st.sidebar.markdown("---")

    # --- 입력창 ---
    st.sidebar.subheader("1. 종목명 검색")
    
    search_text = st.sidebar.text_input(
        "종목명 (예: samsung)", 
        key="search_keyword",
        placeholder="입력 후 Enter"
    )
    
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("2. 시장 & 소속부")
    market_list = ['전체'] + sorted(df['Market'].unique().tolist())
    market_option = st.sidebar.selectbox("시장", market_list)
    
    dept_list = ['전체'] + sorted(df['Dept'].fillna('기타').unique().tolist())
    dept_option = st.sidebar.selectbox("소속부", dept_list)
    st.sidebar.markdown("---")

    st.sidebar.subheader("3. 시가총액 (단위: 억 원)")
    c1, c2 = st.sidebar.columns(2)
    
    # 기본값 1000억
    min_cap_input = c1.number_input("최소 (억)", value=1000, step=100)
    max_cap_input = c2.number_input("최대 (억)", value=5000000, step=100)

    # 4. 필터링 로직
    if search_text or market_option != '전체' or dept_option != '전체' or min_cap_input != 1000:
        
        # --- 기록 저장 ---
        if search_text:
            timestamp = datetime.now().strftime("%H:%M")
            new_log = f"[{timestamp}] {search_text}"
            
            history = st.session_state['search_history']
            # 중복 제거
            history = [h for h in history if h.split('] ')[1] != search_text]
            # 추가
            history.insert(0, new_log)
            # 저장
            st.session_state['search_history'] = history
            save_history(history)

        result = df.copy()
        
        if search_text:
            result = result[result['Name'].str.contains(search_text, case=False)]
        if market_option != '전체':
            result = result[result['Market'] == market_option]
        if dept_option != '전체':
            result = result[result['Dept'] == dept_option]
            
        result = result[
            (result['Marcap'] / 100000000 >= min_cap_input) &
            (result['Marcap'] / 100000000 <= max_cap_input)
        ]
        
        result = result.sort_values(by='Marcap', ascending=False)
        
        # --- 링크 ---
        result['네이버_URL'] = "https://finance.naver.com/item/main.naver?code=" + result['Code']
        result['FnGuide_URL'] = "http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A" + result['Code']
        result['DART_URL'] = "https://finance.naver.com/item/dart.naver?code=" + result['Code']
        result['Report_URL'] = "https://finance.naver.com/research/company_list.naver?searchType=itemCode&itemCode=" + result['Code']
        
        result['Marcap_억'] = result['Marcap'] / 100000000
        
        st.success(f"검색 결과: {len(result)}개")
        
        final_cols = ['Code', 'Name', 'Market', 'Close', 'Marcap_억', '네이버_URL', 'FnGuide_URL', 'Report_URL']
        
        st.dataframe(
            result[final_cols],
            column_config={
                "Close": st.column_config.NumberColumn("현재가", format="%d원"),
                "Marcap_억": st.column_config.NumberColumn("시가총액", format="%d억"),
                "네이버_URL": st.column_config.LinkColumn("시세", display_text="네이버 🟢"),
                "FnGuide_URL": st.column_config.LinkColumn("재무", display_text="FnGuide 📘"),
                "Report_URL": st.column_config.LinkColumn("리포트", display_text="증권사 📄") 
            },
            hide_index=True,
            use_container_width=True
        )
        
        if len(result) == 0:
            st.warning("조건에 맞는 종목이 없습니다.")
            
        elif len(result) > 0:
            st.markdown("---")
            st.subheader("🚀 종목 입체 분석")
            st.caption("네이버/FnGuide에 없는, 다른 시각의 데이터 소스를 확인하세요.")
            
            target_stock = st.selectbox("분석할 종목을 선택하세요", result['Name'].tolist())
            
            if target_stock:
                s_code = result[result['Name'] == target_stock]['Code'].values[0]
                
                c1, c2, c3, c4 = st.columns(4)
                
                # 1. 트레이딩뷰
                tv_url = f"https://kr.tradingview.com/chart/?symbol=KRX:{s_code}"
                c1.link_button("📈 트레이딩뷰 차트", tv_url, use_container_width=True)
                
                # 2. 구글 트렌드
                gt_url = f"https://trends.google.co.kr/trends/explore?date=today%2012-m&geo=KR&q={target_stock}"
                c2.link_button("📊 구글 관심도 추이", gt_url, use_container_width=True)
                
                # 3. 삼프로TV
                sp_url = f"https://www.youtube.com/results?search_query=삼프로TV+{target_stock}"
                c3.link_button("📺 삼프로TV 해설", sp_url, use_container_width=True)
                
                # 4. 구글 뉴스
                gn_url = f"https://www.google.com/search?q={target_stock}+주가전망&tbm=nws"
                c4.link_button("📰 구글 뉴스 심층", gn_url, use_container_width=True)

else:
    st.warning("데이터를 불러오지 못했습니다. 'krx_list.csv' 파일이 깃허브에 있는지 확인해주세요!")

