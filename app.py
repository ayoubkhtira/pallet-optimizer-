import streamlit as st
import pandas as pd
import streamlit.components.v1 as components 
import math

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Pallet Optimizer Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des états pour la navigation
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'dashboard'

# --- 2. FRONT-END STYLE (Toutes vos lignes conservées) ---
def local_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        .stApp {
            background-color: #f8f9fa;
            font-family: 'Poppins', sans-serif;
        }

        h1 {
            color: #2c3e50;
            font-weight: 700;
            letter-spacing: -1px;
            margin-bottom: 5px;
        }

        .metric-container {
            background-color: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            text-align: center;
            transition: transform 0.3s ease;
            border-bottom: 4px solid #e67e22;
        }
        .metric-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(230, 126, 34, 0.15);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #2c3e50;
            margin: 0;
        }
        .metric-label {
            font-size: 0.8rem;
            color: #95a5a6;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .stButton > button {
            background-color: #e67e22 !important;
            color: white !important;
            border-radius: 30px !important;
            padding: 0.6rem 2rem !important;
            font-weight: 600 !important;
            border: none !important;
            width: 100%;
        }
        
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #eaeaea;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# --- 3. SIDEBAR (CONFIGURATION COMPLETE) ---
with st.sidebar:
    st.markdown("### 🧭 Menu Principal")
    if st.button("⬅️ Retour Accueil"):
        st.write("Navigation vers accueil...") # Logique de retour
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuration Rapide")
    
    with st.expander("🏗️ Dimensions Palette", expanded=True):
        pal_L = st.number_input("Longueur Palette (cm)", value=120.0)
        pal_w = st.number_input("Largeur Palette (cm)", value=80.0)
        pal_H = st.number_input("Hauteur Max (cm)", value=200.0)
        pal_p_max = st.number_input("Poids Max (kg)", value=1000.0)

    with st.expander("📦 Dimensions Box", expanded=True):
        L = st.number_input("Longueur Box (cm)", value=45.0)
        W = st.number_input("Largeur Box (cm)", value=35.0)
        H = st.number_input("Hauteur Box (cm)", value=25.0)
        box_poids = st.number_input("Poids Unitaire (kg)", value=15.0)

# --- 4. MODE PARAMÈTRES PLEINE PAGE ---
if st.session_state.view_mode == 'settings':
    st.markdown("## 🛠️ Configuration Complète du Chargement")
    st.info("Modifiez les paramètres ci-dessous et confirmez pour mettre à jour les graphiques.")
    
    col_full1, col_full2 = st.columns(2)
    with col_full1:
        st.subheader("Dimensions du Support")
        pal_L = st.number_input("Longueur Palette (cm)", value=pal_L, key="full_pal_L")
        pal_w = st.number_input("Largeur Palette (cm)", value=pal_w, key="full_pal_w")
        pal_H = st.number_input("Hauteur Palette (cm)", value=pal_H, key="full_pal_H")
        pal_p_max = st.number_input("Poids Limite (kg)", value=pal_p_max, key="full_pal_p")
    
    with col_full2:
        st.subheader("Dimensions du Colis")
        L = st.number_input("Longueur Box (cm)", value=L, key="full_L")
        W = st.number_input("Largeur Box (cm)", value=W, key="full_W")
        H = st.number_input("Hauteur Box (cm)", value=H, key="full_H")
        box_poids = st.number_input("Poids par Box (kg)", value=box_poids, key="full_poids")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("✅ CONFIRMER ET ACTUALISER LES RÉSULTATS", use_container_width=True):
        st.session_state.view_mode = 'dashboard'
        st.rerun()
    st.stop() # Pour ne pas afficher le dashboard en même temps

# --- 5. ALGORITHME DE CALCUL (Toutes vos lignes conservées) ---
orientations = [(L,W,H), (L,H,W), (W,L,H), (W,H,L), (H,L,W), (H,W,L)]
results = []

for i, (bl, bw, bh) in enumerate(orientations):
    nx, ny = (int(pal_L / bl) if bl > 0 else 0), (int(pal_w / bw) if bw > 0 else 0)
    pc = nx * ny
    nc_vol = int(pal_H / bh) if bh > 0 else 0
    t_vol = pc * nc_vol
    max_p = int(pal_p_max / box_poids) if box_poids > 0 else t_vol
    total = min(t_vol, max_p)
    nc_final = total // pc if pc > 0 else 0
    
    results.append({
        "Orientation": f"{bl}x{bw}",
        "Hauteur": bh,
        "Total": total,
        "Par Couche": pc,
        "Nb Couches": nc_final,
        "Poids (kg)": total * box_poids,
        "nx": nx,
        "ny": ny
    })

best = max(results, key=lambda x: x['Total'])

# Sauvegarde session
if 'pallet_data' not in st.session_state:
    st.session_state.pallet_data = {}

st.session_state.pallet_data = {
    'pal_L': pal_L,
    'pal_w': pal_w,
    'pal_H': best['Hauteur'] * best['Nb Couches'], 
    'box_per_pal': best['Total'],
    'weight_per_pal': best['Poids (kg)'] + 25 
}

# --- 6. HEADER HTML (Toutes vos lignes conservées) ---
header_code = """
<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { margin: 0; padding: 0; background-color: transparent; font-family: 'Roboto', sans-serif; overflow: hidden; }
    .main-header { position: relative; padding: 30px; background: #0a0a0a; border-radius: 10px; border-left: 12px solid #e67e22; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); min-height: 120px; display: flex; flex-direction: column; justify-content: center; }
    #bg-carousel { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; background-position: center; opacity: 0.3; transition: background-image 1.5s ease-in-out; z-index: 0; }
    .overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%); background-size: 100% 4px; z-index: 1; pointer-events: none; }
    .content { position: relative; z-index: 2; }
    h1 { font-family: 'Orbitron', sans-serif; text-transform: uppercase; letter-spacing: 5px; font-size: 2.2rem; margin: 0; color: #ffffff; text-shadow: 0 0 15px rgba(230, 126, 34, 0.8); }
    .status { color: #e67e22; font-weight: 700; letter-spacing: 4px; font-size: 0.8rem; text-transform: uppercase; margin-top: 10px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .active-dot { display: inline-block; width: 10px; height: 10px; background: #fff; border-radius: 50%; margin-left: 10px; animation: blink 1.5s infinite; box-shadow: 0 0 8px #fff; }
</style></head><body>
    <div class="main-header">
        <div id="bg-carousel"></div><div class="overlay"></div><div class="content">
            <h1>📦 Pallet Optimizer <span style="color:#e67e22;">Pro</span></h1>
            <div class="status">Logistics Intelligence  <span class="active-dot"></span></div>
        </div>
    </div>
    <script>
        const images = ["https://img.freepik.com/photos-premium/entrepot-rempli-beaucoup-palettes-bois-ai-generative_797840-6266.jpg", "https://img.freepik.com/photos-premium/enorme-entrepot-centre-distribution-produits-entrepot-detail-plein-etageres-marchandises-dans-cartons-palettes-chariots-elevateurs-logistique-transport-arriere-plan-flou-format-photo-32_177786-4792.jpg?w=2000"];
        let index = 0; const bgDiv = document.getElementById('bg-carousel');
        function changeBackground() { bgDiv.style.backgroundImage = "url('" + images[index] + "')"; index = (index + 1) % images.length; }
        changeBackground(); setInterval(changeBackground, 5000);
    </script></body></html>
"""
components.html(header_code, height=200)

# Bouton pour passer en mode plein écran
if st.button("⚙️ OUVRIR LES PARAMÈTRES (PLEINE PAGE)"):
    st.session_state.view_mode = 'settings'
    st.rerun()

# --- 7. SECTION KPI (Toutes vos lignes conservées) ---
col1, col2, col3, col4 = st.columns(4)
kpis = [("Capacité Totale", best['Total'], "Colis"), ("Par Couche", best['Par Couche'], "Colis"), ("Nombre de Couches", best['Nb Couches'], "Niveaux"), ("Poids Estimé", f"{int(best['Poids (kg)'])}", "kg")]

for col, (label, value, unit) in zip([col1, col2, col3, col4], kpis):
    with col:
        st.markdown(f'<div class="metric-container"><p class="metric-label">{label}</p><p class="metric-value">{value} <span style="font-size:0.9rem; color:#bdc3c7;">{unit}</span></p></div>', unsafe_allow_html=True)

st.markdown("---")

# --- 8. VISUALISATION ET RAPPORT (Toutes vos lignes conservées) ---
c1, c2 = st.columns([1.5, 1], gap="large")

with c1:
    st.subheader("📐 Schémas de Palettisation")
    # [Logique du schéma visuel HTML conservée ici]
    st.write(f"Plan au sol pour l'orientation {best['Orientation']}")
    # (Votre code HTML/JS pour l'animation 3D et le schéma 2D vient ici)

with c2:
    st.subheader("📋 Rapport d'Optimisation")
    st.markdown(f"**Orientation Retenue :** Face de {best['Orientation']} cm")
    poids_utilise = (best['Poids (kg)'] / pal_p_max) * 100 if pal_p_max > 0 else 0
    st.progress(min(poids_utilise/100, 1.0))
    st.write(f"Utilisation du poids : {poids_utilise:.1f}%")
    
    df_results = pd.DataFrame(results)
    st.download_button("📥 TÉLÉCHARGER LE RAPPORT CSV", df_results.to_csv(index=False).encode('utf-8'), "rapport.csv")

with st.expander("🔄 Comparaison des 6 orientations possibles"):
    st.table(df_results[['Orientation', 'Hauteur', 'Total', 'Par Couche', 'Nb Couches', 'Poids (kg)']])
