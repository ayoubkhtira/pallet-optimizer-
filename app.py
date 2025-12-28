import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Pallet Optimizer Pro",
    page_icon="📦",
    layout="wide"
)

# --- CSS PERSONNALISÉ (FRONT-END PREMIUM) ---
def local_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)), 
                        url("https://input-file-url.com/v2/image/62111/r-H_gqM_tUj98p8_86y97_37y-25_f50_25-0-0-0");
            background-attachment: fixed;
            background-size: cover;
        }

        /* Cartes de résultats */
        .metric-card {
            background-color: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            text-align: center;
            border-top: 5px solid #3498db;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #1e3799;
            margin-bottom: 0;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #7f8c8d;
            text-transform: uppercase;
            font-weight: 600;
        }

        /* Grille de la palette */
        .pallet-container {
            background-color: #d2b48c;
            border: 12px solid #8b4513;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# --- HEADER ---
st.title("📦 Pallet Loading Optimizer Pro")
st.caption("Optimisation mathématique basée sur les 6 orientations de box possibles.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("📏 Dimensions Palette", expanded=True):
        pal_L = st.number_input("Longueur (cm)", value=120.0)
        pal_w = st.number_input("Largeur (cm)", value=80.0)
        pal_H = st.number_input("Hauteur Max (cm)", value=200.0)
        pal_p_max = st.number_input("Poids Max (kg)", value=1000.0)

    with st.expander("📦 Dimensions Box", expanded=True):
        L = st.number_input("Longueur Box (cm)", value=45.0)
        W = st.number_input("Largeur Box (cm)", value=35.0)
        H = st.number_input("Hauteur Box (cm)", value=25.0)
        box_poids = st.number_input("Poids Unit. (kg)", value=15.0)

# --- CALCUL DES 6 ORIENTATIONS ---
orientations = [(L,W,H), (L,H,W), (W,L,H), (W,H,L), (H,L,W), (H,W,L)]
results = []

for i, (bl, bw, bh) in enumerate(orientations):
    nx, ny = int(pal_L / bl), int(pal_w / bw)
    pc = nx * ny
    nc_vol = int(pal_H / bh)
    t_vol = pc * nc_vol
    max_p = int(pal_p_max / box_poids) if box_poids > 0 else t_vol
    total = min(t_vol, max_p)
    nc_final = total // pc if pc > 0 else 0
    
    results.append({
        "Orientation": f"Face {bl}x{bw}",
        "Total": total,
        "Par Couche": pc,
        "Nb Couches": nc_final,
        "Poids (kg)": total * box_poids,
        "nx": nx, "ny": ny
    })

best = max(results, key=lambda x: x['Total'])

# --- AFFICHAGE DES RÉSULTATS ---
col1, col2, col3, col4 = st.columns(4)

metrics = [
    ("Total Box", best['Total']),
    ("Par Couche", best['Par Couche']),
    ("Nb Couches", best['Nb Couches']),
    ("Poids Total", f"{best['Poids (kg)']} kg")
]

for col, (label, value) in zip([col1, col2, col3, col4], metrics):
    col.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">{label}</p>
            <p class="metric-value">{value}</p>
        </div>
    """, unsafe_allow_html=True)

st.write("")

c1, c2 = st.columns([1.5, 1])

with c1:
    st.subheader("📐 Plan de Chargement (Couche de base)")
    
    # Création du dessin avec CSS Grid
    box_divs = "".join(['<div style="background:#3498db; border:1px solid white; border-radius:3px;"></div>' for _ in range(best['Par Couche'])])
    grid_html = f"""
    <div class="pallet-container" style="
        display: grid; 
        grid-template-columns: repeat({best['nx']}, 1fr); 
        grid-template-rows: repeat({best['ny']}, 1fr); 
        gap: 5px; 
        height: 400px;
    ">
        {box_divs}
    </div>
    """
    st.markdown(grid_html, unsafe_allow_html=True)

with c2:
    st.subheader("📋 Rapport de Calcul")
    st.info(f"**Orientation retenue :** {best['Orientation']} cm au sol.")
    
    # Bouton de téléchargement
    df_results = pd.DataFrame(results)
    csv = df_results.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Télécharger le rapport (CSV)",
        data=csv,
        file_name='rapport_palettisation.csv',
        mime='text/csv',
    )
    
    # Alerte si limité par le poids
    poids_capacite = (best['Poids (kg)'] / pal_p_max) * 100
    st.write(f"**Utilisation de la charge utile :** {poids_capacite:.1f}%")
    st.progress(min(poids_capacite/100, 1.0))
    
    if poids_capacite >= 95:
        st.error("🚨 LIMITE DE POIDS ATTEINTE")
    elif best['Nb Couches'] * (L if "Face L" in best['Orientation'] else H) >= pal_H * 0.9:
        st.warning("📏 LIMITE DE HAUTEUR ATTEINTE")

st.divider()
with st.expander("🔄 Voir les 6 probabilités testées"):
    st.dataframe(df_results[['Orientation', 'Total', 'Par Couche', 'Nb Couches', 'Poids (kg)']], use_container_width=True)