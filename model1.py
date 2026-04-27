import numpy as np
import joblib
import os
import pywt
import pandas as pd
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.multioutput import MultiOutputRegressor

# --- 1. FEATURE EXTRACTION (LEVEL 11) ---
def extract_wavelet_features_l11(signal, wavelet='db4', level=11):
    """
    Decomposes signal at Level 11.
    Returns exactly 13 features.
    If wavelet gives <13 → add RMS.
    If wavelet gives 13 → return as is.
    """

    sig_arr = np.array(signal)

    # Wavelet decomposition
    coeffs = pywt.wavedec(sig_arr, wavelet, level=level, mode='periodization')

    # Mean absolute energy of each coefficient
    features = [np.mean(np.abs(c)) for c in coeffs]

    # If features < 13 add RMS
    if len(features) < 13:
        rms = np.sqrt(np.mean(sig_arr ** 2))
        features.append(rms)

    # If features > 13 trim extra values
    if len(features) > 13:
        features = features[:13]

    return features

# --- 2. MODEL TRAINING ENGINE ---
def train_engine(X, target_gains, target_shifts, model_type='xgboost'):
    X = np.array(X)
    target_gains = np.array(target_gains)
    target_shifts = np.array(target_shifts)

    # Model configuration optimized for 78 samples
    if model_type == 'linear':
        base_model = LinearRegression()
    elif model_type == 'rf':
        base_model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    elif model_type == 'gpr':
        kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
        base_model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=1e-2, random_state=42)
    else:
        # XGBoost with regularization to prevent overfitting on small data
        base_model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.03, 
                                   reg_lambda=1.5, reg_alpha=0.5,
                                   objective="reg:squarederror", random_state=42)

    # MultiOutputRegressor handles the 13-point target arrays
    gain_model = MultiOutputRegressor(base_model)
    shift_model = MultiOutputRegressor(base_model)

    print(f"🧠 Training {model_type.upper()} with {X.shape[0]} samples...")
    gain_model.fit(X, target_gains)
    shift_model.fit(X, target_shifts)

    # Save models
    os.makedirs("tool/models", exist_ok=True)
    joblib.dump(gain_model, f"tool/models/gain_{model_type}.pkl")
    joblib.dump(shift_model, f"tool/models/shift_{model_type}.pkl")
    print(f"✅ {model_type} models saved to tool/models/")

# --- 3. DATA PROCESSING & EXECUTION ---
if __name__ == "__main__":
    train_list = [
        'tool/data/opamp_square.csv', 
        'tool/data/opamp_sin.csv', 
        'tool/data/Opamp_sin_1MHz_2MHz_combined.csv'
    ]
    pg_excel_path = 'tool/data/new_p&g.xlsx'

    # Load Target Y data (13 indices)
    pg_df = pd.read_excel(pg_excel_path, sheet_name='4096')
    indices = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    gains = pg_df.loc[indices, 'avg_gain'].values
    shifts = pg_df.loc[indices, 'avg_shift'].values

    X_train, Y_gain_train, Y_shift_train = [], [], []

    # Map each X-dataset (3 files) into 13 segments each
    for file in train_list:
        if not os.path.exists(file):
            print(f"⚠️ Skipping missing file: {file}")
            continue
            
        df = pd.read_csv(file)
        col = '/vinp (V)' if '/vinp (V)' in df.columns else 'vinp'
        full_signal = df[col].values
        
        # Split full signal into 13 segments to match 13 targets
        segments = np.array_split(full_signal, 13)
        
        for i in range(13):
            # Extract Level 11 features (13 total)
            features = extract_wavelet_features_l11(segments[i], level=11)
            print(features)
            X_train.append(features)
            
            # Append the 13-point target arrays
            Y_gain_train.append(gains)
            Y_shift_train.append(shifts)

    # Final training execution
    X_train = np.array(X_train)
    Y_gain_train = np.array(Y_gain_train)
    Y_shift_train = np.array(Y_shift_train)

    for m_type in ['xgboost', 'linear', 'rf', 'gpr']:
        train_engine(X_train, Y_gain_train, Y_shift_train, model_type=m_type)

    print("\n🚀 SUCCESS: All models trained with Level 11 Wavelet Features (78 samples).")