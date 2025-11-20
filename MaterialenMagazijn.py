import streamlit as st
import pandas as pd

# --- Session state setup ---
if 'rerun_trigger' not in st.session_state:
    st.session_state['rerun_trigger'] = False

st.set_page_config(page_title="Stone Inventory Tool", layout="wide")
st.title("📦 Steen Voorraad & Order Tool")

# --- Load Inventory ---
def load_inventory(path):
    return pd.read_excel(path)

try:
    inventory = load_inventory("inventory.xlsx")
except Exception:
    st.error("Kon 'inventory.xlsx' niet laden. Zorg dat het bestand bestaat.")
    st.stop()

# --- Dynamic Order Form ---
if 'selected_stone_type' in st.session_state and 'selected_size' in st.session_state and 'order_action' in st.session_state:
    st.subheader("Order / Voorraad Update")

    form_cols = st.columns(2)
    with form_cols[0]:
        project = st.text_input("Projectnaam")
    with form_cols[1]:
        user = st.text_input("Gebruiker")

    stone_type = st.session_state['selected_stone_type']
    size = st.session_state['selected_size']
    action = st.session_state['order_action']  # "order" or "add"

    st.markdown(f"**Geselecteerd product:** {stone_type} ({size})")

    available = int(inventory[(inventory["StoneType"] == stone_type) &
                              (inventory["Size"] == size)]["Quantity"].iloc[0])
    
    st.info(f"Beschikbaar: {available}")
    qty = st.number_input("Aantal", min_value=0, step=1)

    # Disable confirm button if project or user is empty
    if project.strip() == "" or user.strip() == "":
        st.warning("Vul aub Projectnaam en Gebruiker in om door te gaan.")
        disabled = True
    else:
        disabled = False

    if st.button("Bevestigen", disabled=disabled):
        if action == "order":
            if qty > available:
                st.error("Je kunt niet meer opvragen dan in voorraad is!")
            else:
                inventory.loc[
                    (inventory["StoneType"] == stone_type) & (inventory["Size"] == size),
                    "Quantity"
                ] -= qty
                inventory.to_excel("inventory.xlsx", index=False)
                st.success(f"Order geplaatst voor {qty} stuks {stone_type} ({size}) door {user} voor project {project}.")
        elif action == "add":
            inventory.loc[
                (inventory["StoneType"] == stone_type) & (inventory["Size"] == size),
                "Quantity"
            ] += qty
            inventory.to_excel("inventory.xlsx", index=False)
            st.success(f"{qty} stuks {stone_type} ({size}) toegevoegd aan de voorraad door {user}.")

        # Clear selection
        del st.session_state['selected_stone_type']
        del st.session_state['selected_size']
        del st.session_state['order_action']
        st.session_state['rerun_trigger'] = not st.session_state['rerun_trigger']


# --- Display Inventory ---
st.subheader("Beschikbare Voorraad")
unique_types = inventory["StoneType"].unique()
cols = st.columns(len(unique_types))

for idx, stone in enumerate(unique_types):
    with cols[idx]:
        subset = inventory[inventory["StoneType"] == stone]

        st.markdown(f"""
        <div style='padding: 20px; border-radius: 15px; background-color: #f5f5f5;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;'>
            <h3 style='margin-top: 0; text-align:center;'>{stone}</h3>
        </div>
        """, unsafe_allow_html=True)

        for _, row in subset.iterrows():
            row_cols = st.columns([4,1,1])
            with row_cols[0]:
                st.markdown(
                    f"<span style='font-size:24px;'><strong>{row['Size']}</strong><br>{row['Quantity']} stuks</span>", 
                    unsafe_allow_html=True
                )
            with row_cols[1]:
                st.write("")
                if st.button("🛒", key=f"{stone}_{row['Size']}_order"):
                    st.session_state['selected_stone_type'] = stone
                    st.session_state['selected_size'] = row['Size']
                    st.session_state['order_action'] = "order"
                    st.session_state['rerun_trigger'] = not st.session_state.get('rerun_trigger', False)
            with row_cols[2]:
                st.write("")
                if st.button("➕", key=f"{stone}_{row['Size']}_add"):
                    st.session_state['selected_stone_type'] = stone
                    st.session_state['selected_size'] = row['Size']
                    st.session_state['order_action'] = "add"
                    st.session_state['rerun_trigger'] = not st.session_state.get('rerun_trigger', False)
