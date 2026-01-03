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
# 3. ALGORITHME DE CALCUL PROFESSIONNEL (OPTIMISÉ MIXTE)
# ==========================================
def professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, box_unit_weight, pallet_support_weight, b_per_p, max_load):
    if cont_L <= 0 or cont_W <= 0 or cont_H <= 0:
        return {"palettes_sol": 0, "niveaux": 0, "total_palettes": 0, "poids_total_brut": 0, "utilisation_vol": 0}
        
    p_total_weight = (b_per_p * box_unit_weight) + pallet_support_weight
    stack_levels = int(cont_H / p_H) if p_H > 0 else 1

    # --- LOGIQUE DE REMPLISSAGE MIXTE ---
    # Scénario 1 : Tout en Longueur
    n1 = int(cont_L / p_L) * int(cont_W / p_W)
    # Scénario 2 : Tout en Largeur
    n2 = int(cont_L / p_W) * int(cont_W / p_L)
    # Scénario 3 : Mixte (Vertical + Horizontal au fond)
    p_long = max(p_L, p_W)
    p_short = min(p_L, p_W)
    
    rows = int(cont_L / p_long)
    rest_L = cont_L - (rows * p_long)
    n3 = (rows * int(cont_W / p_short)) 
    if rest_L >= p_short:
        n3 += int(cont_W / p_long)

    best_sol_sol = max(n1, n2, n3)
    
    theoretical_total = best_sol_sol * stack_levels
    if p_total_weight > 0 and max_load > 0:
        final_palettes = min(theoretical_total, int(max_load / p_total_weight))
    else:
        final_palettes = theoretical_total
        
    vol_pal = (p_L * p_W * p_H) * final_palettes
    vol_cont = cont_L * cont_W * cont_H
    utilization = (vol_pal / vol_cont) * 100 if vol_cont > 0 else 0
    
    return {
        "palettes_sol": best_sol_sol,
        "niveaux": stack_levels,
        "total_palettes": final_palettes,
        "poids_total_brut": final_palettes * p_total_weight,
        "poids_total_box": final_palettes * (b_per_p * box_unit_weight),
        "poids_total_supports": final_palettes * pallet_support_weight,
        "utilisation_vol": utilization
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
        st.markdown('<p style="font-size: 0.85rem; font-weight: 600; color: #e67e22;">Saisie des poids unitaires :</p>', unsafe_allow_html=True)
        w_box = st.number_input("Poids d'une seule Box (kg)", value=12.5)
        st.markdown(f'<p class="weight-info">Soit {w_box * b_per_p} kg de box par palette</p>', unsafe_allow_html=True)
        w_pal = st.number_input("Poids de la Palette support (kg)", value=25.0)
        st.markdown('<p class="weight-info">Poids du support bois/plastique seul</p>', unsafe_allow_html=True)
        st.markdown("---")
        total_p_weight = (w_box * b_per_p) + w_pal
        st.markdown(f"**Poids Brut / Palette :** `{total_p_weight} kg`")

# ==========================================
# 5. INTERFACE PRINCIPALE
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

col_cfg, col_main = st.columns([1, 2.2], gap="large")

with col_cfg:
    st.subheader("🏗️ Type de Conteneur")
    c_choice = st.selectbox("Choisir l'équipement :", list(CONTAINER_TYPES.keys()))
    
    if c_choice == "Personnaliser...":
        cont_L = st.number_input("Longueur Int. (cm)", value=1200.0)
        cont_W = st.number_input("Largeur Int. (cm)", value=235.0)
        cont_H = st.number_input("Hauteur Int. (cm)", value=240.0)
        max_payload = st.number_input("Charge Utile Max (kg)", value=28000.0)
        c_specs = {"L": cont_L, "W": cont_W, "H": cont_H, "MaxPayload": max_payload, "Vol": round((cont_L*cont_W*cont_H)/1000000, 2)}
    else:
        c_specs = CONTAINER_TYPES[c_choice]
        cont_L, cont_W, cont_H, max_payload = c_specs['L'], c_specs['W'], c_specs['H'], c_specs['MaxPayload']
    
    st.markdown(f"""<div class="status-box"><b>Spécifications :</b><br>• Longueur : {cont_L} cm<br>• Charge : {max_payload} kg<br>• Volume : {c_specs['Vol']} m³</div>""", unsafe_allow_html=True)
    calc_mode = st.radio("Mode d'analyse :", ["Plein potentiel", "Quantité spécifique"])

res = professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, w_box, w_pal, b_per_p, max_payload)

with col_main:
    if calc_mode == "Quantité spécifique":
        target_box = st.number_input("Nombre de Box à charger :", value=500, step=50)
        display_pals = math.ceil(target_box / b_per_p)
        display_box, display_cont = target_box, math.ceil(display_pals / (res['total_palettes'] if res['total_palettes']>0 else 1))
    else:
        display_pals, display_box, display_cont = res['total_palettes'], res['total_palettes'] * b_per_p, 1.0

    m1, m2, m3 = st.columns(3)
    metrics = [("Total Box", display_box), ("Total Palettes", display_pals), ("Conteneurs", display_cont)]
    for col, (lab, val) in zip([m1, m2, m3], metrics):
        col.markdown(f'<div class="metric-container"><p class="metric-label">{lab}</p><p class="metric-value">{val}</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Répartition de la Charge Utile")
    total_boxes_w, total_supports_w, total_load_brut = res['poids_total_box'], res['poids_total_supports'], res['poids_total_brut']
    if total_load_brut > 0:
        st.markdown(f"""
            <div style="width: 100%; background-color: #eee; border-radius: 10px; height: 30px; display: flex; overflow: hidden; margin-top: 15px; border: 1px solid #ddd;">
                <div style="width: {(total_boxes_w/total_load_brut)*100}%; background: #e67e22; height: 100%;"></div>
                <div style="width: {(total_supports_w/total_load_brut)*100}%; background: #2c3e50; height: 100%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.85rem;">
                <span>📦 Poids Box : <b>{total_boxes_w:,.1f} kg</b></span>
                <span>🏗️ Poids Supports : <b>{total_supports_w:,.1f} kg</b></span>
            </div>
        """, unsafe_allow_html=True)

    st.write(f"**Taux d'utilisation volumétrique : {res['utilisation_vol']:.1f}%**")
    st.progress(min(res['utilisation_vol']/100, 1.0))
    
    df_res = pd.DataFrame({"Item": ["Palettes total", "Poids Brut (kg)", "Niveaux"], "Valeur": [display_pals, res['poids_total_brut'], res['niveaux']]})
    st.download_button("📥 TÉLÉCHARGER LE RAPPORT (EXCEL)", get_excel_binary(df_res, pd.DataFrame([c_specs])), "Export_Logistics.xlsx")

# ==========================================
# 6. PLAN DE CHARGEMENT RÉALISTE (MIXTE)
# ==========================================
st.subheader("📐 Plan de chargement (Vue de dessus optimisée)")



palettes_sol = res['palettes_sol']
niveaux = res['niveaux']

# Logique visuelle : Détermine si on affiche les palettes en portrait ou paysage
if p_L >= p_W:
    w_px, h_px, label_dim = "85px", "115px", f"{p_W}x{p_L}"
else:
    w_px, h_px, label_dim = "115px", "85px", f"{p_L}x{p_W}"

cells_html = ""
for i in range(int(palettes_sol)):
    cells_html += f"""
    <div style="width: {w_px}; height: {h_px}; background: #e67e22; border: 2px solid #ffffff; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; font-family: 'Poppins', sans-serif; border-radius: 3px; box-shadow: 3px 3px 5px rgba(0,0,0,0.3); flex-shrink: 0; margin: 5px;">
        <div style="font-size: 8px; opacity: 0.9;">{label_dim}</div>
        <div style="font-size: 13px; font-weight: bold;">x{niveaux}</div>
        <div style="width: 70%; height: 1.5px; background: rgba(255,255,255,0.4); margin-top: 4px;"></div>
    </div>"""

st.markdown(f"""
<div style="background: #ecf0f1; padding: 20px; border-radius: 12px; border: 2px solid #bdc3c7;">
    <div style="background: #2c3e50; padding: 20px; border-radius: 5px; border-left: 15px solid #34495e; border-right: 15px solid #34495e; min-height: 280px; display: flex; flex-wrap: wrap; align-content: flex-start; justify-content: center; box-shadow: inset 0 0 50px rgba(0,0,0,0.6);">
        {cells_html if palettes_sol > 0 else '<div style="color:white; padding:40px;">⚠️ Espace insuffisant pour ces dimensions</div>'}
    </div>
    <div style="width: 100%; height: 20px; background: repeating-linear-gradient(45deg, #e67e22, #e67e22 10px, #d35400 10px, #d35400 20px); margin-top: 15px; border-radius: 4px; display: flex; justify-content: center; align-items: center;">
        <span style="color: white; font-size: 11px; font-weight: bold; text-shadow: 1px 1px 2px black;">ZONE DE CHARGEMENT / SENS DES PORTES</span>
    </div>
</div>
""", unsafe_allow_html=True)
