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

# Styling and soft container boxes
st.markdown(
    """
    <style>
    .stApp { background-color: #EBF4F6; }
    div.stButton > button { background-color: #007ACC; color: white; border-radius: 8px; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #005f9e; color: white; }
    .card-box {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
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

  # Veckonummer input handling (stores as "Vecka XX" in history)
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
        "<p style='color: #666666; font-size: 0.85em; margin-top: -10px;"
        " margin-bottom: 10px;'>(Bocka ur läkare som inte behöver bevakas)</p>",
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

      # Spara till historik
      data["history"][week_num] = {
          "working": working_physicians,
          "proxies": needs_monitoring,
          "assignments": {
              p: [r[0], r[1]] for p, r in final_mapping.items()
          },
      }
      save_data(data)

      st.success(f"Schema för {week_num} genererat!")

      # Side by side visual layout for screenshot capability
      st.markdown(f"### {week_num}")
      col_a, col_b = st.columns(2)

      with col_a:
        st.markdown(
            '<div class="card-box"><h4>Signerande läkare</h4>',
            unsafe_allow_html=True,
        )
        for p, r in final_mapping.items():
          st.text(f"{p} - {r[0]}-{r[1]}")
        st.markdown("</div>", unsafe_allow_html=True)

      with col_b:
        st.markdown(
            '<div class="card-box"><h4>Läkare som ska bevakas</h4>',
            unsafe_allow_html=True,
        )
        if needs_monitoring:
          for p in needs_monitoring:
            st.text(p)
        else:
          st.text("(Inga)")
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
  st.subheader("Masterlista över läkare")
  new_name = st.text_input("Lägg till ny läkare")
  if st.button("Lägg till"):
    if new_name and not any(
        p["name"].lower() == new_name.lower() for p in data["physicians"]
    ):
      data["physicians"].append({"name": new_name, "active": True})
      save_data(data)
      st.success(f"Lagt till {new_name}")
      st.rerun()

  st.write("### Nuvarande läkare:")
  for i, p in enumerate(list(data["physicians"])):
    col1, col2 = st.columns([3, 1])
    col1.text(p["name"])
    if col2.button("Ta bort", key=f"del_{i}"):
      data["physicians"].pop(i)
      save_data(data)
      st.rerun()

with tab3:
  st.subheader("Aktuell lista & Historik")
  history = data.get("history", {})
  if history:
    selected_week = st.selectbox(
        "Välj vecka att titta på", sorted(history.keys(), reverse=True)
    )
    if selected_week:
      hw = history[selected_week]

      st.markdown(f"### {selected_week}")
      col_1, col_2 = st.columns(2)

      with col_1:
        st.markdown(
            '<div class="card-box"><h4>Signerande läkare</h4>',
            unsafe_allow_html=True,
        )
        for p, r in hw["assignments"].items():
          st.text(f"{p} - {r[0]}-{r[1]}")
        st.markdown("</div>", unsafe_allow_html=True)

      with col_2:
        st.markdown(
            '<div class="card-box"><h4>Läkare som ska bevakas</h4>',
            unsafe_allow_html=True,
        )
        if hw["proxies"]:
          for p in hw["proxies"]:
            st.text(p)
        else:
          st.text("(Inga)")
        st.markdown("</div>", unsafe_allow_html=True)
  else:
    st.info("Ingen historik sparad än.")
