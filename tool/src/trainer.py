import numpy as np
import joblib
import os
import pywt
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.multioutput import MultiOutputRegressor
from scipy.stats import kurtosis, skew

def extract_features(signal, vdda=3.6):
    
    sig_arr = np.array(signal)
    rms = np.sqrt(np.mean(sig_arr**2))
    zcr = ((sig_arr[:-1] * sig_arr[1:]) < 0).sum() / len(sig_arr)
    normalized_peak = np.max(np.abs(sig_arr)) / vdda
    
    return [rms , zcr, normalized_peak]

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

def train_engine(X, target_gains, target_shifts, model_type='xgboost'):
    X = np.array(X)
    target_gains = np.array(target_gains)
    target_shifts = np.array(target_shifts)

    # Model Selection Logic
    if model_type == 'linear':
        base_model = LinearRegression()
    elif model_type == 'rf':
        base_model = RandomForestRegressor(n_estimators=100, random_state=42)
    elif model_type == 'gpr':
        # GPR with a standard RBF kernel
        kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        base_model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=9, random_state=42)
    else:
        base_model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, 
                                  objective="reg:squarederror", random_state=42)

    gain_model = MultiOutputRegressor(base_model)
    shift_model = MultiOutputRegressor(base_model)

    print(f"🧠 Training {model_type.upper()}...")
    gain_model.fit(X, target_gains)
    shift_model.fit(X, target_shifts)

    os.makedirs("tool/models", exist_ok=True)
    joblib.dump(gain_model, f"tool/models/gain_{model_type}.pkl")
    joblib.dump(shift_model, f"tool/models/shift_{model_type}.pkl")
    print(f"✅ {model_type} models saved.")