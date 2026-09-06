import json
import os
import streamlit as st
from streamlit_sortables import sort_items

DATA_FILE = "physician_data.json"


def load_data():
  if not os.path.exists(DATA_FILE):
    default_data = {
        "physicians": [
            {"name": f"Person {chr(65+i)}", "active": True} for i in range(10)
        ],
        "history": {},
    }
    save_data(default_data)
    return default_data
  try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return {"physicians": [], "history": {}}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)


st.set_page_config(
    page_title="Bevakning Gilleberget", page_icon="🩺", layout="centered"
)

st.markdown(
    """
    <style>
    .stApp { background-color: #F0F4F8; }
    div.stButton > button { background-color: #FF8C00; color: white; border-radius: 8px; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #E07B00; color: white; }
    div.stTextInput input, div.stSelectbox div[data-baseweb="select"] > div {
        border: 2px solid #FF8C00 !important;
        border-radius: 8px !important;
    }
    .card-box {
        background-color: #E2ECF5;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #FF8C00;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .card-box h4 {
        margin-top: 0;
        color: #1E3A5F;
    }
    /* Compact row wrapper so the box is only as wide as needed, with neat spacing */
    .physician-row {
        background-color: #FFF6EE;
        border: 1.5px solid #EED3B8;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 500;
        color: #1E3A5F;
        display: inline-flex;
        align-items: center;
        gap: 25px;
        margin-bottom: 8px;
        min-width: 280px;
    }
    .physician-actions {
        display: flex;
        gap: 12px;
        margin-left: auto;
    }
    .physician-actions a {
        text-decoration: none;
        font-size: 1.1em;
        color: #1E3A5F;
        transition: color 0.2s;
    }
    .physician-actions a:hover {
        color: #FF8C00;
    }
    </style>
""",
    unsafe_allow_html=True,
)

data = load_data()

st.title("🩺 Bevakning Gilleberget")

# Handle tab selection persistence via query params or session state
if "active_tab" not in st.session_state:
  st.session_state.active_tab = 0

query_params = st.query_params
action = query_params.get("action")
target_idx = query_params.get("idx")
url_tab = query_params.get("tab")

if url_tab is not None:
  try:
    st.session_state.active_tab = int(url_tab)
  except ValueError:
    pass

# Handle actions triggered via query params
if action and target_idx is not None:
  try:
    idx = int(target_idx)
    if 0 <= idx < len(data["physicians"]):
      doc_name = data["physicians"][idx]["name"]
      if action == "edit":
        if "edit_name_dict" not in st.session_state:
          st.session_state.edit_name_dict = {}
        st.session_state.edit_name_dict[doc_name] = True
        st.query_params.clear()
        st.query_params["tab"] = str(st.session_state.active_tab)
        st.rerun()
      elif action == "delete":
        data["physicians"].pop(idx)
        save_data(data)
        st.query_params.clear()
        st.query_params["tab"] = str(st.session_state.active_tab)
        st.rerun()
  except ValueError:
    pass

# Streamlit tabs implementation. Note: standard st.tabs doesn't accept a default index dynamically,
# but we can organize layout or keep track. Alternatively, radio buttons can lock the tab,
# but let's use st.tabs and update query params when tabs are interacted with.
tab1, tab2, tab3 = st.tabs(
    ["Veckans Schema", "Hantera Läkare", "Aktuell lista & Historik"]
)

with tab1:
  st.subheader("Vecko- och närvaroinställningar")

  week_input = st.text_input("Veckonummer", value="37", key="week_input_field")
  week_num = f"Vecka {week_input.strip()}"

  st.markdown("### Bevakande läkare")
  working_status = {}
  for p in data["physicians"]:
    working_status[p["name"]] = st.checkbox(
        p["name"], value=True, key=f"w_{p['name']}"
    )

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
      sizes = [
          base_size + 1 if i < remainder else base_size for i in range(n)
      ]

      current_day = 1
      final_mapping = {}
      for p, size in zip(working_physicians, sizes):
        start = current_day
        end = current_day + size - 1
        final_mapping[p] = (start, end)
        current_day = end + 1

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
        st.query_params["tab"] = "1"
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
    st.query_params["tab"] = "1"
    st.rerun()

  st.write("")
  st.write("### Hantera läkare (Redigera / Ta bort):")

  if data["physicians"]:
    for i, p in enumerate(list(data["physicians"])):
      doc_name = p["name"]
      is_editing = st.session_state.edit_name_dict.get(doc_name, False)

      if is_editing:
        c_edit_box, c_save_btn = st.columns([4, 1])
        with c_edit_box:
          updated_val = st.text_input(
              "Redigera",
              value=doc_name,
              key=f"edit_box_{i}",
              label_visibility="collapsed",
          )
        with c_save_btn:
          if st.button("💾", key=f"save_btn_{i}"):
            if updated_val.strip():
              data["physicians"][i]["name"] = updated_val.strip()
              save_data(data)
              st.session_state.edit_name_dict[doc_name] = False
              st.query_params["tab"] = "1"
              st.rerun()
      else:
        # Compact row box container with inline icons at the right
        row_html = f"""
        <div class="physician-row">
            <span>{doc_name}</span>
            <span class="physician-actions">
                <a href="?action=edit&idx={i}&tab=1" target="_self" title="Redigera">✏️</a>
                <a href="?action=delete&idx={i}&tab=1" target="_self" title="Ta bort">❌</a>
            </span>
        </div>
        """
        st.markdown(row_html, unsafe_allow_html=True)
  else:
    st.info("Inga läkare inlagda.")

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
        st.query_params["tab"] = "2"
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
