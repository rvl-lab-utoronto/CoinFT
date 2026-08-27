import os
import json
import numpy as np
import h5py
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

# --- CONFIGURATION (must match train_mlp_cpu.py) ---
SENSOR_NAME = "CFT24"
MODEL_NAME = f"{SENSOR_NAME}_MLP"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
CONFIG_DIR = os.path.join(SCRIPT_DIR, '..', 'hardware_configs')

device = torch.device("cpu")


# --- NETWORK ARCHITECTURE (must match the one used to train the saved weights) ---
class CoinFTNet(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(CoinFTNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),

            nn.Linear(128, 64),
            nn.ReLU(),

            nn.Linear(64, 36),
            nn.ReLU(),

            nn.Linear(36, 24),
            nn.ReLU(),

            nn.Linear(24, 12),
            nn.ReLU(),

            nn.Linear(12, output_dim)
        )

    def forward(self, x):
        return self.net(x)


def evaluate_on_test():
    # --- Load test data ---
    test_path = os.path.join(DATA_DIR, 'test.h5')
    with h5py.File(test_path, 'r') as f:
        X_test = torch.tensor(f['data'][:], dtype=torch.float32)
        Y_test_norm = torch.tensor(f['label'][:], dtype=torch.float32)

    input_dim = X_test.shape[1]
    output_dim = Y_test_norm.shape[1]
    print(f"Loaded test.h5 -- X: {tuple(X_test.shape)}  Y: {tuple(Y_test_norm.shape)}")

    # --- Load model weights ---
    pth_path = os.path.join(CONFIG_DIR, f"{MODEL_NAME}.pth")
    model = CoinFTNet(input_dim, output_dim).to(device)
    model.load_state_dict(torch.load(pth_path, map_location=device))
    model.eval()
    print(f"Loaded weights from: {pth_path}")

    # --- Load normalization constants ---
    with open(os.path.join(CONFIG_DIR, f'{SENSOR_NAME}_norm.json'), 'r') as f:
        norm = json.load(f)
        mu_y = np.array(norm['mu_y'])
        sd_y = np.array(norm['sd_y'])

    # --- Run inference on the full test set ---
    with torch.no_grad():
        X_test = X_test.to(device)
        pred_norm = model(X_test).cpu().numpy()
        Y_test_norm_np = Y_test_norm.numpy()

    # --- Denormalize back to real units ---
    pred_real = (pred_norm * sd_y) + mu_y
    Y_test_real = (Y_test_norm_np * sd_y) + mu_y

    # --- MSE per axis (all 6, printed for reference) ---
    mse_per_dim = np.mean((pred_real - Y_test_real) ** 2, axis=0)
    labels = ['Fx', 'Fy', 'Fz', 'Mx', 'My', 'Mz']
    print("\nMean-squared error per axis on TEST set (Newtons / Nm):")
    for i, label in enumerate(labels):
        print(f"  {label} : {mse_per_dim[i]:.6f}")

    # --- Plot only Fx, Fy, Fz ---
    plot_len = len(Y_test_real)
    t = np.arange(plot_len)  # raw sample index, no time conversion

    force_axes = [0, 1, 2]  # indices for Fx, Fy, Fz
    force_labels = ['Fx', 'Fy', 'Fz']

    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    for plot_i, axis_i in enumerate(force_axes):
        axs[plot_i].plot(t, Y_test_real[:, axis_i], 'b-', label='True', alpha=0.8)
        axs[plot_i].plot(t, pred_real[:, axis_i], 'r--', label='Pred', alpha=0.8)
        axs[plot_i].set_title(f'Axis {force_labels[plot_i]}')
        axs[plot_i].set_ylabel('Force (N)')
        if plot_i == 0:
            axs[plot_i].legend()

    axs[-1].set_xlabel('Samples')

    plt.tight_layout()
    fig_path = os.path.join(DATA_DIR, f"{MODEL_NAME}_test_force_results.png")
    plt.savefig(fig_path)
    print(f"\nSaved plot: {fig_path}")
    plt.show()


if __name__ == "__main__":
    evaluate_on_test()