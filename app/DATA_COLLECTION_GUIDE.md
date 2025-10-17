# MESC Motor Controller - Data Collection Guide

## Quick Start

### Step-by-Step Data Collection

1. **Launch GUI**: `./run_gui.sh` or `python mesc_controller_gui.py`

2. **Connect**:
   - Select serial port from dropdown
   - Click "Connect"

3. **Start Data Collection**:
   - Click "Start Collection" button (turns orange)
   - Watch real-time plot of phase currents

4. **Control Motor** (optional):
   - Use slider to apply current
   - Watch how currents respond in real-time

5. **Stop Collection**:
   - Click "Stop Collection" button
   - Note sample count displayed

6. **Export Data**:
   - Click "Export CSV"
   - Choose filename and save location
   - Data is saved with timestamp

## What Gets Collected

The GUI automatically logs the following at 100Hz (10ms intervals):

| Variable | Description | Units |
|----------|-------------|-------|
| timestamp | Time since collection started | seconds |
| Vbus | Bus voltage | Volts |
| Iu_avg | Phase U current (averaged) | Amps |
| Iv_avg | Phase V current (averaged) | Amps |
| Iw_avg | Phase W current (averaged) | Amps |
| Vd | D-axis voltage | Volts |
| Vq | Q-axis voltage | Volts |
| angle | Rotor electrical angle | 0-65535 |

## Understanding the Data

### Phase Currents (Iu, Iv, Iw)

These are the instantaneous currents in each of the three motor phases:
- In a balanced 3-phase system: `Iu + Iv + Iw ≈ 0`
- For DC motors or unbalanced loads, this may not hold
- These values are **averaged** using an IIR filter for smoothness

### D-Q Axis Voltages (Vd, Vq)

Field-Oriented Control (FOC) uses rotating reference frame:
- **Vd**: Controls magnetic flux (usually kept near zero)
- **Vq**: Controls torque (proportional to motor torque)

### Rotor Angle

- Ranges from 0 to 65535 (16-bit unsigned)
- Maps to 0° to 360° electrical degrees
- To convert: `degrees = (angle / 65536) × 360`

## Data Collection Tips

### Optimal Collection Duration

- **Transient events**: 1-5 seconds
- **Steady-state operation**: 10-30 seconds
- **Long-term monitoring**: Use shorter intervals, export periodically

### Buffer Size

- Default: 1000 samples
- At 100Hz: 10 seconds of data
- Older samples are automatically discarded when buffer is full

### When to Collect Data

**Good scenarios for data collection:**
- Motor acceleration/deceleration
- Step response testing
- Efficiency analysis
- Fault detection
- Tuning control loops

**What to look for:**
- Current ripple (high-frequency oscillations)
- Phase balance (Iu ≈ Iv ≈ Iw in magnitude)
- Response to step commands
- Unexpected spikes or dropouts

## Analyzing Exported Data

### CSV File Format

```csv
timestamp,Vbus,Iu,Iv,Iw,Vd,Vq,angle
0.000000,48.5,0.12,0.15,-0.27,1.2,5.4,12345
0.010000,48.5,0.13,0.14,-0.27,1.3,5.5,12456
0.020000,48.6,0.14,0.15,-0.29,1.2,5.6,12567
...
```

### Example Analysis Tasks

#### 1. Calculate RMS Current

**Python:**
```python
import pandas as pd
import numpy as np

data = pd.read_csv('mesc_data.csv')
iu_rms = np.sqrt(np.mean(data['Iu']**2))
print(f"Iu RMS: {iu_rms:.3f} A")
```

#### 2. FFT Analysis (Find Current Harmonics)

**Python:**
```python
import numpy as np
import matplotlib.pyplot as plt

# Perform FFT on Iu
fft = np.fft.fft(data['Iu'])
freq = np.fft.fftfreq(len(data), d=0.01)  # 10ms sampling

# Plot frequency spectrum
plt.figure()
plt.plot(freq[:len(freq)//2], np.abs(fft[:len(fft)//2]))
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.title('Current Frequency Spectrum')
plt.grid(True)
plt.show()
```

#### 3. Calculate Power

**Python:**
```python
# Approximate power (simplified, ignores power factor)
power = data['Vbus'] * (np.abs(data['Iu']) + np.abs(data['Iv']) + np.abs(data['Iw'])) / 3
avg_power = power.mean()
print(f"Average Power: {avg_power:.1f} W")
```

#### 4. Detect Phase Imbalance

**Python:**
```python
iu_rms = np.sqrt(np.mean(data['Iu']**2))
iv_rms = np.sqrt(np.mean(data['Iv']**2))
iw_rms = np.sqrt(np.mean(data['Iw']**2))

max_imbalance = max(abs(iu_rms - iv_rms), abs(iv_rms - iw_rms), abs(iw_rms - iu_rms))
avg_current = (iu_rms + iv_rms + iw_rms) / 3

imbalance_percent = (max_imbalance / avg_current) * 100
print(f"Phase Imbalance: {imbalance_percent:.1f}%")
```

## Advanced: Understanding the MESC Logging System

### How It Works

When you click "Start Collection", the GUI sends these commands:

```
log -r              # Reset/clear logging
log -a vbus         # Add bus voltage to log
log -a Iu_avg       # Add phase U current
log -a Iv_avg       # Add phase V current
log -a Iw_avg       # Add phase W current
log -s 10           # Set log interval to 10ms
```

The MESC controller then streams JSON data over serial:

```json
{"vbus": 48.5, "Iu_avg": 0.12, "Iv_avg": 0.15, "Iw_avg": -0.27}
```

The GUI parses this JSON and:
1. Adds timestamp
2. Stores in circular buffer
3. Updates plot every 100ms
4. Allows export to CSV

### Customizing Logging

You can manually add other variables via the terminal:

```
log -a id           # D-axis current
log -a iq           # Q-axis current
log -a ehz          # Electrical frequency
log -a TMOS         # MOSFET temperature
log -a TMOT         # Motor temperature
log -s 5            # Change to 5ms logging (200Hz)
```

See MESC CLI documentation for full list of loggable variables.

## Troubleshooting

### No Data Appearing

1. **Check connection**: Is serial port connected?
2. **Check firmware**: Does your MESC support the `log` command?
3. **Check terminal**: Do you see JSON output when logging starts?

### Plot Not Updating

1. **Matplotlib installed?**: `pip install matplotlib`
2. **Check samples label**: Is sample count increasing?
3. **Check terminal**: Look for error messages

### Garbled Data

1. **Baud rate**: Ensure correct baud rate selected (usually 115200)
2. **Cable quality**: Try different USB cable
3. **Buffer overflow**: Stop other programs using the serial port

### Export Fails

1. **No data**: Ensure collection has run and samples > 0
2. **File permissions**: Check you have write access to save location
3. **Disk space**: Ensure sufficient disk space

## Best Practices

1. **Clear before each test**: Click "Clear Data" to start fresh
2. **Label your exports**: Use descriptive filenames with date/time
3. **Document test conditions**: Note current setting, load, etc.
4. **Multiple runs**: Collect data from several runs for repeatability
5. **Check phase currents sum to zero**: Verify Iu + Iv + Iw ≈ 0

## Safety Reminders

- Always use the Emergency Stop if motor behaves unexpectedly
- Data collection does not affect motor control performance
- Motor continues running during data collection
- Emergency Stop immediately stops motor AND data collection

---

For more information, see:
- [README_GUI.md](README_GUI.md) - GUI usage guide
- MESC Serial CLI Commands Reference - Complete command documentation
- MESC Debug and Buffer System - Advanced data collection techniques
