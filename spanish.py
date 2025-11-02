import re
import time
import random
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="Español • Unidad 1", page_icon="🇪🇸")
st.title("Español • Unidad 1 — ¡Aprendamos!")

# ---------- STYLE ----------
st.markdown("""
<style>
.chat-bubble{
  border:1px solid #d9dfe5; padding:10px 12px; border-radius:12px; margin-bottom:8px;
}
.sender{ color:#334155; font-weight:600; margin-right:6px; }
.typing-cursor::after{ content:'▌'; animation: blink 1s steps(1) infinite; }
@keyframes blink{ 50%{ opacity:0; } }

/* paleta kolorów dla ćwiczeń */
.stage-1 { background:#eef6ff; }   /* niebieskawy */
.stage-2 { background:#f1f7ee; }   /* zielonkawy */
.stage-3 { background:#fff6ec; }   /* pomarańczowy pastel */
.stage-4 { background:#f5f0ff; }   /* fioletowy pastel */
.stage-5 { background:#fef2f2; }   /* różowy pastel */
.test    { background:#f4f6f8; }   /* neutralny dla testu */
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
if "mode" not in st.session_state: st.session_state.mode = "menu"   # menu | ex | test
if "stage" not in st.session_state: st.session_state.stage = 1      # 1..5
if "idx" not in st.session_state: st.session_state.idx = 0
if "mistakes" not in st.session_state: st.session_state.mistakes = []  # [(stage,i,user,correct)]
if "chat" not in st.session_state: st.session_state.chat = []          # [(role,text)]
if "pending_question" not in st.session_state: st.session_state.pending_question = False
if "typing_speed" not in st.session_state: st.session_state.typing_speed = 0.02
# ROTACJA IMION TUTORA
if "tutor_names" not in st.session_state:
    st.session_state.tutor_names = ["Mario", "Lucía", "Carlos", "Sofía", "Diego", "Ana"]
if "tutor_idx" not in st.session_state:
    st.session_state.tutor_idx = 0
if "tutor_name" not in st.session_state:
    st.session_state.tutor_name = st.session_state.tutor_names[0]

# =========================
# DANE ĆWICZEŃ
# =========================
task1 = [
  {"q":"Ayer yo ___ (comer).","ok":["comí","he comido"],"why":"Forma: pretérito (comí) lub perfecto (he comido)."},
  {"q":"Ellos ___ (ir) al cine el martes pasado.","ok":["fueron"],"why":"Ir – indefinido: fueron."},
  {"q":"¿Tú ya ___ (ver) la película?","ok":["has visto","viste"],"why":"Participio irregular: visto."},
  {"q":"Nosotros ___ (estar) en Madrid en 2019.","ok":["estuvimos"],"why":"Estar – indefinido: estuvimos."},
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
# Tu korzystamy z obu języków (PL↔ES)
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
# TEST – 15 + 10 MC (razem więcej)
# =========================
def build_test_items():
    items=[]
    # 1-5: uzupełnianie
    for i in [0,1,2,3,4]:
        items.append({"type":"gap", "prompt":task1[i]["q"], "answers":task1[i]["ok"]})
    # 6-9: tłumaczenia czasu (PL->ES)
    for i in [0,2,3,5]:
        items.append({"type":"translate", "prompt":f"Przetłumacz na hiszpański: „{task2[i]['pl']}”", "answers":task2[i]["es"]})
    # 10-12: MC (symptomy)
    items += [
      {"type":"mc", "prompt":"Wybierz poprawne: A mí me ___ la cabeza.",
       "options":["duelen","duele","dolor"], "correct":["duele"]},
      {"type":"mc", "prompt":"Wybierz poprawne: A ellos les ___ los pies.",
       "options":["duele","duelen","dolor"], "correct":["duelen"]},
      {"type":"mc", "prompt":"Wybierz poprawne: Tengo ___ de estómago.",
       "options":["duele","duelen","dolor"], "correct":["dolor"]},
    ]
    # +10 MC z różnych działów
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
    # 13-15 (na końcu listy) ES->PL części ciała
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
# WYŚWIETLANIE WIADOMOŚCI
# =========================
def add_msg(role: str, text: str):
    st.session_state.chat.append((role, text))

def render_history():
    css_class = stage_css()
    for role, text in st.session_state.chat:
        if role == "asystent":
            # ⬇️ Bez etykiety „Asystent:”, pokazujemy samą wiadomość
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
            # Użytkownik z emotką 👤
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

def qtext(item, ask_prompt: str):
    if "q" in item:
        return f"{qnum()}. {ask_prompt}: {item['q']}"
    elif "pl" in item:
        return f"{qnum()}. {ask_prompt}: „{item['pl']}”"
    else:
        return f"{qnum()}. {ask_prompt}: {item['es']}"

def rotate_tutor_name():
    st.session_state.tutor_idx = (st.session_state.tutor_idx + 1) % len(st.session_state.tutor_names)
    st.session_state.tutor_name = st.session_state.tutor_names[st.session_state.tutor_idx]

def stage_transition(next_stage: int, announce: str, rotate_name: bool = True):
    # pauza 2s PRZED przełączeniem na kolejne ćwiczenie
    time.sleep(2.0)
    if rotate_name:
        rotate_tutor_name()
    st.session_state.stage = next_stage
    st.session_state.idx = 0
    st.session_state.pending_question = False
    st.session_state.chat = []
    add_msg("asystent", announce)
    st.rerun()

# =========================
# MENU STARTOWE
# =========================
if st.session_state.mode == "menu":
    colA, colB = st.columns(2)
    with colA:
        if st.button("▶️ 5 ćwiczeń"):
            st.session_state.mode = "ex"
            st.session_state.stage = 1
            st.session_state.idx = 0
            st.session_state.chat = []
            asystent_once("Ćwiczenie 1: Uzupełnij lukę poprawnie odmienionym czasownikiem (Pretérito Perfecto / Indefinido). 10 zdań. Odpowiadasz tylko formą (np. comí / he comido).")
            st.rerun()
    with colB:
        if st.button("📝 Test sprawdzający (15+ pytań)"):
            st.session_state.mode = "test"
            st.session_state.chat = []
            add_msg("asystent","Test z działu 1. Odpowiadaj na pytania. Na końcu kliknij **Zakończ test**.")
            st.rerun()

# =========================
# TRYB ĆWICZEŃ (EX)
# =========================
def correct_quip():
    return random.choice(["¡Perfecto! ✅", "¡Muy bien! ✅", "¡Genial! ✅", "¡Muuy bien! ✅"])

def handle_stage(items, ask_prompt, answer_key, funny=False):
    # Koniec zestawu?
    if st.session_state.idx >= len(items):
        return "done"

    item = items[st.session_state.idx]

    # 1) PYTANIE od MARIA (jeśli jeszcze nie zadane)
    if not st.session_state.pending_question:
        mario_ask(qtext(item, ask_prompt))

    # 2) Odpowiedź użytkownika
    ans = st.chat_input("Twoja odpowiedź…", key=f"ans_{st.session_state.stage}_{st.session_state.idx}")
    if not ans:
        return "wait"

    add_msg("user", ans)

    # Off-topic → krótki feedback od ASYSTENTA, to samo pytanie ponownie
    if off_topic(ans):
        add_msg("asystent", "?? (trzymajmy się tematu lekcji) 😅")
        st.session_state.pending_question = False
        st.rerun()

    # 3) FEEDBACK – NATYCHMIAST (ASYSTENT)
    if answer_key == "ok":
        ok_list = item["ok"]
    elif answer_key == "es":
        ok_list = item["es"]
    else:
        ok_list = item["pl"]

    good = normalize(ans) in [normalize(x) for x in ok_list]

    if good:
        # zwięzłe, żartobliwe – ale od ASYSTENTA
        add_msg("asystent",
                random.choice(["Świetnie! ✅", "Elegancko! ✅", "Git! ✅"]) if not funny
                else random.choice(["Perfekcyjnie jak tortilla! ✅",
                                    "Tak jest, maestro! ✅",
                                    "Olé, trafione! ✅"]))
    else:
        hint = item.get("why")
        if hint:
            # Ćwiczenie 2 – bez emotek
            add_msg("asystent", short_explain(hint) if st.session_state.stage != 2 else hint)
        else:
            # Ćwiczenie 5: pokaż poprawną ODPOWIEDŹ PO HISZPAŃSKU (PL→ES), bez emotek
            if st.session_state.stage == 5 and answer_key == "es":
                add_msg("asystent", f"Nie tak. Poprawnie po hiszpańsku: {ok_list[0]}.")
            else:
                add_msg("asystent", f"Nie tak. Poprawnie: {ok_list[0]}.")
        st.session_state.mistakes.append((st.session_state.stage, st.session_state.idx, ans, ok_list[0]))

    # 4) PAUZA 2 s → OD RAZU KOLEJNE PYTANIE (znowu napisze MARIO)
    time.sleep(2.0)
    st.session_state.idx += 1
    st.session_state.pending_question = False
    st.rerun()



if st.session_state.mode == "ex":
    render_history()
    if st.session_state.stage == 1:
        status = handle_stage(task1, "Escribe la forma correcta", answer_key="ok", funny=True)
        if status=="done":
            wrong = [m for m in st.session_state.mistakes if m[0]==1]
            if wrong:
                lines = [f"- Zdanie {i+1}: Twoja odp.: {u} → poprawnie: {c}" for _,i,u,c in wrong]
                add_msg("asystent", "Podsumowanie błędów (Ćw.1):\n"+"\n".join(lines))
            else:
                add_msg("asystent","Bardzo dobrze! W ćw.1 brak błędów. 🚀")
            stage_transition(2,"Ćwiczenie 2: Tłumaczenie 10 wyrażeń czasu (PL → ES). Odpowiadasz jednym słowem/zwrotem.")

    elif st.session_state.stage == 2:
        status = handle_stage(task2, "Traduce al español", answer_key="es", funny=True)
        if status=="done":
            stage_transition(3,"Ćwiczenie 3: Zdania z „duele/duelen”, „tener dolor de”, objawy. 8 zdań – uzupełnij brakujące słowo lub formę.")

    elif st.session_state.stage == 3:
        status = handle_stage(task3, "Completa", answer_key="ok", funny=True)
        if status=="done":
            stage_transition(4,"Ćwiczenie 4: Tryb rozkazujący (vosotros, afirmativo). 8 form – podaj tylko formę (np. hablad).")

    elif st.session_state.stage == 4:
        status = handle_stage(task4, "Imperativo (vosotros)", answer_key="ok", funny=True)
        if status=="done":
            stage_transition(5,"Ćwiczenie 5: **Przetłumacz na hiszpański** (PL → ES). Jedno słowo — nazwy części ciała.")

    elif st.session_state.stage == 5:
        # UWAGA: PL -> ES
        status = handle_stage(task5, "Przetłumacz na hiszpański", answer_key="es", funny=True)
        if status=="done":
            add_msg("asystent","Świetna robota! Masz ochotę sprawdzić się w krótkim teście?")
            render_history()
            if st.button("➡️ Przejdź do testu"):
                st.session_state.mode="test"
                st.session_state.chat=[]
                add_msg("asystent","Test z działu 1. Odpowiadaj na pytania. Na końcu kliknij **Zakończ test**.")
                st.rerun()

# =========================
# TRYB TESTU
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
                           index=idx if isinstance(idx,int) else 0, format_func=lambda k:item["options"][k], key=f"mc_{i}")
            answers[i]=idx
        else:
            val = "" if answers[i] is None else answers[i]
            answers[i] = st.text_input("Odpowiedź:", value=val, key=f"in_{i}")
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
        if st.button("↩️ Wróć do 5 ćwiczeń"):
            st.session_state.mode="ex"
            st.session_state.stage=1
            st.session_state.idx=0
            st.session_state.chat=[]
            asystent_once("Ćwiczenie 1: Uzupełnij lukę poprawnie odmienionym czasownikiem (Pretérito Perfecto / Indefinido). 10 zdań. Odpowiadasz tylko formą.")
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

# render test
if st.session_state.mode=="test" and not st.session_state.test_done:
    # odświeżenie puli testu przy wejściu
    render_test()

# Wynik testu + przyciski
if st.session_state.mode=="test" and st.session_state.test_done:
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
        if st.button("↩️ Wróć do 5 ćwiczeń"):
            st.session_state.mode="ex"
            st.session_state.stage=1
            st.session_state.idx=0
            st.session_state.chat=[]
            st.session_state.mistakes=[]
            st.session_state.pending_question=False
            # reset imienia na start
            st.session_state.tutor_idx = 0
            st.session_state.tutor_name = st.session_state.tutor_names[0]
            asystent_once("Ćwiczenie 1: Uzupełnij lukę poprawnie odmienionym czasownikiem (Pretérito Perfecto / Indefinido). 10 zdań. Odpowiadasz tylko formą.")
            st.rerun()
