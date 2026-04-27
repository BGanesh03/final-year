import numpy as np
import pywt
import pandas as pd
def get_wavelet_levels(signal, wavelet='db4', level=11):
    """Decomposes signal into a list of coefficient levels."""
    data = pywt.wavedec(signal, wavelet, level=level, mode='periodization')
    # print(data)
    return data

def reconstruct_optimized(coeffs_list, shifts, wavelet='db4'):
    temp_recon = pywt.waverec(coeffs_list, wavelet, mode='periodization')
    actual_len = len(temp_recon)
    # print(actual_len)
    final_signal = np.zeros(actual_len)
    for i in range(len(coeffs_list)):
        temp_coeffs = [np.zeros_like(c) for c in coeffs_list]
        temp_coeffs[i] = coeffs_list[i]
        level_signal = pywt.waverec(temp_coeffs, wavelet, mode='periodization')
        shift_val = int(shifts[i]) % actual_len
        shifted_level = np.roll(level_signal, -shift_val)
        final_signal += shifted_level
    return final_signal