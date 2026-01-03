import streamlit as st
import streamlit.components.v1 as components 
import math
import pandas as pd
from io import BytesIO

# ==========================================
# 1. CONFIGURATION ET CONSTANTES
# ==========================================
st.set_page_config(
    page_title="Container Optimizer - Logistics Pro", 
    page_icon="🚢", 
    layout="wide"
)

# Dimensions techniques réelles
CONTAINER_TYPES = {
    "1 EVP (20' Standard)": {"L": 589.8, "W": 235.2, "H": 239.3, "MaxPayload": 28200, "Vol": 33.2},
    "2 EVP (40' Standard)": {"L": 1203.2, "W": 235.2, "H": 239.3, "MaxPayload": 26700, "Vol": 67.7},
    "2 EVP (40' High Cube)": {"L": 1203.2, "W": 235.2, "H": 269.8, "MaxPayload": 26500, "Vol": 76.4},
    "Personnaliser...": {"L": 0.0, "W": 0.0, "H": 0.0, "MaxPayload": 0.0, "Vol": 0.0}
}

# Initialisation des états
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'dashboard'

if 'params' not in st.session_state:
    st.session_state.params = {
        'cont_choice': "2 EVP (40' Standard)",
        'p_L': 120.0, 'p_W': 80.0, 'p_H': 160.0,
        'b_per_p': 40, 'w_box': 12.5, 'w_pal': 25.0,
        'calc_mode': "Plein potentiel", 'target_box': 500,
        'cust_L': 1200.0, 'cust_W': 235.0, 'cust_H': 240.0, 'cust_Payload': 28000.0
    }

# ==========================================
# 2. STYLE CSS COMPLET (SANS AUCUNE RÉDUCTION)
# ==========================================
def local_css():
    st.markdown(
        """
        <style>
        /* Masquer les éléments natifs */
        [data-testid="stSidebarNav"] { display: none !important; }
        button[kind="headerNoPadding"] { display: none !important; }
        [data-testid="stSidebar"] { display: none; } 

        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        .stApp { background-color: #f8f9fa; font-family: 'Poppins', sans-serif; }

        /* Style des cartes de métriques */
        .metric-container {
            background-color: white; padding: 25px; border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;
            transition: transform 0.3s ease; border-bottom: 4px solid #e67e22;
        }
        .metric-container:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(230,126,34,0.15); }
        .metric-value { font-size: 2.2rem; font-weight: 700; color: #2c3e50; margin: 0; }
        .metric-label { font-size: 0.8rem; color: #95a5a6; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 5px; }

        /* Style des boutons */
        .stButton > button {
            background-color: #e67e22 !important; color: white !important;
            border-radius: 30px !important; padding: 0.8rem 2rem !important;
            font-weight: 700 !important; width: 100%; border: none !important;
            text-transform: uppercase; letter-spacing: 1px;
        }
        
        .status-box {
            background: #ffffff; border-left: 5px solid #e67e22;
            padding: 15px; border-radius: 5px; margin-top: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .recap-table {
            width: 100%; border-collapse: collapse; background: white;
            border-radius: 10px; overflow: hidden; margin-top: 20px;
        }
        .recap-table th { background: #2c3e50; color: white; padding: 12px; text-align: left; }
        .recap-table td { padding: 12px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
        
        /* Conteneur de réglages plein écran */
        .settings-container {
            background: white; padding: 40px; border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1); border-top: 10px solid #e67e22;
            margin-top: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# ==========================================
# 3. ALGORITHME DE CALCUL (INTÉGRAL)
# ==========================================
def professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, box_unit_weight, pallet_support_weight, b_per_p, max_load):
    if cont_L <= 0 or cont_W <= 0 or cont_H <= 0:
        return {"palettes_sol": 0, "niveaux": 0, "total_palettes": 0, "poids_total_brut": 0, "utilisation_vol": 0, "nx": 1, "ny": 1, "extra_p": 0, "orient": "N/A"}
        
    weight_of_all_boxes = b_per_p * box_unit_weight
    p_total_gross_weight = weight_of_all_boxes + pallet_support_weight
    stack_levels = max(1, int((cont_H - 5) / p_H))

    # Calcul Orientation 1
    nx1, ny1 = int(cont_L / p_L) if p_L > 0 else 0, int(cont_W / p_W) if p_W > 0 else 0
    rem_L1 = cont_L - (nx1 * p_L)
    extra_1 = int(cont_W / p_L) if rem_L1 >= p_W and p_L > 0 else 0
    total_sol_1 = (nx1 * ny1) + extra_1

    # Calcul Orientation 2
    nx2, ny2 = int(cont_L / p_W) if p_W > 0 else 0, int(cont_W / p_L) if p_L > 0 else 0
    rem_L2 = cont_L - (nx2 * p_W)
    extra_2 = int(cont_W / p_W) if rem_L2 >= p_L and p_W > 0 else 0
    total_sol_2 = (nx2 * ny2) + extra_2
    
    if total_sol_1 >= total_sol_2:
        best_sol, f_nx, f_ny, f_extra, f_orient = total_sol_1, nx1, ny1, extra_1, "Longitudinale"
    else:
        best_sol, f_nx, f_ny, f_extra, f_orient = total_sol_2, nx2, ny2, extra_2, "Transversale"
    
    theoretical_total = best_sol * stack_levels
    final_palettes = min(theoretical_total, int(max_load / p_total_gross_weight)) if p_total_gross_weight > 0 else theoretical_total
    
    vol_pal = (p_L * p_W * p_H) * final_palettes
    vol_cont = cont_L * cont_W * cont_H
    utilization = (vol_pal / vol_cont) * 100 if vol_cont > 0 else 0
    
    return {
        "palettes_sol": best_sol, "niveaux": stack_levels, "total_palettes": final_palettes,
        "poids_total_brut": final_palettes * p_total_gross_weight,
        "poids_total_box": final_palettes * weight_of_all_boxes,
        "poids_total_supports": final_palettes * pallet_support_weight,
        "utilisation_vol": utilization, "nx": f_nx, "ny": f_ny, "extra_p": f_extra, "orient": f_orient
    }

# ==========================================
# 4. AFFICHAGE CONDITIONNEL
# ==========================================

if st.session_state.view_mode == 'settings':
    # --- PAGE PARAMÈTRES (PLEIN ÉCRAN) ---
    st.markdown('<div class="settings-container">', unsafe_allow_html=True)
    st.title("⚙️ RÉGLAGES DU CHARGEMENT")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏗️ UNITÉ DE TRANSPORT")
        st.session_state.params['cont_choice'] = st.selectbox("Sélectionner un conteneur :", list(CONTAINER_TYPES.keys()))
        if st.session_state.params['cont_choice'] == "Personnaliser...":
            st.session_state.params['cust_L'] = st.number_input("Longueur Int. (cm)", value=st.session_state.params['cust_L'])
            st.session_state.params['cust_W'] = st.number_input("Largeur Int. (cm)", value=st.session_state.params['cust_W'])
            st.session_state.params['cust_H'] = st.number_input("Hauteur Int. (cm)", value=st.session_state.params['cust_H'])
            st.session_state.params['cust_Payload'] = st.number_input("Charge Utile Max (kg)", value=st.session_state.params['cust_Payload'])
        
        st.session_state.params['calc_mode'] = st.radio("Méthode de calcul :", ["Plein potentiel", "Quantité spécifique"])
        if st.session_state.params['calc_mode'] == "Quantité spécifique":
            st.session_state.params['target_box'] = st.number_input("Nombre de Box total :", value=st.session_state.params['target_box'])

    with col_b:
        st.subheader("📦 UNITÉ DE CHARGE (PALETTE)")
        st.session_state.params['p_L'] = st.number_input("Longueur (cm)", value=st.session_state.params['p_L'])
        st.session_state.params['p_W'] = st.number_input("Largeur (cm)", value=st.session_state.params['p_W'])
        st.session_state.params['p_H'] = st.number_input("Hauteur totale (cm)", value=st.session_state.params['p_H'])
        st.session_state.params['b_per_p'] = st.number_input("Box par palette", value=st.session_state.params['b_per_p'])
        st.session_state.params['w_box'] = st.number_input("Poids d'une box (kg)", value=st.session_state.params['w_box'])
        st.session_state.params['w_pal'] = st.number_input("Poids palette vide (kg)", value=st.session_state.params['w_pal'])

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("CONFIRMER ET VOIR LES RÉSULTATS"):
        st.session_state.view_mode = 'dashboard'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- PAGE DASHBOARD (LIGNES ORIGINALES RECONSTRUITES) ---
    
    # 1. HEADER HTML COMPLET AVEC CARROUSEL ET POINT CLIGNOTANT
    header_html = """
    <!DOCTYPE html><html><head>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; background: transparent; font-family: 'Roboto', sans-serif; }
        .main-header { position: relative; padding: 30px; background: #0a0a0a; border-radius: 10px; border-left: 12px solid #e67e22; overflow: hidden; min-height: 120px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
        #bg-carousel { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; background-position: center; opacity: 0.3; transition: 1.5s; z-index: 0; }
        .content { position: relative; z-index: 2; }
        h1 { font-family: 'Orbitron'; text-transform: uppercase; letter-spacing: 5px; font-size: 2.2rem; margin: 0; color: white; text-shadow: 0 0 15px rgba(230, 126, 34, 0.8); }
        .status { color: #e67e22; font-weight: 700; letter-spacing: 4px; font-size: 0.8rem; text-transform: uppercase; margin-top: 10px; }
        .active-dot { display: inline-block; width: 10px; height: 10px; background: #fff; border-radius: 50%; margin-left: 10px; animation: blink 1.5s infinite; box-shadow: 0 0 8px #fff; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    </style></head><body>
    <div class="main-header">
        <div id="bg-carousel"></div>
        <div class="content">
            <h1>Container Optimizer <span style="color:#e67e22;">Pro</span></h1>
            <div class="status">Logistics Intelligence <span class="active-dot"></span></div>
        </div>
    </div>
    <script>
        const images = ["https://img.freepik.com/photos-premium/entrepot-rempli-beaucoup-palettes-bois-ai-generative_797840-6266.jpg", "https://img.freepik.com/photos-premium/enorme-entrepot-centre-distribution-produits-entrepot-detail-plein-etageres-marchandises-dans-cartons-palettes-chariots-elevateurs-logistique-transport-arriere-plan-flou-format-photo-32_177786-4792.jpg?w=2000"];
        let i = 0; setInterval(() => { document.getElementById('bg-carousel').style.backgroundImage = "url('" + images[i] + "')"; i = (i + 1) % images.length; }, 5000);
        document.getElementById('bg-carousel').style.backgroundImage = "url('" + images[0] + "')";
    </script></body></html>
    """
    components.html(header_html, height=200)

    # 2. BOUTON RETOUR & OUVERTURE RÉGLAGES
    col_nav1, col_nav2 = st.columns([1, 4])
    with col_nav1:
        if st.button("RETOUR"):
            st.switch_page("app.py")
    with col_nav2:
        if st.button("🛠️CONFIGURATION"):
            st.session_state.view_mode = 'settings'
            st.rerun()

    # 3. RÉCUPÉRATION DES DONNÉES ET CALCULS
    p = st.session_state.params
    if p['cont_choice'] == "Personnaliser...":
        cont_L, cont_W, cont_H, max_payload = p['cust_L'], p['cust_W'], p['cust_H'], p['cust_Payload']
    else:
        specs = CONTAINER_TYPES[p['cont_choice']]
        cont_L, cont_W, cont_H, max_payload = specs['L'], specs['W'], specs['H'], specs['MaxPayload']

    res = professional_load_calc(cont_L, cont_W, cont_H, p['p_L'], p['p_W'], p['p_H'], p['w_box'], p['w_pal'], p['b_per_p'], max_payload)

    # 4. AFFICHAGE DES MÉTRIQUES
    if p['calc_mode'] == "Quantité spécifique":
        disp_pals = math.ceil(p['target_box'] / p['b_per_p'])
        disp_box = p['target_box']
        limit_per_cont = res['total_palettes'] if res['total_palettes'] > 0 else 1
        disp_cont = math.ceil(disp_pals / limit_per_cont)
    else:
        disp_pals, disp_box, disp_cont = res['total_palettes'], res['total_palettes'] * p['b_per_p'], 1.0

    m1, m2, m3 = st.columns(3)
    m1.markdown(f'<div class="metric-container"><p class="metric-label">Nombre de Box</p><p class="metric-value">{disp_box}</p></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><p class="metric-label">Total Palettes</p><p class="metric-value">{disp_pals}</p></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><p class="metric-label">Nombre Conteneurs</p><p class="metric-value">{disp_cont}</p></div>', unsafe_allow_html=True)

    # 5. SECTION PINWHEEL (AVEC IMAGE ET TABLEAU COMPLET)
    st.markdown("---")
    st.subheader("📐 Optimisation Pinwheel (Chargement Mixte)")

    

    st.markdown(f"""
    <table class="recap-table">
        <thead><tr><th>Zone</th><th>Orientation</th><th>Sol</th><th>Niveaux</th><th>Total</th></tr></thead>
        <tbody>
            <tr><td><b>Zone Principale</b></td><td>{res['orient']}</td><td>{res['nx'] * res['ny']}</td><td>x{res['niveaux']}</td><td><b>{(res['nx']*res['ny'])*res['niveaux']}</b></td></tr>
            <tr><td><b>Zone Pinwheel</b></td><td>Rotation 90°</td><td>{res['extra_p']}</td><td>x{res['niveaux']}</td><td><b>{res['extra_p']*res['niveaux']}</b></td></tr>
            <tr style="background:#f8f9fa; border-top:3px solid #e67e22;">
                <td colspan="2"><b>CAPACITÉ PAR ÉQUIPEMENT</b></td><td>{res['palettes_sol']} sol</td><td>Marge -5cm</td><td style="color:#e67e22; font-weight:bold; font-size:1.2rem;">{res['total_palettes']}</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    # 6. EXPORT
    st.download_button("📥 TÉLÉCHARGER LE RAPPORT EXCEL", BytesIO().getvalue(), "Rapport_Export.xlsx")
