import os
import streamlit as st
import requests
import xmltodict

hide_decoration_bar_style = '''<style>header {visibility: hidden;}</style>'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)
hide_streamlit_footer = """<style>#MainMenu {visibility: hidden;}
                        footer {visibility: hidden;}</style>"""
st.markdown(hide_streamlit_footer, unsafe_allow_html=True)


private_key = os.environ.get('searchapikey')
url = "https://yandex.ru/search/xml"

filters = [
    'dns.ru',
    'citilink.ru',
    'apple.com',
    'samsung.com',
    'sony.com',
    'techradar.com',
    'google.com',
    'microsoft.com',
    'amazon.com',
    'dns.ru',
    'citilink.ru',
    'apple.com',
    'samsung.com',

]
filter_query = " | ".join([f"site:{url}" for url in filters])


def get_search_results(input_text: str) -> list[str]:

    query_params = {
        "folderid": os.environ.get("folderid"),
        "apikey": private_key,
        "query": input_text + f"({filter_query})",
    }
    try:
        search_response = requests.get(url, params=query_params)
        search_response = xmltodict.parse(search_response.text)
        print(search_response)
        urls = [group['doc']['url'] for group in search_response['yandexsearch']['response']['results']['grouping']['group']]
    except Exception as e:
        print(e)  # logs.debug(e)...
        urls = []
    return urls


def ya_search_interface() -> None:
    st.markdown('Ищите проффесионально в Яндекс Поиске')
    st.write('\n')  # add spacing

    st.subheader('\nКакой товар ищите?\n')
    with st.expander("Поисковый запрос", expanded=True):

        input_ = st.text_input('Введите товар', '')
        answer = []
        space, right_col = st.columns([5, 2])
        with right_col:
            if st.button('Отправить запрос'):
                with st.spinner():
                    answer = get_search_results(input_)

    if answer:
        st.write('\n')  # add spacing
        st.subheader(f'\nРезультаты по запросу: {input_}\n')
        with st.expander("Результаты", expanded=True):
            for uri in answer:
                st.write(uri)


if __name__ == '__main__':
    # call main function
    ya_search_interface()
