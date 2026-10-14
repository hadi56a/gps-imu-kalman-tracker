import matplotlib.pyplot as plt
import argparse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../squat'))

from analyse_squat import detect_complete_squats

def plot_imu_data(csv_raw: str, use_gyro=True):
    squat_indices, timestamps, accel_norm_filt, gyro_norm_filt = detect_complete_squats(csv_raw, use_gyro=use_gyro)

    fig, axes = plt.subplots(2, 1, figsize=(12, 6))

    axes[0].plot(timestamps, accel_norm_filt, label='Accel Norm (g)', color='r')
    if squat_indices:
        axes[0].scatter(timestamps[squat_indices], accel_norm_filt[squat_indices], color='blue', zorder=5, label='Squat détecté', marker='v', s=100)
    axes[0].set_title("Données de l'accéléromètre")
    axes[0].set_xlabel('Temps (s)')
    axes[0].set_ylabel('Accélération (g)')
    axes[0].legend()
    axes[0].grid()

    axes[1].plot(timestamps, gyro_norm_filt, label='Gyro Norm (dps)', color='r')
    if squat_indices:
        axes[1].scatter(timestamps[squat_indices], gyro_norm_filt[squat_indices], color='blue', zorder=5, label='Squat détecté', marker='v', s=100)
    axes[1].set_title('Données du gyroscope')
    axes[1].set_xlabel('Temps (s)')
    axes[1].set_ylabel('Vitesse angulaire (dps)')
    axes[1].legend()
    axes[1].grid()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('raw_csv', type=str)
    parser.add_argument('--no-gyro', action='store_true')
    args = parser.parse_args()
    plot_imu_data(args.raw_csv, use_gyro=not args.no_gyro)