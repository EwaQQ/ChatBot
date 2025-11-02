import re
import time
import random
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="Español • Unidad 1", page_icon="🇪🇸", layout="wide")
st.title("Español • Unidad 1 — ¡Aprendamos!")

# ---------- STYLE ----------
st.markdown("""
<style>
/* ===== kolorowy baner ===== */
.hero {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  border: 1px solid #ffd9c5;
  border-radius: 18px;
  padding: 18px 22px;
  margin: 8px 0 18px 0;
  box-shadow: 0 6px 18px rgba(252,182,159,.35);
}
.hero h2 { margin: 0 0 6px 0; font-size: 1.45rem; }
.hero p  { margin: 0; color:#5b4b43; }

/* ===== ogólna karta ===== */
.card {
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(0,0,0,.06);
  box-shadow: 0 8px 18px rgba(0,0,0,.06);
  transition: transform .12s ease, box-shadow .12s ease;
  margin-bottom: 14px;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 22px rgba(0,0,0,.10);
}
.card h4 { margin: 0 0 6px 0; }
.card p  { margin: 0 0 10px 0; color: #475569; }

/* warianty kolorów dla kart ćwiczeń */
.card-blue   { background: #eff6ff; border-color:#cde3ff; }
.card-green  { background: #f0fdf4; border-color:#c9f0d0; }
.card-orange { background: #fff7ed; border-color:#ffe0c2; }
.card-violet { background: #f5f3ff; border-color:#e4dfff; }
.card-pink   { background: #fff1f2; border-color:#ffd5da; }

/* karty teorii i testu */
.card-theory { background:#f8fafc; border-color:#e2e8f0; }
.card-test   { background: linear-gradient(135deg, #e0f2fe 0%, #e9d5ff 100%); border-color:#dbeafe; }

/* ładniejsze przyciski w kartach */
.card .stButton > button {
  width: 100%;
  border-radius: 10px;
  padding: 8px 12px;
  border: 1px solid rgba(0,0,0,.07);
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.card-blue  .stButton > button { background:#dbeafe; }
.card-green .stButton > button { background:#dcfce7; }
.card-orange.stButton > button,
.card-orange .stButton > button { background:#ffedd5; }
.card-violet .stButton > button { background:#ede9fe; }
.card-pink   .stButton > button { background:#ffe4e6; }
.card-theory .stButton > button { background:#e2e8f0; }
.card-test   .stButton > button { background:#e0e7ff; }

.section-title{
  margin: 8px 0 4px 0;
  font-size: 1.15rem;
}
</style>
""", unsafe_allow_html=True)


# =========================
# HELPERY
# =========================
def normalize(s: str) -> str:
    if s is None: return ""
    s = s.strip().lower()
    repl = (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ü","u"),("ñ","n"),
            ("ą","a"),("ć","c"),("ę","e"),("ł","l"),("ń","n"),("ó","o"),("ś","s"),("ź","z"),("ż","z"))
    for a,b in repl: s = s.replace(a,b)
    return re.sub(r"\s+"," ", s)

def off_topic(user_input: str) -> bool:
    s = normalize(user_input)
    unrelated = ["pogoda","polityka","piłka","film","pizza","pograj","komputer","git","python","praca"]
    return any(w in s for w in unrelated) or len(s.split())>4

def short_explain(hint: str) -> str:
    jokes = ["Nie do końca…","No nie tym razem…","Blisko jak Barcelona do morza.","Uff, prawie, prawie!"]
    return random.choice(jokes)+ " " + hint

def qnum() -> int: return st.session_state.idx + 1

def type_out(container, prefix: str, text: str, css_class: str, speed: float=0.02):
    typed=""
    for ch in text:
        typed+=ch
        container.markdown(
            f"<div class='chat-bubble {css_class}'><span class='sender'>{prefix}</span> "
            f"<span class='typing-cursor'>{typed}</span></div>", unsafe_allow_html=True
        )
        time.sleep(speed)
    container.markdown(
        f"<div class='chat-bubble {css_class}'><span class='sender'>{prefix}</span> {typed}</div>",
        unsafe_allow_html=True
    )

def stage_css():
    if st.session_state.mode=="test": return "test"
    return f"stage-{st.session_state.stage}"

# =========================
# STAN
# =========================
if "mode" not in st.session_state: st.session_state.mode = "menu"   # menu | ex | test | theory
if "stage" not in st.session_state: st.session_state.stage = 1
if "idx" not in st.session_state: st.session_state.idx = 0
if "mistakes" not in st.session_state: st.session_state.mistakes = []  # [(stage,i,user,correct)]
if "chat" not in st.session_state: st.session_state.chat = []          # [(role,text)]
if "pending_question" not in st.session_state: st.session_state.pending_question = False
if "typing_speed" not in st.session_state: st.session_state.typing_speed = 0.02
if "selected_theory" not in st.session_state: st.session_state.selected_theory = None

# ROTACJA IMION TUTORA
if "tutor_names" not in st.session_state:
    st.session_state.tutor_names = ["Mario", "Lucía", "Carlos", "Sofía", "Diego", "Ana"]
if "tutor_idx" not in st.session_state:
    st.session_state.tutor_idx = 0
if "tutor_name" not in st.session_state:
    st.session_state.tutor_name = st.session_state.tutor_names[0]

def rotate_tutor_name():
    st.session_state.tutor_idx = (st.session_state.tutor_idx + 1) % len(st.session_state.tutor_names)
    st.session_state.tutor_name = st.session_state.tutor_names[st.session_state.tutor_idx]

# ====== DODANE: imię tutora zależne od ćwiczenia ======
TUTOR_BY_STAGE = {
    1: "Mario",
    2: "Lucía",
    3: "Carlos",
    4: "Sofía",
    5: "Diego",
}
def set_tutor_for_stage(stage: int):
    st.session_state.tutor_name = TUTOR_BY_STAGE.get(stage, st.session_state.tutor_names[0])
# ======================================================

# =========================
# BANK ZADAŃ PODSTAWOWYCH
# =========================
task1 = [
  {"q":"Ayer yo ___ (comer).","ok":["comí","he comido"],"why":"Forma: pretérito (comí) lub perfecto (he comido)."},
  {"q":"Ellos ___ (ir) al cine el martes pasado.","ok":["fueron"],"why":"Ir – indefinido: fueron."},
  {"q":"¿Tú ya ___ (ver) la película?","ok":["has visto","viste"],"why":"Participio irregular: visto."},
  {"q":"Nosotros ___ (estar) en Madrid w 2019.","ok":["estuvimos"],"why":"Estar – indefinido: estuvimos."},
  {"q":"María ___ (hacer) la tarea hace una hora.","ok":["hizo"],"why":"Hizo (hacer)."},
  {"q":"Yo nunca ___ (escribir) cartas.","ok":["he escrito","escribí"],"why":"Participio irregular: escrito."},
  {"q":"¿Vosotros ___ (poner) la mesa?","ok":["pusisteis","habéis puesto"],"why":"Poner: pusisteis / habéis puesto."},
  {"q":"Ellas ___ (decir) la verdad.","ok":["dijeron","han dicho"],"why":"Decir: dijeron / han dicho."},
  {"q":"Yo ___ (tener) un problema en 2005.","ok":["tuve"],"why":"Tener: tuve."},
  {"q":"Últimamente nosotros ___ (leer) mucho.","ok":["hemos leído"],"why":"Perfecto z 'últimamente'."},
]
task2 = [
  {"pl":"wczoraj","es":["ayer"]},
  {"pl":"przedwczoraj","es":["anteayer"]},
  {"pl":"już","es":["ya"]},
  {"pl":"jeszcze nie","es":["todavia no","todavía no"]},
  {"pl":"w 2005 roku","es":["en 2005"]},
  {"pl":"w zeszły wtorek","es":["el martes pasado"]},
  {"pl":"tydzień temu","es":["hace una semana"]},
  {"pl":"nigdy","es":["nunca"]},
  {"pl":"kiedykolwiek","es":["alguna vez"]},
  {"pl":"ostatnio","es":["últimamente","ultimamente"]},
]
task3 = [  # 8 zdań
  {"q":"A mí me ___ la cabeza.","ok":["duele"],"why":"Singular: duele + la cabeza."},
  {"q":"A ellos les ___ los pies.","ok":["duelen"],"why":"Plural: duelen + los pies."},
  {"q":"Tengo ___ de estómago.","ok":["dolor"],"why":"Tener dolor de + parte del cuerpo."},
  {"q":"Ella ___ tos desde ayer.","ok":["tiene"],"why":"Tener tos."},
  {"q":"Nosotros ___ fiebre.","ok":["tenemos"],"why":"Tener fiebre."},
  {"q":"Estoy ___ (zmęczony).","ok":["cansado","agotado"],"why":"Estar cansado/agotado."},
  {"q":"Mi hermano está ___ (chory).","ok":["enfermo","resfriado"],"why":"Estar enfermo/resfriado."},
  {"q":"A ti te ___ la espalda.","ok":["duele"],"why":"Singular: duele + la espalda."},
]
task4 = [
  {"q":"(vosotros) hablar → ___","ok":["hablad"],"why":"-ar → -ad"},
  {"q":"(vosotros) comer → ___","ok":["comed"],"why":"-er → -ed"},
  {"q":"(vosotros) abrir → ___","ok":["abrid"],"why":"-ir → -id"},
  {"q":"(vosotros, refl.) levantarse → ___","ok":["levantaos"],"why":"afirmativo reflexivo: -aos/-eos/-ios"},
  {"q":"(vosotros, refl.) ponerse → ___","ok":["poneos"],"why":"poneos (no *poneros*)."},
  {"q":"(vosotros, refl.) sentarse → ___","ok":["sentaos"],"why":"reflexivo -ar: -aos."},
  {"q":"(vosotros) irse → ___","ok":["idos","iros"],"why":"RAE: idos; aceptado iros."},
  {"q":"(vosotros) hacer → ___","ok":["haced"],"why":"Imperativo regular: haced."},
]
task5 = [
  {"es":"la cabeza","pl":["głowa"]},
  {"es":"la oreja","pl":["ucho","uszy"]},
  {"es":"la cara","pl":["twarz","buźka"]},
  {"es":"el cuello","pl":["szyja","kark"]},
  {"es":"las manos","pl":["ręce","dłonie","ręka","dłoń"]},
  {"es":"las piernas","pl":["nogi","noga"]},
  {"es":"los tobillos","pl":["kostki","kostka"]},
  {"es":"los ojos","pl":["oczy","oko"]},
  {"es":"la nariz","pl":["nos"]},
  {"es":"la boca","pl":["usta","buzia"]},
  {"es":"los hombros","pl":["ramiona","barki","ramię"]},
  {"es":"los brazos","pl":["ręce","ramiona"]},
  {"es":"el vientre","pl":["brzuch","podbrzusze"]},
  {"es":"las rodillas","pl":["kolana","kolano"]},
  {"es":"los pies","pl":["stopy","stopa"]},
]

# =========================
# ĆWICZENIA – DEFINICJE (mix typów)
# =========================
# typy: "gap" -> wpisz; "translate" -> wpisz; "mc" -> wielokrotnego wyboru (radio 1 z 3)
exercises = {
  1: {
    "title": "Ćwiczenie 1 — Czas przeszły: Perfecto vs Indefinido",
    "ask": "Escribe la forma correcta",
    "items": (
      [{"type":"gap","prompt":x["q"],"answers":x["ok"],"why":x["why"]} for x in task1] + [
        {"type":"mc","prompt":"Marker czasu dla Perfecto to…",
         "options":["ayer","el martes pasado","ya"],"correct":["ya"]},
        {"type":"mc","prompt":"Wybierz formę Indefinido (3. os. lm.) dla 'ir'",
         "options":["iban","fueron","van"],"correct":["fueron"]},
      ])
  },
  2: {
    "title": "Ćwiczenie 2 — Wyrażenia czasu (PL → ES)",
    "ask": "Traduce al español",
    "items": (
      [{"type":"translate","prompt":f"„{x['pl']}”","answers":x["es"]} for x in task2] + [
        {"type":"mc","prompt":"„ostatnio” pasuje zwykle do…",
         "options":["Perfecto","Indefinido","Futuro"],"correct":["Perfecto"]},
        {"type":"mc","prompt":"„el martes pasado” to zwykle…",
         "options":["Perfecto","Indefinido","Presente"],"correct":["Indefinido"]},
      ])
  },
  3: {
    "title": "Ćwiczenie 3 — duele/duelen, tener dolor de, objawy",
    "ask": "Completa",
    "items": (
      [{"type":"gap","prompt":x["q"],"answers":x["ok"],"why":x["why"]} for x in task3] + [
        {"type":"mc","prompt":"A mí me ___ los ojos.",
         "options":["duele","duelen","dolor"],"correct":["duelen"]},
        {"type":"mc","prompt":"Tengo ___ de cabeza.",
         "options":["duelen","dolor","duele"],"correct":["dolor"]},
      ])
  },
  4: {
    "title": "Ćwiczenie 4 — Imperativo (vosotros, afirmativo)",
    "ask": "Imperativo (vosotros)",
    "items": (
      [{"type":"gap","prompt":x["q"],"answers":x["ok"],"why":x["why"]} for x in task4] + [
        {"type":"mc","prompt":"(vosotros, refl.) ponerse → ?",
         "options":["poneros","poneos","ponéos"],"correct":["poneos"]},
        {"type":"mc","prompt":"(vosotros) comer → ?",
         "options":["comed","comeis","comes"],"correct":["comed"]},
      ])
  },
  5: {
    "title": "Ćwiczenie 5 — Części ciała (PL → ES)",
    "ask": "Przetłumacz na hiszpański",
    "items": (
      [{"type":"translate","prompt":x["pl"][0], "answers":[x["es"]]} for x in task5] + [
        {"type":"mc","prompt":"„nogi” po hiszpańsku to…",
         "options":["los pies","las piernas","los brazos"],"correct":["las piernas"]},
        {"type":"mc","prompt":"„usta” po hiszpańsku to…",
         "options":["la boca","la cara","la nariz"],"correct":["la boca"]},
      ])
  }
}

# =========================
# TEST – generator (jak wcześniej)
# =========================
def build_test_items():
    items=[]
    for i in [0,1,2,3,4]:
        items.append({"type":"gap", "prompt":task1[i]["q"], "answers":task1[i]["ok"]})
    for i in [0,2,3,5]:
        items.append({"type":"translate", "prompt":f"Przetłumacz na hiszpański: „{task2[i]['pl']}”", "answers":task2[i]["es"]})
    items += [
      {"type":"mc", "prompt":"Wybierz poprawne: A mí me ___ la cabeza.",
       "options":["duelen","duele","dolor"], "correct":["duele"]},
      {"type":"mc", "prompt":"Wybierz poprawne: A ellos les ___ los pies.",
       "options":["duele","duelen","dolor"], "correct":["duelen"]},
      {"type":"mc", "prompt":"Wybierz poprawne: Tengo ___ de estómago.",
       "options":["duele","duelen","dolor"], "correct":["dolor"]},
    ]
    mc_more = [
      ("Marker czasu dla Perfecto to…", ["ayer","el martes pasado","ya"], ["ya"]),
      ("Wybierz formę Indefinido dla 'ir' (3 os. l.mn.)", ["van","fueron","iban"], ["fueron"]),
      ("Participio de 'ver' to…", ["visto","vido","visto/a"], ["visto"]),
      ("Vosotros (imperativo) de 'comer' to…", ["comed","comeis","comes"], ["comed"]),
      ("Doler (mnoga) z 'los ojos':", ["me duele los ojos","me duelen los ojos","tengo dolor los ojos"], ["me duelen los ojos"]),
      ("Tener + symptom: poprawne to…", ["tengo tos","estoy tos","soy tos"], ["tengo tos"]),
      ("'w 2005 roku' po hiszpańsku:", ["en 2005","a 2005","del 2005"], ["en 2005"]),
      ("'kiedykolwiek' po hiszpańsku:", ["alguna vez","nunca","jamás"], ["alguna vez"]),
      ("Vosotros (refl.) ponerse – imperativo:", ["poneros","poneos","ponéos"], ["poneos"]),
      ("Marker Indefinido:", ["últimamente","ya","el martes pasado"], ["el martes pasado"]),
    ]
    for q, opts, corr in mc_more:
        items.append({"type":"mc","prompt":q,"options":opts,"correct":corr})
    for i in [0,7,14]:
        items.append({"type":"translate", "prompt":f"Przetłumacz na polski: „{task5[i]['es']}”", "answers":task5[i]["pl"]})
    return items

if "test_items" not in st.session_state:
    st.session_state.test_items = build_test_items()
if "test_answers" not in st.session_state:
    st.session_state.test_answers = [None]*len(st.session_state.test_items)
if "test_done" not in st.session_state:
    st.session_state.test_done = False
if "test_score" not in st.session_state:
    st.session_state.test_score = 0

# =========================
# UI – WYŚWIETLANIE WIADOMOŚCI
# =========================
def add_msg(role: str, text: str):
    st.session_state.chat.append((role, text))

def render_history():
    css_class = stage_css()
    for role, text in st.session_state.chat:
        if role == "asystent":
            with st.chat_message("assistant", avatar="📝"):
                st.markdown(f"<div class='chat-bubble {css_class}'>{text}</div>", unsafe_allow_html=True)
        elif role == "mario":
            with st.chat_message("assistant", avatar="🇪🇸"):
                name = st.session_state.tutor_name
                st.markdown(
                    f"<div class='chat-bubble {css_class}'><span class='sender'>{name}:</span> {text}</div>",
                    unsafe_allow_html=True
                )
        elif role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(
                    f"<div class='chat-bubble {css_class}'><span class='sender'>Ty:</span> {text}</div>",
                    unsafe_allow_html=True
                )

def mario_ask(text: str):
    css_class = stage_css()
    with st.chat_message("assistant", avatar="🇪🇸"):
        ph = st.empty()
        name = st.session_state.tutor_name
        type_out(ph, f"{name}:", text, css_class, speed=st.session_state.typing_speed)
    add_msg("mario", text)
    st.session_state.pending_question = True

def asystent_once(text: str):
    add_msg("asystent", text)

def stage_transition_back_to_menu():
    time.sleep(2.0)
    rotate_tutor_name()
    st.session_state.mode = "menu"
    st.session_state.idx = 0
    st.session_state.chat = []
    st.session_state.pending_question = False
    st.rerun()

# =========================
# EKRAN STARTOWY (wybór ćwiczeń, test, teoria)
# =========================
theory_text = {
  1: "- **Indefinido**: zakończone fakty (ayer, el martes pasado, en 2019).\n- **Perfecto**: doświadczenie/ciągłość do dziś (ya, todavía no, últimamente) = **haber + participio**.",
  2: "- **Markery czasu**: *ayer, anteayer, ya, todavía no, el martes pasado, hace una semana, últimamente…*",
  3: "- **doler**: *me duele* (l.poj.) / *me duelen* (l.mn.).\n- **tener + symptom**: *tener tos / fiebre / gripe*; **tener dolor de** + część ciała.",
  4: "- **Imperativo vosotros**: -ad / -ed / -id; formy zwrotne: -aos / -eos / -ios (np. **poneos**).",
  5: "- **Partes del cuerpo**: *la cabeza, los ojos, la nariz, la boca, las manos, las piernas…*"
}

def show_menu():
    # ===== kolorowy baner =====
    st.markdown(
        """
        <div class="hero">
          <h2>🌶️ <em>Español • Unidad 1</em>!</h2>
          <p>Wybierz ćwiczenie, przeczytaj teorię albo zrób test.¡Vamos! 🇪🇸</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ===== Ćwiczenia =====
    st.markdown('<div class="section-title">🎯 Wybierz ćwiczenie</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown('<div class="card card-blue">🌀<h4>Ćw. 1</h4><p>Perfecto vs Indefinido — wpisz poprawną formę.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex1"):
            st.session_state.mode="ex"; st.session_state.stage=1; st.session_state.idx=0
            st.session_state.chat=[]
            set_tutor_for_stage(1)  # <<< DODANE
            asystent_once(exercises[1]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card card-green">⏱️<h4>Ćw. 2</h4><p>Wyrażenia czasu (PL → ES) — tłumaczenia + pytania MC.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex2"):
            st.session_state.mode="ex"; st.session_state.stage=2; st.session_state.idx=0
            st.session_state.chat=[]
            set_tutor_for_stage(2)  # <<< DODANE
            asystent_once(exercises[2]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="card card-orange">🩺<h4>Ćw. 3</h4><p><em>duele/duelen</em>, <em>tener dolor de</em>, objawy — uzupełnij i wybierz.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex3"):
            st.session_state.mode="ex"; st.session_state.stage=3; st.session_state.idx=0
            st.session_state.chat=[]
            set_tutor_for_stage(3)  # <<< DODANE
            asystent_once(exercises[3]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="card card-violet">🗣️<h4>Ćw. 4</h4><p>Imperativo (vosotros) — formy i zwrotne.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex4"):
            st.session_state.mode="ex"; st.session_state.stage=4; st.session_state.idx=0
            st.session_state.chat=[]
            set_tutor_for_stage(4)  # <<< DODANE
            asystent_once(exercises[4]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c5:
        st.markdown('<div class="card card-pink">🧠<h4>Ćw. 5</h4><p>Części ciała (PL → ES) — tłumaczenia + pytania MC.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex5"):
            st.session_state.mode="ex"; st.session_state.stage=5; st.session_state.idx=0
            st.session_state.chat=[]
            set_tutor_for_stage(5)  # <<< DODANE
            asystent_once(exercises[5]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ===== Teoria =====
    st.markdown('<div class="section-title">📚 Teoria</div>', unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.columns(5)
    theory_labels = ["Teoria 1", "Teoria 2", "Teoria 3", "Teoria 4", "Teoria 5"]
    theory_icons  = ["📜","📜","📜","📜","📜"]
    for i, col in enumerate([t1,t2,t3,t4,t5], start=1):
        with col:
            st.markdown(f'<div class="card card-theory">{theory_icons[i-1]}<h4>{theory_labels[i-1]}</h4><p>Najważniejsze zasady z działu {i}.</p>', unsafe_allow_html=True)
            if st.button("Czytaj →", key=f"th{i}"):
                st.session_state.mode="theory"; st.session_state.selected_theory=i; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ===== Test =====
    st.markdown('<div class="section-title">🧪 Test</div>', unsafe_allow_html=True)
    cta = st.container()
    with cta:
        st.markdown('<div class="card card-test">🚀<h4>Test sprawdzający</h4><p>Mieszanka 25+ pytań: uzupełnianie, tłumaczenia i wielokrotnego wyboru.</p>', unsafe_allow_html=True)
        if st.button("Zacznij test →", key="test_start"):
            st.session_state.mode="test"
            st.session_state.chat=[]
            add_msg("asystent","Test z działu 1. Kliknij **Zakończ test** na końcu.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# SILNIK ĆWICZEŃ (mix typów)
# =========================
def render_exercise():
    render_history()

    ex = exercises[st.session_state.stage]
    items = ex["items"]

    # koniec ćwiczenia
    if st.session_state.idx >= len(items):
        add_msg("asystent", "Koniec ćwiczenia. Brawo! Wróć do menu i wybierz kolejne zadanie lub test. 🎯")
        render_history()
        if st.button("↩️ Wróć do menu"):
            stage_transition_back_to_menu()
        return

    item = items[st.session_state.idx]
    ask_prompt = ex["ask"]

    # pytanie – tylko jeśli jeszcze nie zadane
    if not st.session_state.pending_question:
        if item["type"] in ("gap","translate"):
            # tekstowe
            q = f"{qnum()}. {ask_prompt}: {item['prompt']}"
        else:  # mc
            q = f"{qnum()}. {item['prompt']}"
        mario_ask(q)

    # odbiór odpowiedzi
    if item["type"] in ("gap","translate"):
        ans = st.chat_input("Twoja odpowiedź…", key=f"ans_{st.session_state.stage}_{st.session_state.idx}")
        if not ans:
            return
        add_msg("user", ans)

        if off_topic(ans):
            add_msg("asystent", "?? (trzymajmy się tematu lekcji) 😅")
            st.session_state.pending_question = False
            st.rerun()

        good = normalize(ans) in [normalize(x) for x in item["answers"]]
        if good:
            add_msg("asystent", random.choice(["Świetnie! ✅","Elegancko! ✅","Git! ✅"]))
        else:
            hint = item.get("why")
            if hint:
                # Ćw.2 bez emotek
                add_msg("asystent", short_explain(hint) if st.session_state.stage != 2 else hint)
            else:
                # Ćw.5: pokaż poprawne po HISZPAŃSKU
                if st.session_state.stage == 5:
                    add_msg("asystent", f"Nie tak. Poprawnie po hiszpańsku: {item['answers'][0]}.")
                else:
                    add_msg("asystent", f"Nie tak. Poprawnie: {item['answers'][0]}.")
            st.session_state.mistakes.append((st.session_state.stage, st.session_state.idx, ans, item["answers"][0]))

        time.sleep(1.0)
        st.session_state.idx += 1
        st.session_state.pending_question = False
        st.rerun()

    else:  # MC
        key = f"mc_{st.session_state.stage}_{st.session_state.idx}"
        choice = st.radio("Wybierz:", item["options"], index=None, key=key)
        if choice is None:  # jeszcze nic nie wybrano
            return
        add_msg("user", choice)
        good = choice in item["correct"]
        if good:
            add_msg("asystent", random.choice(["Dobrze! ✅","Tak jest! ✅","Super! ✅"]))
        else:
            # Ćw.2 bez emotek
            add_msg("asystent",
                    f"Nie tak. Poprawnie: {', '.join(item['correct'])}"
                    if st.session_state.stage == 2 else
                    f"Nie tak. Poprawnie: {', '.join(item['correct'])}")
            st.session_state.mistakes.append((st.session_state.stage, st.session_state.idx, choice, item["correct"][0]))
        time.sleep(2.0)
        st.session_state.idx += 1
        st.session_state.pending_question = False
        # wyczyść wybór, żeby nie przenosił się na następne pytanie
        st.session_state.pop(key, None)
        st.rerun()

# =========================
# TRYB TESTU (jak wcześniej)
# =========================
def render_test():
    st.session_state.mode = "test"
    render_history()
    st.divider()
    answers = st.session_state.test_answers
    items = st.session_state.test_items
    for i,item in enumerate(items):
        st.markdown(f"**{i+1}. {item['prompt']}**")
        if item["type"]=="mc":
            idx = answers[i]
            idx = st.radio("Wybierz:", list(range(len(item["options"]))),
                           index=idx if isinstance(idx,int) else 0, format_func=lambda k:item["options"][k], key=f"mc_t_{i}")
            answers[i]=idx
        else:
            val = "" if answers[i] is None else answers[i]
            answers[i] = st.text_input("Odpowiedź:", value=val, key=f"in_t_{i}")
        st.markdown("<br/>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Zakończ test"):
            score, report = evaluate_test()
            st.session_state.test_done=True
            st.session_state.test_score=score
            st.session_state.test_report=report
            st.rerun()
    with col2:
        if st.button("↩️ Wróć do menu"):
            st.session_state.mode="menu"
            st.session_state.chat=[]
            st.rerun()

def evaluate_test():
    items = st.session_state.test_items
    answers = st.session_state.test_answers
    total=len(items); good=0
    mistakes=[]
    for i,it in enumerate(items):
        ans = answers[i]
        if it["type"]=="mc":
            if isinstance(ans,int) and it["options"][ans] in it["correct"]:
                good+=1
            else:
                mistakes.append((i,it["prompt"], f"Poprawne: {', '.join(it['correct'])}"))
        else:
            if ans is not None and normalize(ans) in [normalize(x) for x in it["answers"]]:
                good+=1
            else:
                mistakes.append((i,it["prompt"], f"Poprawne: {', '.join(it['answers'])}"))
    pct = round(100*good/total)
    theory = (
        "- **Pretérito Indefinido**: zakończone wydarzenia w przeszłości, często z markerami *ayer, el martes pasado, en 2019*.\n"
        "- **Pretérito Perfecto**: doświadczenie/ciągłość do dziś, markery *ya, todavía no, últimamente* (+ *haber* + participio).\n"
        "- **doler**: *me duele* / *me duelen*.\n"
        "- **tener + symptom**: *tener tos / fiebre / gripe*; *tener dolor de* + część ciała.\n"
        "- **Imperativo vosotros**: -ad / -ed / -id; zwrotne: -aos / -eos / -ios (np. *poneos*).\n"
        "- Części ciała: *la cabeza, los ojos, la nariz, la boca, las manos...*"
    )
    lines=[f"**Wynik:** {pct}% ({good}/{total})", ""]
    if mistakes:
        lines.append("**Na co zwrócić uwagę:**")
        for _,p,exp in mistakes:
            lines.append(f"- {p} — {exp}")
    else:
        lines.append("Świetnie! Brak błędów.")
    lines.extend(["", "**Teoria (skrót):**", theory])
    return pct, "\n".join(lines)

# =========================
# TRYB TEORII
# =========================
def render_theory():
    i = st.session_state.selected_theory
    st.subheader(f"Teoria {i}")
    st.markdown(theory_text[i])
    if st.button("↩️ Wróć do menu"):
        st.session_state.mode="menu"; st.rerun()

# =========================
# ROUTER
# =========================
if st.session_state.mode == "menu":
    show_menu()

elif st.session_state.mode == "ex":
    render_exercise()

elif st.session_state.mode == "test" and not st.session_state.test_done:
    render_test()

elif st.session_state.mode == "test" and st.session_state.test_done:
    st.markdown(f"<div class='chat-bubble test'><span class='sender'>Wynik testu:</span> {st.session_state.test_score}%</div>", unsafe_allow_html=True)
    st.markdown(st.session_state.test_report)
    col1,col2=st.columns(2)
    with col1:
        if st.button("🔁 Powtórz test"):
            st.session_state.test_items = build_test_items()
            st.session_state.test_answers = [None]*len(st.session_state.test_items)
            st.session_state.test_done=False
            st.rerun()
    with col2:
        if st.button("↩️ Wróć do menu"):
            st.session_state.mode="menu"
            st.session_state.chat=[]
            st.session_state.mistakes=[]
            st.session_state.pending_question=False
            # reset imienia na start
            st.session_state.tutor_idx = 0
            st.session_state.tutor_name = st.session_state.tutor_names[0]
            st.rerun()

elif st.session_state.mode == "theory":
    render_theory()
