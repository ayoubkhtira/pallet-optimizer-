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
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# ==========================================
# 3. ALGORITHME DE CALCUL PROFESSIONNEL (MIXTE)
# ==========================================
def professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, box_unit_weight, pallet_support_weight, b_per_p, max_load):
    if cont_L <= 0 or cont_W <= 0 or cont_H <= 0:
        return {"palettes_sol": 0, "niveaux": 0, "total_palettes": 0, "poids_total_brut": 0, "utilisation_vol": 0}
        
    p_total_weight = (b_per_p * box_unit_weight) + pallet_support_weight
    stack_levels = int(cont_H / p_H) if p_H > 0 else 1

    p_long = max(p_L, p_W)
    p_short = min(p_L, p_W)
    
    # Calcul mixte
    rows_main = int(cont_L / p_long)
    palettes_main = rows_main * int(cont_W / p_short)
    
    rest_L = cont_L - (rows_main * p_long)
    palettes_rotated = 0
    if rest_L >= p_short:
        palettes_rotated = int(cont_W / p_long)

    best_sol_sol = palettes_main + palettes_rotated
    theoretical_total = best_sol_sol * stack_levels
    
    if p_total_weight > 0 and max_load > 0:
        final_palettes = min(theoretical_total, int(max_load / p_total_weight))
    else:
        final_palettes = theoretical_total
        
    return {
        "palettes_sol": best_sol_sol,
        "palettes_main": palettes_main,
        "palettes_rotated": palettes_rotated,
        "niveaux": stack_levels,
        "total_palettes": final_palettes,
        "poids_total_brut": final_palettes * p_total_weight,
        "poids_total_box": final_palettes * (b_per_p * box_unit_weight),
        "poids_total_supports": final_palettes * pallet_support_weight,
        "utilisation_vol": ((p_L * p_W * p_H * final_palettes) / (cont_L * cont_W * cont_H)) * 100 if cont_L > 0 else 0
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
    st.markdown("""<style>.back-btn-container { padding: 10px 0px; border-bottom: 1px solid #eee; margin-bottom: 15px; }</style>""", unsafe_allow_html=True)
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
        total_p_weight = (w_box * b_per_p) + w_pal
        st.markdown(f"**Poids Brut / Palette :** `{total_p_weight} kg`")

# ==========================================
# 5. INTERFACE PRINCIPALE
# ==========================================
header_code = """<div style="padding: 20px; background: #0a0a0a; border-left: 10px solid #e67e22; border-radius: 10px; color: white; font-family: 'Orbitron', sans-serif;">
<h1 style="margin:0;">Container Optimizer <span style="color:#e67e22;">Pro</span></h1>
<p style="color:#e67e22; font-size:0.8rem; letter-spacing:2px;">MIXED LOADING ALGORITHM ACTIVE</p></div>"""
st.markdown(header_code, unsafe_allow_html=True)

col_cfg, col_main = st.columns([1, 2.2], gap="large")

with col_cfg:
    st.subheader("🏗️ Type de Conteneur")
    c_choice = st.selectbox("Choisir l'équipement :", list(CONTAINER_TYPES.keys()))
    c_specs = CONTAINER_TYPES[c_choice] if c_choice != "Personnaliser..." else {"L": 1200, "W": 235, "H": 240, "MaxPayload": 28000, "Vol": 67}
    cont_L, cont_W, cont_H, max_payload = c_specs['L'], c_specs['W'], c_specs['H'], c_specs['MaxPayload']
    calc_mode = st.radio("Mode d'analyse :", ["Plein potentiel", "Quantité spécifique"])

res = professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, w_box, w_pal, b_per_p, max_payload)

with col_main:
    display_pals = res['total_palettes'] if calc_mode == "Plein potentiel" else st.number_input("Box à charger", 500)//b_per_p
    m1, m2, m3 = st.columns(3)
    for col, (lab, val) in zip([m1, m2, m3], [("Box", display_pals*b_per_p), ("Palettes", display_pals), ("Conteneurs", 1)]):
        col.markdown(f'<div class="metric-container"><p class="metric-label">{lab}</p><p class="metric-value">{val}</p></div>', unsafe_allow_html=True)
    st.progress(min(res['utilisation_vol']/100, 1.0))

# ==========================================
# 6. PLAN DE CHARGEMENT VISUEL AVEC DISTINCTION
# ==========================================
st.subheader("📐 Plan de chargement (Vue de dessus réelle)")



cells_html = ""
# Palettes Standard
for _ in range(int(res['palettes_main'])):
    cells_html += f"""<div style="width: 80px; height: 110px; background: #e67e22; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; border-radius: 3px; margin: 4px; font-size: 12px; flex-shrink: 0;">x{res['niveaux']}</div>"""

# Palettes Tournées (Indicateur visuel spécial)
for _ in range(int(res['palettes_rotated'])):
    cells_html += f"""<div style="width: 110px; height: 80px; background: #2c3e50; border: 2px solid #e67e22; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; font-weight: bold; border-radius: 3px; margin: 4px; font-size: 10px; flex-shrink: 0;">
        <span style="font-size: 14px;">🔄</span>
        <span>x{res['niveaux']}</span>
    </div>"""

st.markdown(f"""
<div style="background: #ecf0f1; padding: 20px; border-radius: 12px; border: 2px solid #bdc3c7;">
    <div style="background: #2c3e50; padding: 20px; border-radius: 5px; min-height: 250px; display: flex; flex-wrap: wrap; align-content: flex-start; justify-content: flex-start; box-shadow: inset 0 0 50px rgba(0,0,0,0.5);">
        {cells_html if res['palettes_sol'] > 0 else '<div style="color:white;">Aucun chargement possible</div>'}
    </div>
    <div style="width: 100%; height: 15px; background: repeating-linear-gradient(45deg, #e67e22, #e67e22 10px, #333 10px, #333 20px); margin-top: 10px; border-radius: 4px;"></div>
    <div style="display: flex; gap: 20px; margin-top: 10px;">
        <div style="display: flex; align-items: center; font-size: 0.8rem;"><div style="width: 15px; height: 15px; background: #e67e22; margin-right: 5px;"></div> Sens Standard</div>
        <div style="display: flex; align-items: center; font-size: 0.8rem;"><div style="width: 15px; height: 15px; background: #2c3e50; border: 1px solid #e67e22; margin-right: 5px;"></div> Optimisation (Tournée)</div>
    </div>
</div>
""", unsafe_allow_html=True)
