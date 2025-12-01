import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------- CONFIG ----------
FILE1 = "MA2N_fixed.csv"
FILE2 = "MA2R_fixed.csv"

# ---------- LOAD DATA ----------
def load_and_prepare(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    rpm_col = next((col for col in df.columns if col.lower() == 'rpm'), None)
    ct_col = next((col for col in df.columns if col.lower() == 'ct'), None)
    cp_col = next((col for col in df.columns if col.lower() == 'cp'), None)

    if not all([rpm_col, ct_col, cp_col]):
        raise ValueError(f"File {file} must contain 'RPM', 'CT', and 'CP' columns.")

    return df[rpm_col], df[ct_col], df[cp_col]

rpm1, ct1, cp1 = load_and_prepare(FILE1)
rpm2, ct2, cp2 = load_and_prepare(FILE2)

# ---------- PLOTTING ----------
plt.figure(figsize=(12, 5))

# Thrust Coefficient
plt.subplot(1, 2, 1)
plt.plot(rpm2, ct2, 'o-', label="Comparison")
plt.plot(rpm1, ct1, 's-', label="Target")
plt.xlabel("Ω (RPM)")
plt.ylabel(r"$C_T$")
plt.title("GWS Direct Drive 3×2\nStatic Case")
plt.xlim(1500, 7500)
plt.ylim(0.00, 0.15)
plt.grid(True)
plt.legend()

# Power Coefficient
plt.subplot(1, 2, 2)
plt.plot(rpm2, cp2, 'o-', label="Comparison")
plt.plot(rpm1, cp1, 's-', label="Target")
plt.xlabel("Ω (RPM)")
plt.ylabel(r"$C_P$")
plt.title("GWS Direct Drive 3×2\nStatic Case")
plt.xlim(1500, 7500)
plt.ylim(0.0, 0.10)
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()