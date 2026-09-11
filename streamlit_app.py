import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from streamlit_sortables import sort_items

# --- FIREBASE INIT (CACHED) ---
@st.cache_resource
def init_firestore():
  if not firebase_admin._apps:
    fb_credentials = dict(st.secrets["firebase"])
    fb_credentials["private_key"] = fb_credentials["private_key"].replace(
        "\\n", "\n"
    )
    cred = credentials.Certificate(fb_credentials)
    firebase_admin.initialize_app(cred)
  return firestore.client()


db = init_firestore()
DOC_REF = db.collection("gilleberget").document("data")


def load_data_from_db():
  try:
    doc = DOC_REF.get()
    if doc.exists:
      return doc.to_dict()
  except Exception as e:
    st.error(f"Ett fel uppstod vid hämtning från databasen: {e}")

  default_data = {
      "physicians": [
          {"name": f"Person {chr(65+i)}", "active": True} for i in range(10)
      ],
      "history": {},
  }
  save_data(default_data)
  return default_data


def save_data(data):
  DOC_REF.set(data)
  st.session_state.data = data


# Ladda data till session_state vid första start
if "data" not in st.session_state:
  st.session_state.data = load_data_from_db()

data = st.session_state.data

st.set_page_config(
    page_title="Bevakning Gilleberget", page_icon="🩺", layout="centered"
)

st.markdown(
    """
    <style>
    :root {
        --primary-color: #FF4B4B;
    }
    
    .stApp { background-color: #F0F4F8; }
    
    ::selection {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    
    button[kind="primary"] {
        background-color: #FF4B4B !important;
        border-color: #FF4B4B !important;
    }
    button[kind="primary"]:hover {
        background-color: #E33B3B !important;
        border-color: #E33B3B !important;
    }
    
    div[data-testid="stCheckbox"] div[data-checked="true"] {
        background-color: #FF4B4B !important;
        border-color: #FF4B4B !important;
    }
    div[data-testid="stCheckbox"] div[data-checked="true"] svg {
        fill: white !important;
    }
    
    div[data-testid="stAlert"][data-baseweb="notification"]:has(svg) {
        background-color: #FFF6EE !important;
        color: #1E3A5F !important;
        border: 1px solid #FF4B4B !important;
    }
    div[data-testid="stAlert"] svg {
        fill: #FF4B4B !important;
        color: #FF4B4B !important;
    }
    
    a { color: #FF4B4B !important; }
    
    div.stButton > button:not([kind="header"]) { 
        background-color: #FF4B4B; 
        color: white; 
        border-radius: 8px; 
        border: none; 
        font-weight: bold; 
    }
    div.stButton > button:not([kind="header"]):hover { 
        background-color: #E33B3B; 
        color: white; 
    }
    
    div.stTextInput input, div.stSelectbox div[data-baseweb="select"] > div {
        border: 2px solid #FF4B4B !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    div.stTextInput input:focus, div.stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: #FF4B4B !important;
        box-shadow: 0 0 0 1px #FF4B4B !important;
    }
    
    .card-box {
        background-color: #E2ECF5;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #FF4B4B;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .card-box h4 {
        margin-top: 0;
        color: #1E3A5F;
    }
    
    .physician-card {
        background-color: #FFF6EE;
        border: none;
        padding: 0px 10px;
        height: 38px;
        border-radius: 6px;
        font-weight: 500;
        color: #1E3A5F;
        display: flex;
        align-items: center;
        width: 270px;
        box-sizing: border-box;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        font-size: 1.1em;
    }

    div[data-testid="column"] .stButton > button {
        background-color: #FFF6EE !important;
        color: #1E3A5F !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 1.1em !important;
        height: 38px !important;
        width: 100% !important;
        padding: 0px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 6px !important;
        box-sizing: border-box !important;
        background-image: none !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        background-color: #F7E5D4 !important;
        color: #FF4B4B !important;
    }

    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 4px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🩺 Bevakning Gilleberget")

tab1, tab2, tab3 = st.tabs(
    ["Veckans Schema", "Hantera Läkare", "Aktuell lista & Historik"]
)

with tab1:
  st.subheader("Vecko- och närvaroinställningar")

  col_w1, col_w2 = st.columns(2)
  with col_w1:
    week_input = st.text_input("Veckonummer", value="37", key="week_input_field")
  with col_w2:
    year_input = st.text_input("År", value="2026", key="year_input_field")

  week_num = f"Vecka {week_input.strip()}, {year_input.strip()}"

  st.markdown("### Bevakande läkare")
  working_status = {}
  for p in data["physicians"]:
    new_active = st.checkbox(
        p["name"], value=p.get("active", True), key=f"w_{p['name']}"
    )
    if new_active != p.get("active", True):
      p["active"] = new_active
      save_data(data)
    working_status[p["name"]] = new_active

  working_physicians = [
      name for name, active in working_status.items() if active
  ]
  absent_physicians = [
      name for name, active in working_status.items() if not active
  ]

  needs_monitoring = []
  if absent_physicians:
    st.markdown("### Läkare att bevaka")
    st.markdown(
        "<p style='color: #555555; font-size: 0.85em; margin-top: -10px;"
        " margin-bottom: 10px;'>(Bocka ur läkare som inte behöver"
        " bevakas)</p>",
        unsafe_allow_html=True,
    )
    for name in absent_physicians:
      if st.checkbox(name, value=True, key=f"proxy_{name}"):
        needs_monitoring.append(name)

  if st.button("Generera Schema", type="primary"):
    if not working_physicians:
      st.error("Minst en läkare måste arbeta.")
    else:
      n = len(working_physicians)
      base_size = 31 // n
      remainder = 31 % n

      history = data.get("history", {})
      recent_weeks = list(history.keys())[-4:]
      recent_weeks_rev = list(reversed(recent_weeks))

      def get_extra_day_history(doc_name):
        history_score = []
        for w_key in recent_weeks_rev:
          w_data = history[w_key]
          assignments = w_data.get("assignments", {})
          if doc_name in assignments:
            r = assignments[doc_name]
            end_day = r[1]
            days_assigned = end_day - r[0] + 1
            num_working = len(w_data.get("working", []))
            w_base = (31 // num_working) if num_working > 0 else 0

            score = 1.0 if days_assigned > w_base else 0.0
            if end_day >= 31:
              score -= 0.5
            elif end_day == 30:
              score -= 0.2

            history_score.append(score)
          else:
            history_score.append(0.0)
        while len(history_score) < 4:
          history_score.append(0.0)
        return tuple(history_score)

      sorted_candidates = sorted(
          working_physicians, key=lambda p: get_extra_day_history(p)
      )
      extra_receivers = set(sorted_candidates[:remainder])

      master_names = [p["name"] for p in data["physicians"]]

      def get_last_start_day(doc_name):
        for week_idx, w_key in enumerate(recent_weeks_rev):
          assignments = history[w_key].get("assignments", {})
          if doc_name in assignments:
            return (week_idx, assignments[doc_name][0])
        m_idx = (
            master_names.index(doc_name) if doc_name in master_names else 999
        )
        return (99, m_idx)

      ordered_working_physicians = sorted(
          working_physicians, key=get_last_start_day
      )

      sizes = [
          base_size + 1 if p in extra_receivers else base_size
          for p in ordered_working_physicians
      ]

      current_day = 1
      final_mapping = {}
      for p, size in zip(ordered_working_physicians, sizes):
        start = current_day
        end = current_day + size - 1
        final_mapping[p] = (start, end)
        current_day = end + 1

      if "history" not in data:
        data["history"] = {}

      data["history"][week_num] = {
          "working": working_physicians,
          "proxies": needs_monitoring,
          "assignments": {
              p: [r[0], r[1]] for p, r in final_mapping.items()
          },
      }
      save_data(data)

      st.success(f"Schema för {week_num} genererat!")

      st.markdown(f"### {week_num}")
      col_a, col_b = st.columns(2)

      with col_a:
        content_a = "<h4>Signerande läkare</h4>"
        for p, r in final_mapping.items():
          content_a += f"<p style='margin: 2px 0;'>{p} - {r[0]}-{r[1]}</p>"
        st.markdown(
            f'<div class="card-box">{content_a}</div>', unsafe_allow_html=True
        )

      with col_b:
        content_b = "<h4>Läkare som ska bevakas</h4>"
        if needs_monitoring:
          for p in needs_monitoring:
            content_b += f"<p style='margin: 2px 0;'>{p}</p>"
        else:
          content_b += "<p style='margin: 2px 0;'>(Inga)</p>"
        st.markdown(
            f'<div class="card-box">{content_b}</div>', unsafe_allow_html=True
        )

with tab2:
  st.subheader("Masterlista över läkare")

  if "edit_name_dict" not in st.session_state:
    st.session_state.edit_name_dict = {}

  new_name = st.text_input("Lägg till ny läkare", key="add_doc_input")
  if st.button("Lägg till"):
    clean_name = new_name.strip()
    if clean_name:
      if any(p["name"].lower() == clean_name.lower() for p in data["physicians"]):
        st.error("Läkaren finns redan i listan.")
      else:
        data["physicians"].append({"name": clean_name, "active": True})
        save_data(data)
        st.success(f"Lagt till {clean_name}")
        st.rerun()

  st.write("---")
  st.write("### Nuvarande läkare (Dra och släpp för att ändra ordning):")

  current_names = [p["name"] for p in data["physicians"]]
  sort_key = f"sortable_physicians_{len(current_names)}"
  sorted_names = sort_items(current_names, key=sort_key)

  if sorted_names and sorted_names != current_names:
    name_to_obj = {p["name"]: p for p in data["physicians"]}
    data["physicians"] = [name_to_obj[name] for name in sorted_names]
    save_data(data)
    st.rerun()

  st.write("")

  @st.fragment
  def render_management_fragment():
    st.write("### Redigera")

    current_data = st.session_state.data
    physicians_list = current_data["physicians"]

    if physicians_list:
      for i, p in enumerate(list(physicians_list)):
        doc_name = p["name"]
        is_editing = st.session_state.edit_name_dict.get(doc_name, False)

        if is_editing:
          c_input, c_save = st.columns([3.8, 0.6])
          with c_input:
            updated_val = st.text_input(
                "Redigera namn",
                value=doc_name,
                key=f"edit_box_{i}",
                label_visibility="collapsed",
            )
          with c_save:
            if st.button("💾", key=f"save_btn_{i}", help="Spara ändring"):
              if updated_val.strip():
                current_data["physicians"][i]["name"] = updated_val.strip()
                save_data(current_data)
                st.session_state.edit_name_dict[doc_name] = False
                st.rerun()
        else:
          c_edit, c_del, c_name = st.columns([0.35, 0.35, 4])
          with c_edit:
            if st.button("✏️", key=f"edit_btn_{i}", help="Redigera namn"):
              st.session_state.edit_name_dict[doc_name] = True
              st.rerun()
          with c_del:
            if st.button("❌", key=f"del_btn_{i}", help="Ta bort läkare"):
              current_data["physicians"].pop(i)
              save_data(current_data)
              st.rerun()
          with c_name:
            st.markdown(
                f'<div class="physician-card"><span>{doc_name}</span></div>',
                unsafe_allow_html=True,
            )
    else:
      st.info("Inga läkare inlagda.")

  render_management_fragment()

with tab3:
  st.subheader("Aktuell lista & Historik")
  history = data.get("history", {})
  if history:
    selected_week = st.selectbox(
        "Välj vecka att titta på",
        sorted(history.keys(), reverse=True),
        key="history_week_select",
    )

    if st.button("🗑️ Ta bort vald vecka från historiken"):
      if selected_week in data["history"]:
        del data["history"][selected_week]
        save_data(data)
        st.success(f"Tog bort {selected_week}!")
        st.rerun()

    if selected_week in history:
      hw = history[selected_week]
      st.markdown(f"### {selected_week}")
      col_1, col_2 = st.columns(2)

      with col_1:
        content_1 = "<h4>Signerande läkare</h4>"
        for p, r in hw["assignments"].items():
          content_1 += f"<p style='margin: 2px 0;'>{p} - {r[0]}-{r[1]}</p>"
        st.markdown(
            f'<div class="card-box">{content_1}</div>', unsafe_allow_html=True
        )

      with col_2:
        content_2 = "<h4>Läkare som ska bevakas</h4>"
        if hw["proxies"]:
          for p in hw["proxies"]:
            content_2 += f"<p style='margin: 2px 0;'>{p}</p>"
        else:
          content_2 += "<p style='margin: 2px 0;'>(Inga)</p>"
        st.markdown(
            f'<div class="card-box">{content_2}</div>', unsafe_allow_html=True
        )
  else:
    st.info("Ingen historik sparad än.")
