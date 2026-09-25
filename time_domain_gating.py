import numpy as np
import matplotlib.pyplot as plt
import os

# Create directory if it doesn't exist yet to prevent save errors
os.makedirs('plots', exist_ok=True)

# 1. Base Setup (X/Ku Band Array)
N = 512
freqs = np.linspace(8e9, 18e9, N)
df = freqs[1] - freqs[0]

# Time/Distance spacing from IFFT parameters
time_vector = np.fft.fftfreq(N, d=df)
# Keep only positive time delays for intuitive visualization
pos_idx = time_vector >= 0
t_plot = time_vector[pos_idx] * 1e9  # Convert to nanoseconds

# 2. Simulate the Material Response + Room Clutter
# Let's say our true material resonance is a clean Gaussian dip in reflection
true_material_s11 = -10 - 20 * np.exp(-((freqs - 12e9) / 1e9)**2)
# Convert dB back to linear complex vector for math
s11_linear = 10**(true_material_s11 / 20) * np.exp(1j * 0) 

# Add Room Clutter: A reflection off a back wall 3 nanoseconds away
clutter_delay = 3.0e-9
clutter = 0.08 * np.exp(-1j * 2 * np.pi * freqs * clutter_delay)
s11_corrupted = s11_linear + clutter

# 3. Time-Domain Conversion (The IFFT step)
time_domain_raw = np.fft.ifft(s11_corrupted)

# 4. FIXED GATE: Build the explicit brick-wall mask windows
gate_window = np.zeros(N)
gate_limit_idx = np.where(t_plot > 2.2)[0][0]

# Front gate passes everything from 0 up to 2.2ns
gate_window[0:gate_limit_idx] = 1.0  
# Mirror gate handles the negative-frequency conjugate spectrum for the FFT loop
gate_window[-gate_limit_idx:] = 1.0 

# Apply the gate to slice out the clutter spike at 3ns
time_domain_gated = time_domain_raw * gate_window

# 5. Transform Back to Frequency Space (The FFT return)
s11_gated_linear = np.fft.fft(time_domain_gated)
s11_gated_db = 20 * np.log10(np.abs(s11_gated_linear))

# ==========================================================
# VISUAL RENDERING: SPLIT AND EXPORT INDEPENDENT IMAGES
# ==========================================================

# --- PLOT 1: TIME DOMAIN PROFILE ---
plt.figure(figsize=(7, 5))
plt.plot(t_plot, np.abs(time_domain_raw)[pos_idx], label='Raw Echoes (Sample + Wall)', color='crimson', lw=2)
plt.plot(t_plot, gate_window[pos_idx] * np.max(np.abs(time_domain_raw)), '--', label='Gate Window', color='green')
plt.title('VNA Time-Domain Profile (IFFT)')
plt.xlabel('Time Delay (nanoseconds)')
plt.ylabel('Linear Echo Amplitude')
plt.xlim([0, 6])
plt.grid(True, linestyle='--')
plt.legend()
plt.tight_layout()
plt.savefig('plots/gating_time.png', dpi=300)
plt.close()

# --- PLOT 2: CLEANED FREQUENCY SWEEP ---
plt.figure(figsize=(7, 5))
plt.plot(freqs / 1e9, 20*np.log10(np.abs(s11_corrupted)), label='Corrupted VNA Data (with ripple)', color='crimson', alpha=0.4)
plt.plot(freqs / 1e9, s11_gated_db, label='Gated Material Data', color='dodgerblue', lw=2.5)
plt.title('Frequency Sweep Clutter Filtering')
plt.xlabel('Frequency (GHz)')
plt.ylabel('Magnitude (dB)')
plt.ylim([-35, 0])
plt.grid(True, linestyle='--')
plt.legend()
plt.tight_layout()
plt.savefig('plots/gating_frequency.png', dpi=300)
plt.show()  # Display the smooth curve verification window
