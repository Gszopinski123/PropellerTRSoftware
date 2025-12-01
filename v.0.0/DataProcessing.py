import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ---------- CONFIG ----------
INPUT_FILE = "combined_data_log_4.csv"
COMPARISON_FILE = "AIR2A.csv"
OUTPUT_FILE_BASE = "temp"
PROPELLER_DIAMETER = 0.185  # meters
# APC0838 - 0.21
# MA2 - 0.195
# AIR2 - 0.185

# ---------- FIND UNIQUE OUTPUT FILE ----------
output_index = 0
while True:
    output_file = f"{OUTPUT_FILE_BASE}_{output_index}.csv" if output_index else f"{OUTPUT_FILE_BASE}.csv"
    if not os.path.exists(output_file):
        break
    output_index += 1

# ---------- LOAD AND PROCESS INPUT ----------
data = pd.read_csv(INPUT_FILE)

# Ensure proper numeric types before filtering
numeric_cols = ['Mech_RPM', 'Opt_RPM', 'Thrust (N)', 'Torque (Nm)']
for col in numeric_cols:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# Invert torque if mostly negative
if data['Torque (Nm)'].dropna().lt(0).mean() > 0.5:
    data['Torque (Nm)'] = -data['Torque (Nm)']

# Filter out invalid rows
data = data[(data['Mech_RPM'] > 0) & (data['Opt_RPM'] > 0) & (data['Thrust (N)'] > 0) & (data['Torque (Nm)'] > 0)]

rpm_choice = input("Use Mechanical RPM, Optical RPM, or Both? (mech/opt/both): ").strip().lower()
if rpm_choice == 'mech':
    data['RPM'] = data['Mech_RPM']
elif rpm_choice == 'opt':
    data['RPM'] = data['Opt_RPM']
else:
    data['RPM'] = (data['Mech_RPM'] + data['Opt_RPM']) / 2

data['n (rps)'] = data['RPM'] / 60
data['Power (W)'] = 2 * np.pi * data['n (rps)'] * data['Torque (Nm)']
data['ESC_Power (W)'] = data['ESC_Current'] * data['Power_Voltage']
data['Air_Density'] = pd.to_numeric(data['Air_Density'], errors='coerce')

data['CT'] = data['Thrust (N)'] / (data['Air_Density'] * (data['n (rps)']**2) * PROPELLER_DIAMETER**4)
data['CP'] = data['Power (W)'] / (data['Air_Density'] * (data['n (rps)']**3) * PROPELLER_DIAMETER**5)

# ---------- SAVE RESULTS ----------
result_data = data[['PWM', 'RPM', 'CT', 'CP']]
result_data.to_csv(output_file, index=False)
print(f"Calculation complete. Results saved to {output_file}")

# ---------- PLOTTING ----------
compare = input("Would you like to include comparison data? (y/n): ").strip().lower() == 'y'
plt.figure(figsize=(12, 5))

if compare:
    ref = pd.read_csv(COMPARISON_FILE)
    ref.columns = ref.columns.str.strip()  # Strip extra spaces just in case
    rpm_col = next((col for col in ref.columns if col.lower() == 'rpm'), None)
    ct_col = next((col for col in ref.columns if col.lower() == 'ct'), None)
    cp_col = next((col for col in ref.columns if col.lower() == 'cp'), None)

# Thrust Coefficient
plt.subplot(1, 2, 1)
if compare and rpm_col and ct_col:
    plt.plot(ref[rpm_col], ref[ct_col], 'o-', label="Comparison")
plt.plot(data['RPM'], data['CT'], 's-', label="Target")
plt.xlabel("Ω (RPM)")
plt.ylabel(r"$C_T$")
plt.title("GWS Direct Drive 3×2\nStatic Case")
plt.xlim(0, 30000)
plt.ylim(0.05, 0.17)
plt.grid(True)
plt.legend()

# Power Coefficient
plt.subplot(1, 2, 2)
if compare and rpm_col and cp_col:
    plt.plot(ref[rpm_col], ref[cp_col], 'o-', label="Comparison")
plt.plot(data['RPM'], data['CP'], 's-', label="Target")
plt.xlabel("Ω (RPM)")
plt.ylabel(r"$C_P$")
plt.title("GWS Direct Drive 3×2\nStatic Case")
plt.xlim(0, 30000)
plt.ylim(0.0, 0.11)
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()
