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

# Dimensions techniques réelles (Espace de manoeuvre inclus)
CONTAINER_TYPES = {
    "1 EVP (20' Standard)": {"L": 589.8, "W": 235.2, "H": 239.3, "MaxPayload": 28200, "Vol": 33.2},
    "2 EVP (40' Standard)": {"L": 1203.2, "W": 235.2, "H": 239.3, "MaxPayload": 26700, "Vol": 67.7},
    "2 EVP (40' High Cube)": {"L": 1203.2, "W": 235.2, "H": 269.8, "MaxPayload": 26500, "Vol": 76.4},
    "Personnaliser...": {"L": 0.0, "W": 0.0, "H": 0.0, "MaxPayload": 0.0, "Vol": 0.0}
}

# Initialisation de l'état de la sidebar (Fonctionnalité Moderne)
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'

# ==========================================
# 2. FRONT-END (STYLE ORANGE HARMONISÉ)
# ==========================================
def local_css():
    st.markdown(
        """
        <style>
        /* FONCTIONNALITÉ MODERNE : Masquer navigation et flèche */
        [data-testid="stSidebarNav"] { display: none !important; }
        button[kind="headerNoPadding"] { display: none !important; }
        
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
        
        .status-box {
            background: #ffffff;
            border-left: 5px solid #e67e22;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .weight-info { font-size: 0.75rem; color: #666; font-style: italic; margin-top: -10px; margin-bottom: 10px; }
        
        .recap-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
        }
        .recap-table th { background: #2c3e50; color: white; padding: 12px; text-align: left; }
        .recap-table td { padding: 12px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# Logique de fermeture forcée si l'état est 'collapsed'
if st.session_state.sidebar_state == 'collapsed':
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)

# ==========================================
# 3. ALGORITHME DE CALCUL PROFESSIONNEL
# ==========================================
def professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, box_unit_weight, pallet_support_weight, b_per_p, max_load):
    if cont_L <= 0 or cont_W <= 0 or cont_H <= 0:
        return {"palettes_sol": 0, "niveaux": 0, "total_palettes": 0, "poids_total_brut": 0, "utilisation_vol": 0, "nx": 1, "ny": 1, "extra_p": 0, "orient": "N/A"}
        
    weight_of_all_boxes = b_per_p * box_unit_weight
    p_total_gross_weight = weight_of_all_boxes + pallet_support_weight
    
    stack_levels = int((cont_H - 5) / p_H) if p_H > 0 else 1
    if stack_levels < 1: stack_levels = 1

    nx1, ny1 = int(cont_L / p_L) if p_L > 0 else 0, int(cont_W / p_W) if p_W > 0 else 0
    rem_L1 = cont_L - (nx1 * p_L)
    extra_1 = int(cont_W / p_L) if rem_L1 >= p_W and p_L > 0 else 0
    total_sol_1 = (nx1 * ny1) + extra_1

    nx2, ny2 = int(cont_L / p_W) if p_W > 0 else 0, int(cont_W / p_L) if p_L > 0 else 0
    rem_L2 = cont_L - (nx2 * p_W)
    extra_2 = int(cont_W / p_W) if rem_L2 >= p_L and p_W > 0 else 0
    total_sol_2 = (nx2 * ny2) + extra_2
    
    if total_sol_1 >= total_sol_2:
        best_sol, f_nx, f_ny, f_extra, f_orient = total_sol_1, nx1, ny1, extra_1, "Longitudinale"
    else:
        best_sol, f_nx, f_ny, f_extra, f_orient = total_sol_2, nx2, ny2, extra_2, "Transversale"
    
    theoretical_total = best_sol * stack_levels
    
    if p_total_gross_weight > 0 and max_load > 0:
        max_pals_weight = int(max_load / p_total_gross_weight)
        final_palettes = min(theoretical_total, max_pals_weight)
    else:
        final_palettes = theoretical_total
        
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

def get_excel_binary(df_res, df_cfg):
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_res.to_excel(writer, index=False, sheet_name='Analyse_Chargement')
        df_cfg.to_excel(writer, index=False, sheet_name='Specs_Techniques')
    return out.getvalue()

# ==========================================
# 4. SIDEBAR & NAVIGATION (ORIGINAL COMPLET)
# ==========================================
with st.sidebar:
    st.markdown("""
        <style>
        .stSidebar [data-testid="stVerticalBlock"] { gap: 0.5rem; }
        .back-btn-container { padding: 10px 0px; border-bottom: 1px solid #eee; margin-bottom: 15px; }
        .stSidebar .stButton > button {
            background-color: transparent !important;
            color: #e67e22 !important;
            border: 2px solid #e67e22 !important;
            transition: all 0.3s ease !important;
        }
        .stSidebar .stButton > button:hover {
            background-color: #e67e22 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
    if st.button("RETOUR PALETTISATION"):
        st.switch_page("app.py")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ PARAMÈTRES")
    with st.expander("🏗️ DIMENSIONS & QUANTITÉ", expanded=True):
        p_data = st.session_state.get('pallet_data', {})
        p_L = st.number_input("Longueur Palette (cm)", value=float(p_data.get('pal_L', 120)))
        p_W = st.number_input("Largeur Palette (cm)", value=float(p_data.get('pal_w', 80)))
        p_H = st.number_input("Hauteur avec Box (cm)", value=float(p_data.get('pal_H', 160)))
        b_per_p = st.number_input("Nombre de Box par Palette", value=int(p_data.get('box_per_pal', 40)))

    with st.expander("⚖️ MASSE DES COMPOSANTS", expanded=True):
        w_box = st.number_input("Poids d'une seule Box (kg)", value=12.5)
        st.markdown(f'<p class="weight-info">Soit {w_box * b_per_p} kg de box par palette</p>', unsafe_allow_html=True)
        w_pal = st.number_input("Poids de la Palette support (kg)", value=25.0)
        st.markdown('<p class="weight-info">Poids du support bois/plastique seul</p>', unsafe_allow_html=True)
        total_p_weight = (w_box * b_per_p) + w_pal
        st.markdown(f"**Poids Brut / Palette :** `{total_p_weight} kg`")

# ==========================================
# 5. INTERFACE PRINCIPALE (HEADER + BOUTON TOGGLE)
# ==========================================
header_code = """
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { margin: 0; padding: 0; background-color: transparent; font-family: 'Roboto', sans-serif; overflow: hidden; }
    .main-header {
        position: relative; padding: 30px; background: #0a0a0a; border-radius: 10px;
        border-left: 12px solid #e67e22; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        min-height: 120px; display: flex; flex-direction: column; justify-content: center;
    }
    #bg-carousel {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-size: cover; background-position: center; opacity: 0.3; transition: background-image 1.5s ease-in-out; z-index: 0;
    }
    .overlay {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%);
        background-size: 100% 4px; z-index: 1; pointer-events: none;
    }
    .content { position: relative; z-index: 2; }
    h1 { font-family: 'Orbitron', sans-serif; text-transform: uppercase; letter-spacing: 5px; font-size: 2.2rem; margin: 0; color: #ffffff; text-shadow: 0 0 15px rgba(230, 126, 34, 0.8); }
    .status { color: #e67e22; font-weight: 700; letter-spacing: 4px; font-size: 0.8rem; text-transform: uppercase; margin-top: 10px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .active-dot { display: inline-block; width: 10px; height: 10px; background: #fff; border-radius: 50%; margin-left: 10px; animation: blink 1.5s infinite; box-shadow: 0 0 8px #fff; }
</style>
</head>
<body>
    <div class="main-header">
        <div id="bg-carousel"></div>
        <div class="overlay"></div>
        <div class="content">
            <h1> Container Optimizer <span style="color:#e67e22;">Pro</span></h1>
            <div class="status">Logistics Intelligence  <span class="active-dot"></span></div>
        </div>
    </div>
    <script>
        const images = ["https://img.freepik.com/photos-premium/entrepot-rempli-beaucoup-palettes-bois-ai-generative_797840-6266.jpg", "https://img.freepik.com/photos-premium/enorme-entrepot-centre-distribution-produits-entrepot-detail-plein-etageres-marchandises-dans-cartons-palettes-chariots-elevateurs-logistique-transport-arriere-plan-flou-format-photo-32_177786-4792.jpg?w=2000"];
        let index = 0;
        const bgDiv = document.getElementById('bg-carousel');
        function changeBackground() {
            bgDiv.style.backgroundImage = "url('" + images[index] + "')";
            index = (index + 1) % images.length;
        }
        changeBackground();
        setInterval(changeBackground, 5000);
    </script>
</body>
</html>
"""
components.html(header_code, height=200)

# BOUTON TOGGLE (AJOUT MODERNE)
col_toggle, _ = st.columns([0.2, 0.8])
with col_toggle:
    toggle_label = "FERMER" if st.session_state.sidebar_state == 'expanded' else "🛠️ RÉGLAGES"
    if st.button(toggle_label):
        st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'
        st.rerun()

col_cfg, col_main = st.columns([1, 2.2], gap="large")

with col_cfg:
    st.subheader("🏗️ Type de Conteneur")
    c_choice = st.selectbox("Choisir l'équipement :", list(CONTAINER_TYPES.keys()))
    
    if c_choice == "Personnaliser...":
        st.info("Saisissez vos dimensions personnalisées :")
        cont_L = st.number_input("Longueur Int. (cm)", value=1200.0)
        cont_W = st.number_input("Largeur Int. (cm)", value=235.0)
        cont_H = st.number_input("Hauteur Int. (cm)", value=240.0)
        max_payload = st.number_input("Charge Utile Max (kg)", value=28000.0)
        vol_cust = (cont_L * cont_W * cont_H) / 1000000
        c_specs = {"L": cont_L, "W": cont_W, "H": cont_H, "MaxPayload": max_payload, "Vol": round(vol_cust, 2)}
    else:
        c_specs = CONTAINER_TYPES[c_choice]
        cont_L, cont_W, cont_H = c_specs['L'], c_specs['W'], c_specs['H']
        max_payload = c_specs['MaxPayload']
    
    st.markdown(f"""
    <div class="status-box">
        <b>Spécifications Actuelles :</b><br>
        • Longueur : {cont_L} cm<br>
        • Largeur : {cont_W} cm<br>
        • Hauteur : {cont_H} cm<br>
        • Charge Max : {max_payload} kg<br>
        • Volume : {c_specs['Vol']} m³
    </div>
    """, unsafe_allow_html=True)
    
    calc_mode = st.radio("Mode d'analyse :", ["Plein potentiel", "Quantité spécifique"])

res = professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, w_box, w_pal, b_per_p, max_payload)

with col_main:
    if calc_mode == "Quantité spécifique":
        target_box = st.number_input("Nombre de Box à charger :", value=500, step=50)
        needed_pals = math.ceil(target_box / b_per_p) if b_per_p > 0 else 0
        limit_pal_per_cont = res['total_palettes'] if res['total_palettes'] > 0 else 1
        needed_conts = math.ceil(needed_pals / limit_pal_per_cont)
        display_pals, display_box, display_cont = needed_pals, target_box, needed_conts
    else:
        display_pals, display_box, display_cont = res['total_palettes'], res['total_palettes'] * b_per_p, 1.0

    m1, m2, m3 = st.columns(3)
    metrics = [("Total Box", display_box), ("Total Palettes", display_pals), ("Nombre Conteneurs", display_cont)]
    for col, (lab, val) in zip([m1, m2, m3], metrics):
        col.markdown(f'<div class="metric-container"><p class="metric-label">{lab}</p><p class="metric-value">{val}</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Répartition de la Charge Utile")
    total_brut = res['poids_total_brut']
    if total_brut > 0:
        st.markdown(f"""<div style="width: 100%; background-color: #eee; border-radius: 10px; height: 30px; display: flex; overflow: hidden; border: 1px solid #ddd;"><div style="width: {(res['poids_total_box']/total_brut)*100}%; background: #e67e22; height: 100%;"></div><div style="width: {(res['poids_total_supports']/total_brut)*100}%; background: #2c3e50; height: 100%;"></div></div>""", unsafe_allow_html=True)

# ==========================================
# 6. RAPPORT D'OPTIMISATION PINWHEEL
# ==========================================
st.subheader("📐 Optimisation du Chargement Mixte (Pinwheel)")



st.markdown(f"""
<table class="recap-table">
    <thead>
        <tr>
            <th>Disposition</th>
            <th>Orientation</th>
            <th>Palettes au sol</th>
            <th>Gerbage (H)</th>
            <th>Total Palettes</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>Sens Principal</b></td>
            <td>{res['orient']}</td>
            <td>{res['nx'] * res['ny']}</td>
            <td>x {res['niveaux']} niveaux</td>
            <td><b>{(res['nx'] * res['ny']) * res['niveaux']}</b></td>
        </tr>
        <tr>
            <td><b>Sens Pinwheel (Extra)</b></td>
            <td>Tournée à 90°</td>
            <td>{res['extra_p']}</td>
            <td>x {res['niveaux']} niveaux</td>
            <td><b>{res['extra_p'] * res['niveaux']}</b></td>
        </tr>
        <tr style="background:#f8f9fa; border-top: 3px solid #e67e22;">
            <td colspan="2"><b>CAPACITÉ PAR CONTENEUR</b></td>
            <td style="font-weight:bold;">{res['palettes_sol']} (Sol)</td>
            <td colspan="1">Marge de sécurité (-5cm)</td>
            <td style="color:#e67e22; font-weight:bold; font-size:1.2rem;">{res['total_palettes']}</td>
        </tr>
    </tbody>
</table>
""", unsafe_allow_html=True)

df_res = pd.DataFrame({"Item": ["Palettes", "Poids (kg)", "Conteneurs"], "Valeur": [display_pals, res['poids_total_brut'], display_cont]})
xl_file = get_excel_binary(df_res, pd.DataFrame([c_specs]))
st.download_button("📥 TÉLÉCHARGER LE RAPPORT", xl_file, "Export_Logistique.xlsx")

if False:
    st.write("Section neutralisée")
