import json
import os
import streamlit as st

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

# Styling with orange outline for text inputs, selectboxes, and soft boxed containers
st.markdown(
    """
    <style>
    .stApp { background-color: #F0F4F8; }
    div.stButton > button { background-color: #FF8C00; color: white; border-radius: 8px; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #E07B00; color: white; }
    /* Orange border outline for text inputs and selectboxes */
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
    </style>
""",
    unsafe_allow_html=True,
)

data = load_data()

st.title("🩺 Bevakning Gilleberget")

tab1, tab2, tab3 = st.tabs(
    ["Veckans Schema", "Hantera Läkare", "Aktuell lista & Historik"]
)

with tab1:
  st.subheader("Vecko- och närvaroinställningar")

  week_input = st.text_input("Veckonummer", value="37")
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

  # Initialize edit state in session state if missing
  if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

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
  st.write("### Nuvarande läkare (Ändra ordning med pilarna, redigera eller ta bort):")

  if data["physicians"]:
    for i, p in enumerate(list(data["physicians"])):
      col_name, col_up, col_down, col_edit, col_del = st.columns(
          [4, 0.8, 0.8, 0.8, 0.8]
      )

      # Check if this item is currently being edited
      if st.session_state.edit_index == i:
        with col_name:
          updated_name = st.text_input(
              "Redigera", value=p["name"], key=f"edit_input_{i}", label_visibility="collapsed"
          )
        with col_edit:
          if st.button("💾", key=f"save_{i}"):
            if updated_name.strip():
              data["physicians"][i]["name"] = updated_name.strip()
              save_data(data)
              st.session_state.edit_index = None
              st.rerun()
      else:
        with col_name:
          st.markdown(
              f"<p style='padding-top: 8px; font-weight: 500; color:"
              f" #1E3A5F;'>{p['name']}</p>",
              unsafe_allow_html=True,
          )
        with col_edit:
          if st.button("✏️", key=f"edit_{i}"):
            st.session_state.edit_index = i
            st.rerun()

      with col_up:
        if i > 0 and st.button("⬆️", key=f"up_{i}"):
          data["physicians"][i], data["physicians"][i - 1] = (
              data["physicians"][i - 1],
              data["physicians"][i],
          )
          save_data(data)
          st.rerun()

      with col_down:
        if i < len(data["physicians"]) - 1 and st.button("⬇️", key=f"down_{i}"):
          data["physicians"][i], data["physicians"][i + 1] = (
              data["physicians"][i + 1],
              data["physicians"][i],
          )
          save_data(data)
          st.rerun()

      with col_del:
        if st.button("🗑️", key=f"del_{i}"):
          data["physicians"].pop(i)
          save_data(data)
          st.rerun()
  else:
    st.info("Inga läkare inlagda.")

with tab3:
  st.subheader("Aktuell lista & Historik")
  history = data.get("history", {})
  if history:
    selected_week = st.selectbox(
        "Välj vecka att titta på", sorted(history.keys(), reverse=True)
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
