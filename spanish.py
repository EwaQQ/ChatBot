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

/* bąble czatu */
.chat-bubble{
  border:1px solid #d9dfe5; padding:10px 12px; border-radius:12px; margin-bottom:8px;
}
.sender{ color:#334155; font-weight:600; margin-right:6px; }
.typing-cursor::after{ content:'▌'; animation: blink 1s steps(1) infinite; }
@keyframes blink{ 50%{ opacity:0; } }

/* paleta kolorów dla ćwiczeń */
.stage-1 { background:#eef6ff; }
.stage-2 { background:#f1f7ee; }
.stage-3 { background:#fff6ec; }
.stage-4 { background:#f5f0ff; }
.stage-5 { background:#fef2f2; }
.test    { background:#f4f6f8; }
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
    st.session_state.tutor_names = ["Mario", "Lucía", "Carlos", "Sofía", "Diego", "Ana", "Marco"]
if "tutor_idx" not in st.session_state:
    st.session_state.tutor_idx = 0
if "tutor_name" not in st.session_state:
    st.session_state.tutor_name = st.session_state.tutor_names[0]

def rotate_tutor_name():
    st.session_state.tutor_idx = (st.session_state.tutor_idx + 1) % len(st.session_state.tutor_names)
    st.session_state.tutor_name = st.session_state.tutor_names[st.session_state.tutor_idx]

# ====== Imię tutora zależne od ćwiczenia ======
TUTOR_BY_STAGE = {1:"Marco", 2:"Lucía", 3:"Carlos", 4:"Sofía", 5:"Diego"}
def set_tutor_for_stage(stage: int):
    st.session_state.tutor_name = TUTOR_BY_STAGE.get(stage, st.session_state.tutor_names[0])

# ====== „Recenzent” – 3. chatbot (działa w tle) ======
def review_message(role: str, text: str) -> str:
    """
    Minimalny strażnik merytoryki:
    - doprecyzowuje nazwy czasów w ćw.1 (Simple vs Compuesto),
    - poprawia drobne literówki markerów (ultimamente -> últimamente),
    - wygładza sformułowania feedbacku.
    """
    if st.session_state.stage == 1 and role in ("asystent", "mario"):
        if "Perfecto" in text and "Compuesto" not in text and "Simple" not in text:
            text = text.replace("Perfecto", "Pretérito Perfecto Compuesto")
        if "Indefinido" in text and "Simple" not in text:
            text = text.replace("Indefinido", "Pretérito Perfecto Simple")
    text = text.replace("ultimamente", "últimamente")
    return text

# =========================
# BANK ZADAŃ (bazowe zbiory)
# =========================
SIMPLE_MARKERS    = ["ayer", "anteayer", "el martes pasado", "en 2019", "el año pasado"]
COMPUESTO_MARKERS = ["hoy", "esta semana", "este mes", "ya", "todavía no", "últimamente", "alguna vez"]

def gen_stage1_items():
    """
    Marco generuje 5 przykładów:
    - 3 przykłady Compuesto (haber + participio)
    - 2 przykłady Simple (formas de indefinido)
    ZAWSZE zapisujemy oczekiwany czas w polu 'tense' i powód w 'why'.
    """
    sujetos = [("yo","comer","he comido","comí"),
               ("tú","ver","has visto","viste"),
               ("nosotros","leer","hemos leído","leímos"),
               ("ellos","ir","han ido","fueron"),
               ("ella","hacer","ha hecho","hizo"),
               ("vosotros","poner","habéis puesto","pusisteis"),
               ("ellas","decir","han dicho","dijeron"),
               ("yo","escribir","he escrito","escribí"),
               ("nosotros","estar","hemos estado","estuvimos")]

    random.shuffle(sujetos)
    comp = random.sample(COMPUESTO_MARKERS, 3)
    simp = random.sample(SIMPLE_MARKERS, 2)

    def phr(marker, subj, verbo, comp_ok, simp_ok):
        if marker in COMPUESTO_MARKERS:
            # Compuesto
            q = f"{marker.capitalize()} {subj} ___ ({verbo})."
            ok = [comp_ok]
            tense = "PPC"  # Pretérito Perfecto Compuesto
            why = f"Marcador „{marker}” → rama czasowa związana z teraźniejszością/niezakończona → Pretérito Perfecto Compuesto."
        else:
            # Simple
            q = f"{subj.capitalize()} ___ ({verbo}) {marker}."
            ok = [simp_ok]
            tense = "PPS"  # Pretérito Perfecto Simple
            why = f"Marcador „{marker}” → przeszłość odcięta od teraz → Pretérito Perfecto Simple."
        return {"type":"gap","prompt":q,"answers":ok,"why":why,"tense":tense}

    items = []
    for m in comp:
        s = sujetos.pop()
        items.append(phr(m, *s))
    for m in simp:
        s = sujetos.pop()
        items.append(phr(m, *s))
    random.shuffle(items)
    return items[:5]

# --- Ćwiczenie 2: wyrażenia czasu (PL→ES) ---
task2 = [
  {"pl":"wczoraj","es":["ayer"]},
  {"pl":"przedwczoraj","es":["anteayer"]},
  {"pl":"już","es":["ya"]},
  {"pl":"jeszcze nie","es":["todavía nie","todavia no".replace("nie","no")]},  # poprawka polskiego "nie" -> "no"
  {"pl":"w 2005 roku","es":["en 2005"]},
  {"pl":"w zeszły wtorek","es":["el martes pasado"]},
  {"pl":"tydzień temu","es":["hace una semana"]},
  {"pl":"nigdy","es":["nunca"]},
  {"pl":"kiedykolwiek","es":["alguna vez"]},
  {"pl":"ostatnio","es":["últimamente","ultimamente"]},
]

# --- Ćwiczenie 3: duele/duelen, tener dolor de (PL→ES/gap) ---
task3 = [
  {"q":"A mí me ___ la cabeza.","ok":["duele"],"why":"Singular: duele + la cabeza."},
  {"q":"A ellos les ___ los pies.","ok":["duelen"],"why":"Plural: duelen + los pies."},
  {"q":"Tengo ___ de estómago.","ok":["dolor"],"why":"Tener dolor de + parte del cuerpo."},
  {"q":"Ella ___ tos desde ayer.","ok":["tiene"],"why":"Tener tos."},
  {"q":"Nosotros ___ fiebre.","ok":["tenemos"],"why":"Tener fiebre."},
  {"q":"Estoy ___ (zmęczony).","ok":["cansado","agotado"],"why":"Estar cansado/agotado."},
  {"q":"Mi hermano está ___ (chory).","ok":["enfermo","resfriado"],"why":"Estar enfermo/resfriado."},
  {"q":"A ti te ___ la espalda.","ok":["duele"],"why":"Singular: duele + la espalda."},
]

# --- Ćwiczenie 4: Imperativo (vosotros) ---
task4 = [
  {"q":"(vosotros) hablar → ___","ok":["hablad"],"why":"-ar → -ad"},
  {"q":"(vosotros) comer → ___","ok":["comed"],"why":"-er → -ed"},
  {"q":"(vosotros) abrir → ___","ok":["abrid"],"why":"-ir → -id"},
  {"q":"(vosotros, refl.) levantarse → ___","ok":["levantaos"],"why":"reflexivo afirm.: -aos/-eos/-ios"},
  {"q":"(vosotros, refl.) ponerse → ___","ok":["poneos"],"why":"poneos (nie 'poneros')."},
  {"q":"(vosotros, refl.) sentarse → ___","ok":["sentaos"],"why":"reflexivo -ar: -aos."},
  {"q":"(vosotros) irse → ___","ok":["idos","iros"],"why":"RAE: 'idos'; akceptowane 'iros'."},
  {"q":"(vosotros) hacer → ___","ok":["haced"],"why":"Imperativo regular: haced."},
]

# --- Ćwiczenie 5: części ciała (PL→ES) ---
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
# ĆWICZENIA – DEFINICJE (dokładnie 5 pozycji każde)
# =========================
def pick5(lst):
    return random.sample(lst, 5)

def build_exercises():
    return {
      1: {
        "title": "Ćwiczenie 1 — Pretérito Perfecto Simple vs Pretérito Perfecto Compuesto",
        "ask": "",
        "items": gen_stage1_items()
      },
      2: {
        "title": "Ćwiczenie 2 — Wyrażenia czasu (PL → ES)",
        "ask": "",
        "items": [{"type":"translate","prompt":f"„{x['pl']}”","answers":x["es"]} for x in pick5(task2)]
      },
      3: {
        "title": "Ćwiczenie 3 — duele/duelen, tener dolor de, objawy",
        "ask": "",
        "items": [{"type":"gap","prompt":x["q"],"answers":x["ok"],"why":x["why"]} for x in pick5(task3)]
      },
      4: {
        "title": "Ćwiczenie 4 — Imperativo (vosotros, afirmativo)",
        "ask": "",
        "items": [{"type":"gap","prompt":x["q"],"answers":x["ok"],"why":x["why"]} for x in pick5(task4)]
      },
      5: {
        "title": "Ćwiczenie 5 — Części ciała (PL → ES)",
        "ask": "",
        "items": [{"type":"translate","prompt":x["pl"][0], "answers":[x["es"]]} for x in pick5(task5)]
      }
    }

# dynamiczny stan ćwiczeń (po „Nowe przykłady”)
if "dynamic_exercises" not in st.session_state:
    st.session_state.dynamic_exercises = build_exercises()

def reset_stage_items(stage:int):
    base = build_exercises()
    st.session_state.dynamic_exercises[stage]["items"] = base[stage]["items"]

# =========================
# TEST – generator (losowy zestaw przy każdym uruchomieniu)
# =========================
def build_test_items():
    items=[]
    for it in gen_stage1_items():
        items.append({"type":"gap","prompt":it["prompt"],"answers":it["answers"]})
    for x in random.sample(task2, 4):
        items.append({"type":"translate", "prompt":f"Przetłumacz na hiszpański: „{x['pl']}”", "answers":x["es"]})
    items += [
      {"type":"mc", "prompt":"Wybierz poprawne: A mí me ___ la cabeza.",
       "options":["duelen","duele","dolor"], "correct":["duele"]},
      {"type":"mc", "prompt":"Wybierz poprawne: A ellos les ___ los pies.",
       "options":["duele","duelen","dolor"], "correct":["duelen"]},
      {"type":"mc", "prompt":"Wybierz poprawne: Tengo ___ de estómago.",
       "options":["duele","duelen","dolor"], "correct":["dolor"]},
    ]
    mc_more = [
      ("Marcador típico del Compuesto:", ["ayer","el año pasado","ya"], ["ya"]),
      ("Marcador típico del Simple:", ["esta semana","hoy","el martes pasado"], ["el martes pasado"]),
    ]
    for q, opts, corr in mc_more:
        items.append({"type":"mc","prompt":q,"options":opts,"correct":corr})
    for x in random.sample(task5, 3):
        items.append({"type":"translate", "prompt":f"Przetłumacz na polski: „{x['es']}”", "answers":x["pl"]})
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
# UI – WYŚWIETLANIE WIADOMOŚCI (z recenzentem)
# =========================
def add_msg(role: str, text: str):
    checked = review_message(role, text)
    st.session_state.chat.append((role, checked))

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
        to_show = review_message("mario", text)
        typed=""
        for ch in to_show:
            typed+=ch
            ph.markdown(
                f"<div class='chat-bubble {css_class}'><span class='sender'>{name}:</span> "
                f"<span class='typing-cursor'>{typed}</span></div>", unsafe_allow_html=True
            )
            time.sleep(st.session_state.typing_speed)
        ph.markdown(
            f"<div class='chat-bubble {css_class}'><span class='sender'>{name}:</span> {to_show}</div>",
            unsafe_allow_html=True
        )
    add_msg("mario", text)
    st.session_state.pending_question = True

def asystent_once(text: str):
    add_msg("asystent", text)

def stage_transition_back_to_menu():
    time.sleep(0.6)
    rotate_tutor_name()
    st.session_state.mode = "menu"
    st.session_state.idx = 0
    st.session_state.chat = []
    st.session_state.pending_question = False
    st.rerun()

# =========================
# TEORIA (rozszerzona i doprecyzowana)
# =========================
theory_text = {
  1: (
    "- ## Pretérito Perfecto Simple (PPS) vs Pretérito Perfecto Compuesto (PPC)\n"
    "### Kiedy PPS?\n"
    "- Zdarzenia zakończone w przeszłości, odcięte od chwili obecnej.\n"
    "- Typowe marcadores: ayer, anteayer, el martes pasado, en 2019, el año pasado, hace una semana.\n"
    "- Przykłady: Ayer fuimos al cine. / En 2019 estuvimos en Madrid.\n\n"
    "### Kiedy PPC? (wariant Hiszpanii)\n"
    "- Doświadczenia lub zdarzenia w ramach czasowych niezakończonych (hoy, esta semana, este mes, este año) lub z wiązaną teraźniejszością (ya, todavía no, últimamente, alguna vez).\n"
    "- Budowa: haber (he, has, ha, hemos, habéis, han) + participio (he comido, has visto, han dicho...).\n"
    "- Przykłady: Hoy he comido tarde. / ¿Ya has visto la película? / Últimamente hemos leído mucho.\n\n"
    "### Uwaga dialektalna\n"
    "- W Ameryce Łacińskiej częściej używa się form Simple tam, gdzie w Hiszpanii pojawia się Compuesto (hoy comí zamiast hoy he comido). W tej aplikacji trzymamy się wariantu Hiszpanii.\n\n"
    "### Participios irregulares (wybór)\n"
    "- abrir → abierto, decir → dicho, escribir → escrito, hacer → hecho, poner → puesto, ver → visto, volver → vuelto, romper → roto\n\n"
    "### Tłumaczenia (PL → wybór czasu)\n"
    "- „Dzisiaj jadłem późno” → PPC (Hoy he comido tarde).\n"
    "- „W zeszły wtorek byliśmy w kinie” → PPS (El martes pasado fuimos al cine).\n"
    "- „Już to widziałaś?” → PPC (¿Ya lo has visto?).\n"
    "- „W 2019 roku mieszkaliśmy w…” → PPS (En 2019 vivimos/estuvimos en…).\n"
    "- „Ostatnio dużo czytamy” → PPC (Últimamente hemos leído mucho).\n\n"
    "### Typowe błędy i wskazówki\n"
    "- Nie mieszaj PPS i PPC w jednym zdaniu, gdy marker jasno wskazuje ramę: Esta semana he estudiado (PPC), ale la semana pasada estudié (PPS).\n"
    "- Ya i todavía no prawie zawsze pchają do PPC w wariancie Hiszpanii.\n"
    "- Hace + periodo zwykle łączy się z PPS (Hace dos días vi a Ana).\n"
  ),
  2: (
    "- Marcadores czasu (PL→ES) i powiązania z czasami:\n"
    "  - wczoraj → ayer (PPS), przedwczoraj → anteayer (PPS), już → ya (PPC), jeszcze nie → todavía no (PPC),\n"
    "  - w zeszły wtorek → el martes pasado (PPS), ostatnio → últimamente (PPC)."
  ),
  3: "- doler: me duele (l.poj.) / me duelen (l.mn.). tener + symptom; tener dolor de + część ciała.",
  4: "- Imperativo vosotros: -ad / -ed / -id; zwrotne: -aos / -eos / -ios (np. poneos).",
  5: "- Partes del cuerpo: la cabeza, los ojos, la nariz, la boca, las manos, las piernas…"
}

# =========================
# MENU
# =========================
def show_menu():
    st.markdown(
        """
        <div class="hero">
          <h2>🌶️ <em>Español • Unidad 1</em>!</h2>
          <p>Wybierz ćwiczenie, przeczytaj teorię albo zrób test. ¡Vamos! 🇪🇸</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-title">🎯 Wybierz ćwiczenie</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown('<div class="card card-blue">🌀<h4>Ćw. 1</h4><p>Pretérito Perfecto Simple vs Compuesto — forma z kontekstu i markerów.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex1"):
            st.session_state.mode="ex"; st.session_state.stage=1; st.session_state.idx=0
            st.session_state.chat=[]; set_tutor_for_stage(1)
            st.session_state.dynamic_exercises[1]["items"] = gen_stage1_items()
            asystent_once(st.session_state.dynamic_exercises[1]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card card-green">⏱️<h4>Ćw. 2</h4><p>Wyrażenia czasu (PL → ES) — 5 szybkich tłumaczeń.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex2"):
            st.session_state.mode="ex"; st.session_state.stage=2; st.session_state.idx=0
            st.session_state.chat=[]; set_tutor_for_stage(2)
            reset_stage_items(2)
            asystent_once(st.session_state.dynamic_exercises[2]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="card card-orange">🩺<h4>Ćw. 3</h4><p>duele/duelen, tener dolor de — 5 uzupełnień.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex3"):
            st.session_state.mode="ex"; st.session_state.stage=3; st.session_state.idx=0
            st.session_state.chat=[]; set_tutor_for_stage(3)
            reset_stage_items(3)
            asystent_once(st.session_state.dynamic_exercises[3]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="card card-violet">🗣️<h4>Ćw. 4</h4><p>Imperativo (vosotros) — 5 form do wpisania.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex4"):
            st.session_state.mode="ex"; st.session_state.stage=4; st.session_state.idx=0
            st.session_state.chat=[]; set_tutor_for_stage(4)
            reset_stage_items(4)
            asystent_once(st.session_state.dynamic_exercises[4]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c5:
        st.markdown('<div class="card card-pink">🧠<h4>Ćw. 5</h4><p>Części ciała (PL → ES) — 5 słówek.</p>', unsafe_allow_html=True)
        if st.button("Start →", key="ex5"):
            st.session_state.mode="ex"; st.session_state.stage=5; st.session_state.idx=0
            st.session_state.chat=[]; set_tutor_for_stage(5)
            reset_stage_items(5)
            asystent_once(st.session_state.dynamic_exercises[5]["title"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">📚 Teoria</div>', unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.columns(5)
    for i, col in enumerate([t1,t2,t3,t4,t5], start=1):
        with col:
            st.markdown(f'<div class="card card-theory">📜<h4>Teoria {i}</h4><p>Najważniejsze zasady z działu {i}.</p>', unsafe_allow_html=True)
            if st.button("Czytaj →", key=f"th{i}"):
                st.session_state.mode="theory"; st.session_state.selected_theory=i; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">🧪 Test</div>', unsafe_allow_html=True)
    cta = st.container()
    with cta:
        st.markdown('<div class="card card-test">🚀<h4>Test sprawdzający</h4><p>Mieszanka: uzupełnianie, tłumaczenia, wielokrotny wybór.</p>', unsafe_allow_html=True)
        if st.button("Zacznij test →", key="test_start"):
            st.session_state.mode="test"
            st.session_state.chat=[]
            # usunięto ** z komunikatu asystenta
            add_msg("asystent","Test z działu 1. Kliknij Zakończ test na końcu.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# SILNIK ĆWICZEŃ (5 pozycji + przyciski końcowe)
# =========================
def render_exercise():
    render_history()

    ex = st.session_state.dynamic_exercises[st.session_state.stage]
    items = ex["items"]

    if st.session_state.idx >= len(items):
        add_msg("asystent", "Koniec ćwiczenia. Brawo! 🎯 Wybierz, co dalej.")
        render_history()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("↩️ Wróć do menu"):
                stage_transition_back_to_menu()
        with col2:
            if st.button("✨ Nowe przykłady"):
                if st.session_state.stage == 1:
                    st.session_state.tutor_name = "Marco"
                reset_stage_items(st.session_state.stage)
                st.session_state.idx = 0
                st.session_state.chat = []
                st.session_state.pending_question = False
                asystent_once(st.session_state.dynamic_exercises[st.session_state.stage]["title"])
                st.rerun()
        return

    item = items[st.session_state.idx]
    ask_prompt = ex["ask"]

    if not st.session_state.pending_question:
        if item["type"] in ("gap","translate"):
            q = f"{qnum()}. {item['prompt']}"
        else:
            q = f"{qnum()}. {item['prompt']}"
        mario_ask(q)

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

        if st.session_state.stage == 1:
            tense_full = "Pretérito Perfecto Compuesto" if item.get("tense")=="PPC" else "Pretérito Perfecto Simple"
            correct_form = item["answers"][0]
            reason = item.get("why","")
            if good:
                add_msg("asystent", f"Dobrze. Oczekiwany czas: {tense_full}. {reason} Poprawna forma to {correct_form} (i takiej użyłaś/eś).")
            else:
                add_msg("asystent", f"Oczekiwany czas: {tense_full}. {reason} Poprawna forma: {correct_form}.")
        else:
            if good:
                add_msg("asystent", random.choice(["Świetnie! ✅","Elegancko! ✅","Git! ✅"]))
            else:
                hint = item.get("why")
                if hint:
                    add_msg("asystent", short_explain(hint) if st.session_state.stage != 2 else hint)
                else:
                    if st.session_state.stage == 5:
                        add_msg("asystent", f"Nie tak. Poprawnie po hiszpańsku: {item['answers'][0]}.")
                    else:
                        add_msg("asystent", f"Nie tak. Poprawnie: {item['answers'][0]}.")
                st.session_state.mistakes.append((st.session_state.stage, st.session_state.idx, ans, item["answers"][0]))

        time.sleep(0.6)
        st.session_state.idx += 1
        st.session_state.pending_question = False
        st.rerun()

    else:  # MC
        key = f"mc_{st.session_state.stage}_{st.session_state.idx}"
        choice = st.radio("Wybierz:", item["options"], index=None, key=key)
        if choice is None:
            return
        add_msg("user", choice)
        good = choice in item["correct"]
        if good:
            add_msg("asystent", random.choice(["Dobrze! ✅","Tak jest! ✅","Super! ✅"]))
        else:
            add_msg("asystent", f"Nie tak. Poprawnie: {', '.join(item['correct'])}")
            st.session_state.mistakes.append((st.session_state.stage, st.session_state.idx, choice, item["correct"][0]))
        time.sleep(0.8)
        st.session_state.idx += 1
        st.session_state.pending_question = False
        st.session_state.pop(key, None)
        st.rerun()

# =========================
# TRYB TESTU (losowe przykłady za każdym razem)
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
        "- Pretérito Perfecto Simple: wydarzenia przeszłe, odcięte od teraz; markery: ayer, el martes pasado, en 2019.\n"
        "- Pretérito Perfecto Compuesto: doświadczenie/ramy niezakończone; markery: hoy, esta semana, ya, todavía no, últimamente.\n"
        "- doler: me duele / me duelen; tener + symptom; tener dolor de + część ciała.\n"
        "- Imperativo vosotros: -ad / -ed / -id; zwrotne: -aos/-eos/-ios (np. poneos).\n"
        "- Partes del cuerpo: la cabeza, los ojos, la nariz, la boca, las manos..."
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
            st.session_state.tutor_idx = 0
            st.session_state.tutor_name = st.session_state.tutor_names[0]
            st.rerun()

elif st.session_state.mode == "theory":
    render_theory()
