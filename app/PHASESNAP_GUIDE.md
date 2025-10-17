# Phase Snapshot Data Collection Guide

## Overview

The MESC Motor Controller GUI now uses the `phasesnap` command to capture high-resolution current and voltage waveforms directly from the motor controller.

## How It Works

### Command: `phasesnap`

When you click "Start Collection" in the GUI, it sends the `phasesnap` command to your MESC controller.

The controller responds by:
1. Capturing 600 samples of phase currents and voltages
2. Sampling at PWM frequency (~20kHz = 50μs per sample)
3. Outputting the data as CSV in the terminal

### Sample Data Format

```
Ia, Ib, Ic, Va, Vb, Vc
0.076, 0.174, -0.074, 0.588, 0.634, 0.785
-0.004, 0.174, -0.074, 0.287, 0.226, 0.000
0.640, 0.658, 0.812, 0.483, 0.483, 0.468
...
(600 samples total)
```

Where:
- **Ia, Ib, Ic**: Phase A, B, C currents in Amperes
- **Va, Vb, Vc**: Phase A, B, C voltages in Volts

## Using the GUI

### Step-by-Step

1. **Connect to MESC**
   - Select serial port
   - Click "Connect"

2. **Optional: Apply Current**
   - Use slider to set motor current
   - Motor will be running during capture

3. **Capture Data**
   - Click "Start Collection"
   - Button changes to "Collecting..."
   - Wait ~1-2 seconds for capture and parsing
   - Button returns to "Start Collection" when done

4. **View Results**
   - Plot shows 600 samples over ~30ms
   - Three traces: Ia (blue), Ib (red), Ic (green)
   - Sample count displayed

5. **Export Data**
   - Click "Export CSV"
   - Choose location and filename
   - Opens in Excel, MATLAB, Python, etc.

6. **Repeat or Clear**
   - Click "Start Collection" again for new capture
   - Click "Clear Data" to reset plot

## Understanding the Data

### Time Resolution

- **Sample period**: 50 microseconds (20kHz)
- **Total duration**: 30 milliseconds (600 × 50μs)
- **Timestamp**: Calculated as `sample_index × 50μs`

### Current Values

The phase currents should satisfy Kirchhoff's Current Law:
```
Ia + Ib + Ic ≈ 0
```

If this doesn't hold, there may be:
- Measurement offset errors
- Ground loop issues
- ADC calibration problems

### Voltage Values

Phase voltages are measured relative to ground. In a 3-phase system:
- Peak voltage ≈ Vbus / √3
- Voltages shift with PWM modulation
- Zero voltage = low-side FET conducting

## Data Analysis Examples

### Python: Plot All Phases

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
data = pd.read_csv('mesc_data.csv')

# Plot currents
plt.figure(figsize=(12, 6))
plt.plot(data['timestamp_s'] * 1000, data['Ia'], 'b-', label='Ia', linewidth=0.8)
plt.plot(data['timestamp_s'] * 1000, data['Ib'], 'r-', label='Ib', linewidth=0.8)
plt.plot(data['timestamp_s'] * 1000, data['Ic'], 'g-', label='Ic', linewidth=0.8)
plt.xlabel('Time (ms)')
plt.ylabel('Current (A)')
plt.title('Phase Currents - 30ms Snapshot')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

### Python: Check Current Balance

```python
import numpy as np

# Calculate sum (should be near zero)
current_sum = data['Ia'] + data['Ib'] + data['Ic']
max_error = np.max(np.abs(current_sum))
avg_magnitude = np.mean(np.abs(data['Ia']) + np.abs(data['Ib']) + np.abs(data['Ic'])) / 3

print(f"Maximum current sum error: {max_error:.3f} A")
print(f"Error as % of average magnitude: {100*max_error/avg_magnitude:.2f}%")

if max_error < 0.1:
    print("✓ Current balance is good!")
else:
    print("⚠ Current balance issue detected")
```

### Python: Calculate RMS Current

```python
import numpy as np

ia_rms = np.sqrt(np.mean(data['Ia']**2))
ib_rms = np.sqrt(np.mean(data['Ib']**2))
ic_rms = np.sqrt(np.mean(data['Ic']**2))

print(f"Ia RMS: {ia_rms:.3f} A")
print(f"Ib RMS: {ib_rms:.3f} A")
print(f"Ic RMS: {ic_rms:.3f} A")
print(f"Average RMS: {(ia_rms + ib_rms + ic_rms)/3:.3f} A")
```

### Python: Find Peak Current

```python
import numpy as np

ia_peak = np.max(np.abs(data['Ia']))
ib_peak = np.max(np.abs(data['Ib']))
ic_peak = np.max(np.abs(data['Ic']))

print(f"Ia peak: {ia_peak:.3f} A")
print(f"Ib peak: {ib_peak:.3f} A")
print(f"Ic peak: {ic_peak:.3f} A")
print(f"Maximum peak: {max(ia_peak, ib_peak, ic_peak):.3f} A")
```

### Python: FFT Analysis (Find Switching Frequency)

```python
import numpy as np
import matplotlib.pyplot as plt

# Perform FFT
fft = np.fft.fft(data['Ia'])
freq = np.fft.fftfreq(len(data), d=50e-6)  # 50us sampling period

# Plot frequency spectrum up to 50kHz
mask = (freq > 0) & (freq < 50000)
plt.figure(figsize=(12, 6))
plt.plot(freq[mask]/1000, np.abs(fft[mask]))
plt.xlabel('Frequency (kHz)')
plt.ylabel('Magnitude')
plt.title('Current Frequency Spectrum')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Find PWM frequency (should be around 20kHz)
pwm_idx = np.argmax(np.abs(fft[mask]))
pwm_freq = freq[mask][pwm_idx]
print(f"Dominant frequency: {pwm_freq/1000:.1f} kHz")
```

### MATLAB: Load and Plot

```matlab
% Load data
data = readtable('mesc_data.csv');

% Plot currents
figure('Position', [100 100 1200 600]);
hold on;
plot(data.timestamp_s * 1000, data.Ia, 'b-', 'LineWidth', 0.8);
plot(data.timestamp_s * 1000, data.Ib, 'r-', 'LineWidth', 0.8);
plot(data.timestamp_s * 1000, data.Ic, 'g-', 'LineWidth', 0.8);
xlabel('Time (ms)');
ylabel('Current (A)');
title('Phase Currents - 30ms Snapshot');
legend('Ia', 'Ib', 'Ic');
grid on;
grid minor;
```

## Troubleshooting

### No Data Captured

**Symptoms**: Sample count stays at 0

**Possible causes**:
1. MESC not responding - check terminal for output
2. Serial connection issue - try reconnecting
3. Firmware doesn't support `phasesnap` - update firmware

**Solutions**:
- Check terminal window for "Capturing phase current..." message
- Manually type `phasesnap` in command field to test
- Verify firmware version supports snapshot

### Garbled Data

**Symptoms**: Plot shows random spikes or nonsense values

**Possible causes**:
1. Serial buffer overflow
2. ANSI escape codes not properly stripped
3. Baud rate mismatch

**Solutions**:
- Use 115200 baud (recommended)
- Close other programs using the serial port
- Try collecting again

### Current Sum Not Zero

**Symptoms**: Ia + Ib + Ic ≠ 0

**Possible causes**:
1. ADC offset calibration needed
2. Ground loop in wiring
3. Common-mode noise

**Solutions**:
- Run ADC calibration in MESC
- Check motor and controller grounding
- Use differential measurements if available

## Advanced Usage

### Capture Multiple Snapshots

To compare multiple captures:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load multiple files
data1 = pd.read_csv('snapshot_1A.csv')
data2 = pd.read_csv('snapshot_2A.csv')
data3 = pd.read_csv('snapshot_3A.csv')

# Plot overlaid
plt.figure(figsize=(12, 6))
plt.plot(data1['timestamp_s']*1000, data1['Ia'], 'b-', alpha=0.5, label='1A')
plt.plot(data2['timestamp_s']*1000, data2['Ia'], 'r-', alpha=0.5, label='2A')
plt.plot(data3['timestamp_s']*1000, data3['Ia'], 'g-', alpha=0.5, label='3A')
plt.xlabel('Time (ms)')
plt.ylabel('Phase A Current (A)')
plt.title('Current Scaling Test')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### Calculate Current Ripple

```python
import numpy as np

# Remove DC component
ia_ac = data['Ia'] - np.mean(data['Ia'])

# Calculate ripple (peak-to-peak)
ripple = np.max(ia_ac) - np.min(ia_ac)
ripple_rms = np.sqrt(np.mean(ia_ac**2))

print(f"Current ripple (pk-pk): {ripple:.3f} A")
print(f"Current ripple (RMS): {ripple_rms:.3f} A")
```

### Estimate Switching Losses

```python
import numpy as np

# Assuming 1mΩ FET resistance
r_fet = 0.001

# Calculate switching current (max rate of change)
di_dt = np.diff(data['Ia']) / 50e-6  # A/s
max_di_dt = np.max(np.abs(di_dt))

# Estimate conduction loss
i_rms = np.sqrt(np.mean(data['Ia']**2))
p_cond = i_rms**2 * r_fet

print(f"Max dI/dt: {max_di_dt/1e6:.1f} MA/s")
print(f"Conduction loss (approx): {p_cond:.3f} W per phase")
```

## Best Practices

1. **Before Capture**:
   - Ensure motor is in stable state
   - Check that current command is appropriate
   - Verify serial connection is solid

2. **During Capture**:
   - Don't disturb motor or controller
   - Avoid changing current during snapshot
   - Let capture complete (~1-2 seconds)

3. **After Capture**:
   - Verify sample count = 600
   - Check that plot looks reasonable
   - Export immediately if data is important

4. **Data Management**:
   - Use descriptive filenames (e.g., `motor_1A_no_load_20250114.csv`)
   - Include test conditions in filename
   - Keep backups of important captures

---

**For More Information**:
- MESC Serial CLI Commands Reference
- README_GUI.md - GUI usage guide
- DATA_COLLECTION_GUIDE.md - General data collection info
