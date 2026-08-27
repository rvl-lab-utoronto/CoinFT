import time
from bota_driver import BotaDriver, DriverState

# Path to your sensor's JSON configuration file
# (generate/download this from Bota's web-based Config Tool)
CONFIG_PATH = "ethercat_gen0.json"


def main():
    driver = BotaDriver(CONFIG_PATH)

    # Lifecycle: UNCONFIGURED -> INACTIVE -> ACTIVE
    if not driver.configure():
        raise RuntimeError("Failed to configure driver")

    # Optional: zero out the sensor while INACTIVE
    if not driver.tare():
        print("Warning: tare failed")

    if not driver.activate():
        raise RuntimeError("Failed to activate driver")

    print(f"Driver version: {driver.get_driver_version_string()}")
    print(f"Expected timestep: {driver.get_expected_timestep_us()}")

    try:
        while True:
            time.sleep(0.1)
            frame = driver.read_frame()  # blocks until new data arrives

            fx, fy, fz = frame.force
            print(f"Fx: {fx:.3f} N  Fy: {fy:.3f} N  Fz: {fz:.3f} N")

            if frame.status.invalid:
                print("  Warning: frame marked invalid")
            if frame.status.overrange:
                print("  Warning: frame overrange")

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        driver.deactivate()
        driver.cleanup()
        driver.shutdown()


if __name__ == "__main__":
    main()
