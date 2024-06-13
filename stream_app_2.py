import os
import streamlit as st
import requests
import xmltodict

hide_decoration_bar_style = '''<style>header {visibility: hidden;}</style>'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)
hide_streamlit_footer = """<style>#MainMenu {visibility: hidden;}
                        footer {visibility: hidden;}</style>"""
st.markdown(hide_streamlit_footer, unsafe_allow_html=True)


private_key = os.environ.get('yagptkey', '')
url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
data = {}
data["modelUri"] = "gpt://b1g60k1kva2jrejf255o/yandexgpt-lite/rc"
data["copleteionOptions"] = {"stream": False, "temprature": 0.3, "maxTokens": 1000}


def get_ya_gpt(input_text: str) -> str:
    data["messages"] = [
        {
            "role": "system",
            "text": """Ты — специалист, помогающий сотрудникам онлайн интернет магазина техники помочь с работой,
            твоя задача координировать их и проводить обзор по сервисам для сотрудников ...""",
        },
        {
            "role": "user",
            "text": input_text
        }
    ]
    try:
        response = requests.post(
            url, headers={"Authorization": "Bearer " + private_key}, json=data
        ).json()
        answer = response["result"]["alternatives"][0]["text"]
    except Exception as e:
        print(e)
        answer = "Ошибка при обработке запроса"
    return answer


def ya_gpt_interface() -> None:
    st.markdown('Ассистент поможет вам в ваших вопросах')
    st.write('\n')  # add spacing

    st.subheader('\nЗапрос AI помощь\n')
    with st.expander("", expanded=True):

        input_ = st.text_input('Ваш запрос', 'Помоги разобраться с тем как искать товары?')
        answer = []
        space, right_col = st.columns([5, 2])
        with right_col:
            if st.button('Отправить запрос'):
                with st.spinner():
                    answer = get_ya_gpt(input_)

    if answer:
        st.write('\n')  # add spacing
        st.subheader(f'\nРезультаты по вашему запросу:\n')
        with st.expander("Ответ", expanded=True):
            st.write(answer)


if __name__ == '__main__':
    # call main function
    ya_gpt_interface()
