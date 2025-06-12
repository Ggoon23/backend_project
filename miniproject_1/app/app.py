
import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime # 파일 이름에 타임스탬프를 추가하기 위해

# --- 1. 세션 상태 초기화 ---
# selectbox의 옵션 리스트를 세션 상태에 저장합니다.
if 'csv_files' not in st.session_state:
    st.session_state.csv_files = [] # 처음에는 비어 있는 리스트

# 저장될 CSV 파일들을 위한 디렉토리 설정
OUTPUT_DIR = "downloaded_data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- 2. 웹 데이터 가져오기 및 CSV 저장 함수 ---
def fetch_and_save_data(url):
    try:
        st.info(f"'{url}'에서 데이터를 가져오는 중...")
        # requests를 사용하여 웹 페이지 내용 가져오기 (pandas.read_html이 직접 URL을 처리하지만, 예외 처리 등을 위해)
        response = requests.get(url, timeout=10) # 10초 타임아웃 설정
        response.raise_for_status() # HTTP 오류가 발생하면 예외 발생

        # pandas.read_html을 사용하여 HTML 테이블 파싱
        # match 인자를 사용하여 특정 텍스트를 포함하는 테이블만 가져올 수 있습니다.
        # flavor='lxml'은 파싱 엔진을 지정합니다.
        tables = pd.read_html(response.text, flavor='lxml')

        if not tables:
            st.warning("제공된 URL에서 HTML 테이블을 찾을 수 없습니다.")
            return None

        # 여러 테이블 중 첫 번째 테이블을 선택하거나, 사용자에게 선택하도록 할 수 있습니다.
        # 여기서는 간단하게 첫 번째 테이블을 선택합니다.
        df = tables[0]

        # 파일 이름 생성 (타임스탬프 포함)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # URL에서 도메인 이름을 가져와 파일 이름에 포함 (선택 사항)
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        domain_name = parsed_url.netloc.replace('.', '_')
        file_name = f"{domain_name}_{timestamp}.csv"
        file_path = os.path.join(OUTPUT_DIR, file_name)

        # CSV로 저장 (인덱스 제외)
        df.to_csv(file_path, index=False, encoding='utf-8-sig') # 한글 깨짐 방지를 위해 'utf-8-sig' 권장

        st.success(f"데이터가 '{file_path}'에 성공적으로 저장되었습니다.")
        return file_name # 저장된 파일 이름 반환

    except requests.exceptions.RequestException as e:
        st.error(f"URL 요청 중 오류 발생: {e}")
        st.error("URL이 유효하고 접근 가능한지 확인하세요.")
        return None
    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        st.error("제공된 URL의 콘텐츠 형식이 예상과 다를 수 있습니다 (HTML 테이블이 아닐 수 있음).")
        return None

# --- 3. Streamlit UI 구성 ---
st.title("웹 데이터 가져오기 & CSV 저장")

st.markdown("""
'http://' 또는 'https://'로 시작하는 웹사이트 URL을 입력하면,
해당 페이지의 첫 번째 HTML 테이블 데이터를 가져와 CSV 파일로 저장합니다.
저장된 파일은 아래 선택 상자에 추가됩니다.
""")

# URL 입력창
url_input = st.text_input(
    "데이터를 가져올 웹사이트 URL을 입력하세요:",
    placeholder="예: https://ko.wikipedia.org/wiki/대한민국",
    key="url_text_input"
)

# 데이터 가져오기 및 저장 버튼
if st.button("데이터 가져오기 & 저장"):
    if url_input:
        with st.spinner("데이터를 처리 중입니다... 잠시만 기다려주세요."):
            saved_file = fetch_and_save_data(url_input)
            if saved_file:
                # 새로운 파일 이름을 세션 상태 리스트에 추가
                if saved_file not in st.session_state.csv_files:
                    st.session_state.csv_files.append(saved_file)
                    st.session_state.csv_files.sort() # 정렬 (선택 사항)
    else:
        st.warning("URL을 입력해주세요!")

st.markdown("---")

# --- 4. 저장된 CSV 파일 목록을 selectbox로 표시 ---
st.subheader("저장된 CSV 파일 선택")

if st.session_state.csv_files:
    selected_csv = st.selectbox(
        "저장된 CSV 파일 목록:",
        options=st.session_state.csv_files,
        key="csv_file_selector"
    )
    st.info(f"현재 선택된 파일: {selected_csv}")

    # 선택된 CSV 파일의 내용을 DataFrame으로 읽어와 표시 (선택 사항)
    if selected_csv:
        try:
            file_path_to_read = os.path.join(OUTPUT_DIR, selected_csv)
            preview_df = pd.read_csv(file_path_to_read, encoding='utf-8-sig')
            st.subheader(f"'{selected_csv}' 파일 미리보기:")
            st.dataframe(preview_df)
        except Exception as e:
            st.error(f"선택된 CSV 파일을 읽는 중 오류 발생: {e}")
            st.warning("CSV 파일이 유효한지 확인하세요.")
else:
    st.info("아직 저장된 CSV 파일이 없습니다. 위에서 URL을 입력하고 '데이터 가져오기 & 저장' 버튼을 눌러주세요.")
