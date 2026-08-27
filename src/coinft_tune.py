import os
import sys
import time
import threading
from datetime import datetime

import numpy as np
import h5py
import serial
import serial.tools.list_ports

import bota_driver

#########################
# 1. CONTROL PANEL      #
#########################
COM_NAME = '/dev/cu.usbmodem11203'                 # Serial port for CoinFT
BAUD_RATE = 1000000
RECORD_DURATION = 35              # How long to actually record both sensors, in [s]
TRIM_DURATION = 30                # How much of that recording to keep/use for calibration, in [s]
BOTA_POLL_RATE = 500               # Rate-limit Bota polling to this many Hz
SENSOR_NAME = 'CFT24'
ID = 'train'                       # Unique identifier for the calibration session

BOTA_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ethercat_gen0.json"
)

#########################
# 2. INITIALIZATION     #
#########################
# No hardware sync line -- both threads timestamp with time.perf_counter()
# on the same clock, and we align via interpolation after collection.
bota_data_list = []       # each entry: [Fx, Fy, Fz, Mx, My, Mz]
bota_time_list = []       # perf_counter() timestamp per Bota sample

coinft_data_list = []
coinft_time_list = []     # perf_counter() timestamp per CoinFT packet

stop_daq = threading.Event()
stop_cft = threading.Event()


def force_close_serial(port_name):
    try:
        test_ser = serial.Serial(port_name)
        test_ser.close()
        return True
    except Exception:
        return False


# 2a. Bota sensor setup + tare (replaces ATI taring block)
print("Setting up Bota sensor...")
bota = bota_driver.BotaDriver(BOTA_CONFIG_PATH)

if not bota.configure():
    sys.exit("Failed to configure Bota driver")

print("Taring Bota sensor...")
if not bota.tare():
    sys.exit("Failed to tare Bota sensor")

if not bota.activate():
    sys.exit("Failed to activate Bota driver")

# Warm-up read so the stream is live before we start the real acquisition
_ = bota.read_frame()
print("Bota sensor ready.")

# 2b. Serial Setup (unchanged)
force_close_serial(COM_NAME)
try:
    ser = serial.Serial(COM_NAME, BAUD_RATE, timeout=0.1)
    ser.write(b'i'); time.sleep(0.1); ser.reset_input_buffer()
    ser.write(b'q'); time.sleep(0.01)
    p_raw = ser.read(1)
    if not p_raw:
        raise RuntimeError("PSoC not responding")
    packet_size = ord(p_raw) - 1            # This should be 25
    num_sensors = (packet_size - 1) // 2     # This should be 12
    print(f"PSoC Ready. {num_sensors} Channels. Packet size: {packet_size}")
except Exception as e:
    bota.deactivate()
    bota.shutdown()
    sys.exit(f"Serial Error: {e}")


#########################
# 3. DATA ACQUISITION   #
#########################
def read_bota():
    """
    Software-polled acquisition of the Bota sensor, rate-limited to
    BOTA_POLL_RATE (default 500 Hz) instead of polling as fast as possible.
    Timestamps each sample with time.perf_counter() for later alignment
    against the CoinFT stream.
    """
    period = 1.0 / BOTA_POLL_RATE
    next_read = time.perf_counter()

    while not stop_daq.is_set():
        frame = bota.read_frame()
        fx, fy, fz = frame.force
        mx, my, mz = frame.torque
        bota_data_list.append([fx, fy, fz, mx, my, mz])
        bota_time_list.append(time.perf_counter())

        next_read += period
        sleep_time = next_read - time.perf_counter()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # We're running behind schedule -- reset the reference point
            # instead of letting sleep_time drift further negative.
            next_read = time.perf_counter()


def read_coinft():
    """Reads PSoC data using standard s/i protocol, now also timestamped."""
    ser.write(b's')
    while not stop_cft.is_set():
        if ser.read(1) == b'\x02':
            data = ser.read(packet_size)
            if data and data[-1] == 3:
                coinft_data_list.append(
                    [data[i] + 256 * data[i + 1] for i in range(0, packet_size - 1, 2)]
                )
                coinft_time_list.append(time.perf_counter())
            else:
                print("Packet Error (Bad end framing byte)")
    ser.write(b'i')


#########################
# 4. RUN DATA COLLECTION#
#########################
print("BEGIN DATA COLLECTION...")
t_daq = threading.Thread(target=read_bota)
t_cft = threading.Thread(target=read_coinft)

try:
    # Both sensors record simultaneously for the full RECORD_DURATION.
    # No leading/trailing buffer needed -- the extra recording time itself
    # is the buffer, trimmed down to TRIM_DURATION afterward.
    t_daq.start()
    t_cft.start()

    time.sleep(RECORD_DURATION)

    stop_cft.set()
    stop_daq.set()
    t_cft.join(timeout=2.0)
    t_daq.join(timeout=2.0)
finally:
    if ser.is_open:
        ser.write(b'i')
        ser.close()
    bota.deactivate()
    bota.shutdown()
    print("Acquisition Stopped.")


#########################
# 5. SYNC & CALIBRATION #
#########################
# No hardware sync line -- align by interpolating the faster Bota stream
# onto the CoinFT's own sample timestamps (both clocks are the same
# time.perf_counter() clock since everything runs in this one process).
bota_FT = np.array(bota_data_list)          # [N_bota, 6] -- already calibrated Fx..Mz
bota_t = np.array(bota_time_list)
coinft_raw = np.array(coinft_data_list)      # [N_cft, num_sensors]
coinft_t = np.array(coinft_time_list)

# Anchor the window on the shared END time (whichever sensor stopped first),
# then take exactly TRIM_DURATION seconds back from there. This gives a
# fixed-length window from the middle of the RECORD_DURATION recording,
# discarding the first few seconds as a startup buffer.
t_end = min(bota_t[-1], coinft_t[-1])
t_start = t_end - TRIM_DURATION

if t_start < max(bota_t[0], coinft_t[0]):
    print(
        f"WARNING: requested {TRIM_DURATION}s window starts before one of the "
        f"sensors' data begins -- window will be clipped to available data."
    )
    t_start = max(t_start, bota_t[0], coinft_t[0])

valid = (coinft_t >= t_start) & (coinft_t <= t_end)
coinft_t = coinft_t[valid]
coinft_raw = coinft_raw[valid]

# Sanity check against CoinFT's known mechanical rate (~97 Hz)
coinft_measured_rate = len(coinft_t) / (coinft_t[-1] - coinft_t[0])
bota_measured_rate = len(bota_t) / (bota_t[-1] - bota_t[0])
print(f"Aligned window: {t_end - t_start:.3f}s (target {TRIM_DURATION}s)")
print(f"CoinFT measured rate: {coinft_measured_rate:.2f} Hz (expected ~97 Hz)")
print(f"Bota measured rate:   {bota_measured_rate:.2f} Hz")

# Interpolate each Bota axis onto the CoinFT timestamps
bota_cal_FT = np.zeros((len(coinft_t), 6))
for axis in range(6):
    bota_cal_FT[:, axis] = np.interp(coinft_t, bota_t, bota_FT[:, axis])

# Baseline Taring for CoinFT (Bota is already tared via bota.tare())
baseline = np.mean(coinft_raw[10:50, :], axis=0)
sensor_cal_data = coinft_raw - baseline

# Drop the first sample -- original code dropped it due to electrical noise
# on the CoinFT side right at acquisition start.
if len(bota_cal_FT) > 1:
    bota_cal_FT = bota_cal_FT[1:, :]
    sensor_cal_data = sensor_cal_data[1:, :]

# Least Squares (2nd Order)
X = np.hstack([sensor_cal_data, sensor_cal_data ** 2])
A_T, _, _, _ = np.linalg.lstsq(X, bota_cal_FT, rcond=None)
calibrated_FT = X @ A_T  # A_T is 24 x 6


#########################
# 5a. VALIDATION        #
#########################
rmse = np.sqrt(np.mean((calibrated_FT - bota_cal_FT) ** 2, axis=0))
print("\n" + "=" * 30)
print("LEAST SQUARES FIT CALIBRATION ACCURACY (RMSE)")
print("=" * 30)
axis_labels = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
units = ["N", "N", "N", "Nm", "Nm", "Nm"]

for i in range(6):
    print(f"{axis_labels[i]}: {rmse[i]:.4f} {units[i]}")
print("-" * 30)
print(f"AVG: {np.mean(rmse):.4f}")
print("=" * 30 + "\n")
print("While validated on training data, this gives a rough idea on the quality of the sensor data. There should at least be a learnable signal.")


#########################
# 6. SAVE RESULTS (HDF5)#
#########################
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, 'data')

if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"Created directory: {data_dir}")

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
h5_filename = f'{SENSOR_NAME}_calibrationData_{ts}_{ID}.h5'
full_path = os.path.join(data_dir, h5_filename)

print(full_path)

with h5py.File(full_path, 'w') as f:
    f.create_dataset('A_T', data=A_T, compression="gzip")
    f.create_dataset('sensor_cal_data', data=sensor_cal_data, compression="gzip")
    f.create_dataset('bota_cal_FT', data=bota_cal_FT, compression="gzip")

    f.attrs['sensor_name'] = SENSOR_NAME
    f.attrs['timestamp'] = ts
    f.attrs['reference_sensor'] = 'Bota'

print(f"Saved: {h5_filename}")