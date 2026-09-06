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

# Styling with updated light-blue & orange color palette and soft boxed containers
st.markdown(
    """
    <style>
    .stApp { background-color: #F0F4F8; }
    div.stButton > button { background-color: #FF8C00; color: white; border-radius: 8px; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #E07B00; color: white; }
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
  new_name = st.text_input("Lägg till ny läkare")
  if st.button("Lägg till"):
    if new_name and not any(
        p["name"].lower() == new_name.lower() for p in data["physicians"]
    ):
      data["physicians"].append({"name": new_name, "active": True})
      save_data(data)
      st.success(f"Lagt till {new_name}")
      st.rerun()

  st.write(
      "### Ändra ordning (Dra och släpp) & Ta bort:"
  )

  # Drag and drop component for sorting names
  current_names = [p["name"] for p in data["physicians"]]
  sorted_names = sort_items(current_names, key="physician_drag_drop")

  # If user rearranged elements via drag & drop, update database order
  if sorted_names and sorted_names != current_names:
    name_to_obj = {p["name"]: p for p in data["physicians"]}
    data["physicians"] = [name_to_obj[name] for name in sorted_names]
    save_data(data)
    st.rerun()

  # Delete section for physicians
  st.write("---")
  st.write("### Ta bort läkare från listan:")
  col_del1, col_del2 = st.columns([2, 1])
  with col_del1:
    selected_to_delete = st.selectbox(
        "Välj läkare att ta bort", [p["name"] for p in data["physicians"]]
    )
  with col_del2:
    st.write("")
    if st.button("Radera vald"):
      data["physicians"] = [
          p for p in data["physicians"] if p["name"] != selected_to_delete
      ]
      save_data(data)
      st.success(f"Tog bort {selected_to_delete}")
      st.rerun()

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
