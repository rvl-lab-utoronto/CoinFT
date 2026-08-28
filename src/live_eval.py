import os
import sys
import time
import json
import argparse
from collections import deque

import numpy as np
import h5py
import serial
import onnxruntime as ort
import matplotlib.pyplot as plt

import bota_driver

#########################
# 1. ARGUMENT PARSING   #
#########################
def parse_args():
    parser = argparse.ArgumentParser(
        description="Live comparison of CoinFT (converted via a trained model) "
                    "against the Bota reference sensor."
    )
    parser.add_argument(
        '--model_dir', type=str, required=True,
        help="Folder name inside ./trained_model/ containing "
             "{sensor_name}_MLP.onnx and {sensor_name}_norm.json."
    )
    parser.add_argument(
        '--sensor_name', type=str, default='CFT24',
        help="Sensor name, used to build model/norm filenames (default CFT24)."
    )
    parser.add_argument(
        '--bota_rate', type=int, default=400,
        help="Rate-limit Bota polling to this many Hz (default 250)."
    )
    parser.add_argument(
        '--recording_time', type=float, default=30,
        help="How long to record live before stopping, in seconds (default 60)."
    )
    return parser.parse_args()


ARGS = parse_args()

# Hardware config (matches coinft_tune.py)
COM_NAME = '/dev/cu.usbmodem1203'
BAUD_RATE = 1000000

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BOTA_CONFIG_PATH = os.path.join(SCRIPT_DIR, "ethercat_gen0.json")

MODEL_DIR = os.path.join(PROJECT_ROOT, 'trained_model', ARGS.model_dir)
ONNX_PATH = os.path.join(MODEL_DIR, f'{ARGS.sensor_name}_MLP.onnx')
NORM_PATH = os.path.join(MODEL_DIR, f'{ARGS.sensor_name}_norm.json')

if not os.path.isfile(ONNX_PATH):
    sys.exit(f"Model not found: {ONNX_PATH}")
if not os.path.isfile(NORM_PATH):
    sys.exit(f"Norm file not found: {NORM_PATH}")

AXIS_LABELS = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
UNITS = ["N", "N", "N", "Nm", "Nm", "Nm"]

#########################
# 2. LOAD MODEL + NORM  #
#########################
with open(NORM_PATH, 'r') as f:
    norm = json.load(f)

mu_y = np.array(norm['mu_y'], dtype=np.float32)
sd_y = np.array(norm['sd_y'], dtype=np.float32)
# Input normalization is optional -- only apply if the norm file has it.
mu_x = np.array(norm['mu_x'], dtype=np.float32) if 'mu_x' in norm else None
sd_x = np.array(norm['sd_x'], dtype=np.float32) if 'sd_x' in norm else None

session = ort.InferenceSession(ONNX_PATH, providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name
print(f"Loaded model: {ONNX_PATH}")
print(f"Loaded norm:  {NORM_PATH}"
      f"{' (with input normalization)' if mu_x is not None else ' (no input normalization found)'}")


def coinft_to_ft(raw_features):
    """raw_features: [12] baseline-subtracted capacitance readings -> [6] predicted FT."""
    x = raw_features.astype(np.float32)
    if mu_x is not None and sd_x is not None:
        x = (x - mu_x) / sd_x
    pred_norm = session.run(None, {input_name: x[None, :]})[0][0]
    pred_real = (pred_norm * sd_y) + mu_y
    return pred_real


#########################
# 3. SENSOR SETUP       #
#########################
def force_close_serial(port_name):
    try:
        test_ser = serial.Serial(port_name)
        test_ser.close()
        return True
    except Exception:
        return False


print("Setting up Bota sensor...")
bota = bota_driver.BotaDriver(BOTA_CONFIG_PATH)
if not bota.configure():
    sys.exit("Failed to configure Bota driver")
print("Taring Bota sensor...")
if not bota.tare():
    sys.exit("Failed to tare Bota sensor")
if not bota.activate():
    sys.exit("Failed to activate Bota driver")
_ = bota.read_frame()
print("Bota sensor ready.")

force_close_serial(COM_NAME)
try:
    ser = serial.Serial(COM_NAME, BAUD_RATE, timeout=0.1)
    ser.write(b'i'); time.sleep(0.1); ser.reset_input_buffer()
    ser.write(b'q'); time.sleep(0.01)
    p_raw = ser.read(1)
    if not p_raw:
        raise RuntimeError("PSoC not responding")
    packet_size = ord(p_raw) - 1
    num_sensors = (packet_size - 1) // 2
    print(f"PSoC Ready. {num_sensors} Channels. Packet size: {packet_size}")
except Exception as e:
    bota.deactivate()
    bota.shutdown()
    sys.exit(f"Serial Error: {e}")


def read_coinft_packet():
    """Blocking read of a single CoinFT packet. Returns np.array[12] or None on bad frame."""
    if ser.read(1) != b'\x02':
        return None
    data = ser.read(packet_size)
    if not data or data[-1] != 3:
        print("Packet Error (Bad end framing byte)")
        return None
    return np.array(
        [data[i] + 256 * data[i + 1] for i in range(0, packet_size - 1, 2)],
        dtype=np.float32,
    )


#########################
# 4. BASELINE TARE      #
#########################
BASELINE_SAMPLES = 40
print(f"Taring CoinFT baseline over {BASELINE_SAMPLES} samples...")
ser.write(b's')

baseline_buf = []
while len(baseline_buf) < BASELINE_SAMPLES:
    pkt = read_coinft_packet()
    if pkt is not None:
        baseline_buf.append(pkt)
baseline = np.mean(np.array(baseline_buf), axis=0)
print("CoinFT baseline set.")

#########################
# 5. LIVE RECORDING     #
#########################
# No live plotting during recording -- console status only, to keep the
# loop running at full sample rate. Plot is rendered once at the end.
all_true = []
all_pred = []
all_t = []

print(f"Recording live for {ARGS.recording_time}s "
      f"(model_dir={ARGS.model_dir})...")
t0 = time.perf_counter()
last_print_update = 0.0
UI_UPDATE_PERIOD = 0.1  # throttle console status to ~10 Hz -- flush=True every
                        # sample was the actual bottleneck, not the sensors
sample_count = 0

try:
    while True:
        now = time.perf_counter() - t0
        if now >= ARGS.recording_time:
            break

        pkt = read_coinft_packet()
        if pkt is None:
            continue

        feats = pkt - baseline
        pred_ft = coinft_to_ft(feats)

        frame = bota.read_frame()
        true_ft = np.array([*frame.force, *frame.torque], dtype=np.float32)

        sample_count += 1
        all_t.append(now)
        all_true.append(true_ft)
        all_pred.append(pred_ft)

        if (now - last_print_update) >= UI_UPDATE_PERIOD:
            live_rate = sample_count / now if now > 0 else 0.0
            print(
                f"\rRecording... t={now:5.2f}s / {ARGS.recording_time:.2f}s  "
                f"({live_rate:5.1f} Hz, {sample_count} samples)",
                end='', flush=True,
            )
            last_print_update = now

finally:
    print()  # newline after the \r-updated status line
    if ser.is_open:
        ser.write(b'i')
        ser.close()
    bota.deactivate()
    bota.shutdown()
    print("Live comparison stopped.")

#########################
# 6. SUMMARY + SAVE     #
#########################
all_true = np.array(all_true)
all_pred = np.array(all_pred)
all_t = np.array(all_t)

if len(all_true) > 0:
    rmse = np.sqrt(np.mean((all_pred - all_true) ** 2, axis=0))
    measured_rate = len(all_true) / all_t[-1] if all_t[-1] > 0 else 0.0
    print("\n" + "=" * 30)
    print(f"Measured sample rate: {measured_rate:.1f} Hz over {len(all_true)} samples")
    print("LIVE COMPARISON RMSE")
    print("=" * 30)
    for i in range(6):
        print(f"{AXIS_LABELS[i]}: {rmse[i]:.4f} {UNITS[i]}")
    print("-" * 30)
    print(f"AVG: {np.mean(rmse):.4f}")
    print("=" * 30)

    data_dir = os.path.join(PROJECT_ROOT, 'data')
    os.makedirs(data_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(
        data_dir, f"{ARGS.sensor_name}_live_compare_{ARGS.model_dir}_{ts}.h5"
    )
    with h5py.File(out_path, 'w') as f:
        f.create_dataset('t', data=all_t, compression="gzip")
        f.create_dataset('true_ft', data=all_true, compression="gzip")
        f.create_dataset('pred_ft', data=all_pred, compression="gzip")
        f.attrs['model_dir'] = ARGS.model_dir
        f.attrs['sensor_name'] = ARGS.sensor_name
        f.attrs['bota_rate'] = ARGS.bota_rate
        f.attrs['recording_time'] = ARGS.recording_time
    print(f"Saved: {out_path}")

    # Plot only after recording is done.
    fig, axs = plt.subplots(6, 1, figsize=(9, 12), sharex=True)
    for i in range(6):
        axs[i].plot(all_t, all_true[:, i], 'b-', label='Reference (Bota)', alpha=0.8)
        axs[i].plot(all_t, all_pred[:, i], 'r--', label='CoinFT (model)', alpha=0.8)
        axs[i].set_ylabel(f"{AXIS_LABELS[i]} ({UNITS[i]})")
        if i == 0:
            axs[i].legend(loc='upper right')
    axs[-1].set_xlabel("Time (s)")
    fig.suptitle(f"CoinFT vs. Reference -- model: {ARGS.model_dir}")
    fig.tight_layout()
    plt.show()
else:
    print("No samples collected -- nothing to save.")