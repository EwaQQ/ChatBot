import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Bot dentystyczny", page_icon="💬")
st.title("Bot dentystyczny")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False

if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0

if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:

    st.subheader('Poznjamy się!', divider='blue')

    if "imie" not in st.session_state:
        st.session_state["imie"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["imie"] = st.text_input(label = "Imię", max_chars = 40, placeholder = "Wpisz Twoje imię...")

    st.session_state["experience"] = st.text_area(label = "Objawy", value = "", height = None, max_chars = 200, placeholder = "Opisz twoje objawy...")

    st.session_state["skills"] = st.text_area(label = "Dodatkowe informacje", value = "", height = None, max_chars = 200, placeholder = "Przyjmowane leki/ dodatkowe informacje...")

    st.subheader('Wybierz', divider='blue')

    if "oczekiwania" not in st.session_state:
        st.session_state["oczekwiania"] = "porada"
    if "position" not in st.session_state:
        st.session_state["position"] = "Dentystka Barbara"
    if "company" not in st.session_state:
        st.session_state["company"] = "0"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["oczekiwania"] = st.radio(
            "Czego oczekujesz?",
            key="visibility",
            options=["porada", "pocieszenie", "wstępna diagnoza"],
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Z kim chcesz rozmawiać?",
            ("Dentysta Kazimierz", "Dentystka Angelika", "Dentysta Bożydar", "Dentystka Barbara", "Dentystka Helena")
        )

    st.session_state["company"] = st.selectbox(
        "skala Twojego bólu",
        ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10")
    )

    #st.write(f"**Your information**: {st.session_state["oczekiwania"]} {st.session_state["position"]} at {st.session_state["company"]}")

    if st.button("Zacznij rozmowę", on_click=complete_setup):
        st.write("Zaczynamy...")

if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        """
        Możesz się przywitać! 

        *(pamiętaj, że jest to tylko ChatBot, może się mylić)

        - przeporowadź 5 interakcji aby dostać podsumowanie na koniec
        """,
        icon = "👋"
    )
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system", ""
            "content": (
                        f"You write back only in polish. You like saying your name and you do that often. You are a proffesional dentist {st.session_state['position']} talking to patient called {st.session_state['imie']} "
                        f"with symptomps {st.session_state['experience']} and extra information and taken medicamemts {st.session_state['skills']}. "
                        f"You should help him with {st.session_state['oczekiwania']} and do only that and focus on that. You are making jokes. But focus on being precise and professional. Your responses are short but you ask questions at the end. You can be argoant and have huge ego."
                        f"their scale of pain is {st.session_state['company']}")
        }]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Twoja odpowiedź. ", max_chars = 1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True
                    )

                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("kliknij tutaj -> podsumowanie", on_click=show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Już wszytsko wiem!")

    conversation_history = "\n".join([f"{msg['role']} : {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on how bad the problem is and what can be happening.
             You only respond in polish.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Skala problemu: //Your score
             Kiedy możesz odwiedzić nasz gabinet: //give random dates this month and hours
             Wstępna diagnoza i ocena problemu: //Here you put your feedback
             Give only the feedback do not ask any additional questions. Be precise. In the end tell them to contact the specialist.
              """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )
    
    st.write(feedback_completion.choices[0].message.content)

    if st.button("Jeszcze raz", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")