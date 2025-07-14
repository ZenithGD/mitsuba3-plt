import argparse
import matplotlib.pyplot as plt
import numpy as np
import csv

def main(args):
    samples = []
    times = []
    rmses = []

    with open(args.csv, 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            samples.append(float(row['sample']))
            times.append(float(row['time(s)']))
            rmses.append(float(row['rmse']))

    samples = np.array(samples)
    times = np.array(times)
    rmses = np.array(rmses)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 6))

    ax1.plot(samples, times, color='tab:blue')
    ax1.set_xlabel(args.xlabel)
    ax1.set_ylabel(args.ylabel_time)
    ax1.set_xscale('log', base=2)
    # ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    ax2.plot(samples, rmses, color='tab:orange')
    ax2.set_xscale('log', base=2)
    ax2.set_xlabel(args.xlabel)
    ax2.set_ylabel(args.ylabel_rmse)
    # ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

    fig.suptitle(args.title)
    # plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(args.output)
    print(f"Plot saved to {args.output}")
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot time and RMSE from CSV on a logarithmic sample count axis.")
    parser.add_argument('--csv', type=str, required=True,
                        help='Path to the input CSV file.')
    parser.add_argument('--xlabel', type=str, default='Sample Count',
                        help='Label for the x-axis')
    parser.add_argument('--ylabel_time', type=str, default='Time (s)',
                        help='Label for the time subplot y-axis')
    parser.add_argument('--ylabel_rmse', type=str, default='RMSE',
                        help='Label for the RMSE subplot y-axis')
    parser.add_argument('--title', type=str, default='Time and RMSE vs samples',
                        help='Title of the full figure')
    parser.add_argument('--output', type=str, default='dual_plot.png',
                        help='Output filename to save the plot')

    args = parser.parse_args()
    main(args)
