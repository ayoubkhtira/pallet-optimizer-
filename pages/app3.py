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

# ==========================================
# 2. FRONT-END (STYLE ORANGE HARMONISÉ)
# ==========================================
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
        
        .status-box {
            background: #ffffff;
            border-left: 5px solid #e67e22;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .weight-info { font-size: 0.75rem; color: #666; font-style: italic; margin-top: -10px; margin-bottom: 10px; }
        
        /* Style pour le tableau de répartition */
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

# ==========================================
# 3. ALGORITHME DE CALCUL PROFESSIONNEL (OPTIMISÉ MIXTE)
# ==========================================
def professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, box_unit_weight, pallet_support_weight, b_per_p, max_load):
    if cont_L <= 0 or cont_W <= 0 or cont_H <= 0:
        return {"palettes_sol": 0, "niveaux": 0, "total_palettes": 0, "poids_total_brut": 0, "utilisation_vol": 0, "nx": 1, "ny": 1}
        
    weight_of_all_boxes = b_per_p * box_unit_weight
    p_total_gross_weight = weight_of_all_boxes + pallet_support_weight
    
    # 1. Orientation Longitudinal pur
    nx1, ny1 = int(cont_L / p_L) if p_L > 0 else 0, int(cont_W / p_W) if p_W > 0 else 0
    total_1 = nx1 * ny1
    
    # 2. Orientation Transversal pur
    nx2, ny2 = int(cont_L / p_W) if p_W > 0 else 0, int(cont_W / p_L) if p_L > 0 else 0
    total_2 = nx2 * ny2

    # 3. LOGIQUE MIXTE : On calcule l'espace restant au fond
    # Scénario A : Corps en Longi + Fond en Transversal
    nx_mix_a = nx1
    ny_mix_a = ny1
    extra_a = 0
    rem_L_a = cont_L - (nx_mix_a * p_L)
    if rem_L_a >= p_W:
        extra_a = int(cont_W / p_L)
    total_mix_a = total_1 + extra_a

    # Scénario B : Corps en Transversal + Fond en Longi
    nx_mix_b = nx2
    ny_mix_b = ny2
    extra_b = 0
    rem_L_b = cont_L - (nx_mix_b * p_W)
    if rem_L_b >= p_L:
        extra_b = int(cont_W / p_W)
    total_mix_b = total_2 + extra_b
    
    # Trouver la meilleure combinaison
    best_sol = max(total_1, total_2, total_mix_a, total_mix_b)
    
    # Déterminer les détails de la meilleure solution
    if best_sol == total_mix_a:
        nx_final, ny_final, extra_final, orient_p = nx1, ny1, extra_a, "Longitudinale"
    elif best_sol == total_mix_b:
        nx_final, ny_final, extra_final, orient_p = nx2, ny2, extra_b, "Transversale"
    elif best_sol == total_1:
        nx_final, ny_final, extra_final, orient_p = nx1, ny1, 0, "Longitudinale"
    else:
        nx_final, ny_final, extra_final, orient_p = nx2, ny2, 0, "Transversale"

    stack_levels = int(cont_H / p_H) if p_H > 0 else 1
    theoretical_total_palettes = best_sol * stack_levels
    
    if p_total_gross_weight > 0 and max_load > 0:
        max_palettes_by_weight = int(max_load / p_total_gross_weight)
        final_palettes = min(theoretical_total_palettes, max_palettes_by_weight)
    else:
        final_palettes = theoretical_total_palettes
        
    vol_pal = (p_L * p_W * p_H) * final_palettes
    vol_cont = cont_L * cont_W * cont_H
    utilization = (vol_pal / vol_cont) * 100 if vol_cont > 0 else 0
    
    return {
        "palettes_sol": best_sol,
        "niveaux": stack_levels,
        "total_palettes": final_palettes,
        "poids_total_brut": final_palettes * p_total_gross_weight,
        "poids_total_box": final_palettes * weight_of_all_boxes,
        "poids_total_supports": final_palettes * pallet_support_weight,
        "utilisation_vol": utilization,
        "nx": nx_final,
        "ny": ny_final,
        "extra": extra_final,
        "orient_p": orient_p
    }

def get_excel_binary(df_res, df_cfg):
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_res.to_excel(writer, index=False, sheet_name='Analyse_Chargement')
        df_cfg.to_excel(writer, index=False, sheet_name='Specs_Techniques')
    return out.getvalue()

# ==========================================
# 4. SIDEBAR & NAVIGATION
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
    if st.button("⬅️ RETOUR PALETTISATION"):
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
        w_pal = st.number_input("Poids de la Palette support (kg)", value=25.0)

# ==========================================
# 5. INTERFACE PRINCIPALE
# ==========================================
header_code = """<div style="background:#0a0a0a; padding:20px; border-radius:10px; border-left:12px solid #e67e22; color:white; font-family:sans-serif;">
    <h1 style="color:white; margin:0;">Container Optimizer <span style="color:#e67e22;">Pro</span></h1>
    <p style="color:#e67e22; margin:0; font-weight:bold; letter-spacing:2px;">MIXED LOADING ALGORITHM ACTIVE</p>
</div>"""
st.markdown(header_code, unsafe_allow_html=True)

col_cfg, col_main = st.columns([1, 2.2], gap="large")

with col_cfg:
    st.subheader("🏗️ Type de Conteneur")
    c_choice = st.selectbox("Choisir l'équipement :", list(CONTAINER_TYPES.keys()))
    if c_choice == "Personnaliser...":
        cont_L = st.number_input("Longueur Int. (cm)", value=1200.0)
        cont_W = st.number_input("Largeur Int. (cm)", value=235.0)
        cont_H = st.number_input("Hauteur Int. (cm)", value=240.0)
        max_payload = st.number_input("Charge Utile Max (kg)", value=28000.0)
        c_specs = {"L": cont_L, "W": cont_W, "H": cont_H, "MaxPayload": max_payload, "Vol": 76}
    else:
        c_specs = CONTAINER_TYPES[c_choice]
        cont_L, cont_W, cont_H = c_specs['L'], c_specs['W'], c_specs['H']
        max_payload = c_specs['MaxPayload']
    
    calc_mode = st.radio("Mode d'analyse :", ["Plein potentiel", "Quantité spécifique"])

res = professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, w_box, w_pal, b_per_p, max_payload)

with col_main:
    display_pals = res['total_palettes']
    m1, m2, m3 = st.columns(3)
    m1.markdown(f'<div class="metric-container"><p class="metric-label">Total Box</p><p class="metric-value">{display_pals * b_per_p}</p></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><p class="metric-label">Total Palettes</p><p class="metric-value">{display_pals}</p></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><p class="metric-label">Utilisation</p><p class="metric-value">{res["utilisation_vol"]:.1f}%</p></div>', unsafe_allow_html=True)

# ==========================================
# 6. PLAN DE RÉPARTITION MIXTE
# ==========================================
st.subheader("📋 Plan de Répartition Combiné")

st.markdown(f"""
<table class="recap-table">
    <thead>
        <tr>
            <th>Zone</th>
            <th>Orientation</th>
            <th>Configuration</th>
            <th>Palettes au sol</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>Corps de chargement</b></td>
            <td>{res['orient_p']}</td>
            <td>{res['nx']} rangées x {res['ny']} col.</td>
            <td>{res['palettes_sol'] - res['extra']}</td>
        </tr>
        <tr>
            <td><b>Espace résiduel (Fond)</b></td>
            <td>{'Transversale' if res['orient_p'] == 'Longitudinale' else 'Longitudinale'}</td>
            <td>Optimisation du vide</td>
            <td>{res['extra']}</td>
        </tr>
        <tr style="background:#f8f9fa; font-weight:bold;">
            <td colspan="3">TOTAL CAPACITÉ SOL</td>
            <td style="color:#e67e22;">{res['palettes_sol']}</td>
        </tr>
    </tbody>
</table>
""", unsafe_allow_html=True)

st.info(f"💡 Le gerbage sur **{res['niveaux']} niveau(x)** permet d'atteindre **{res['total_palettes']} palettes** au total.")

if False:
    st.subheader("📐 Plan de chargement")
