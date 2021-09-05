import os
# import sys
# sys.path.append('.')
import numpy as np
import matplotlib.pyplot as plt
import argparse


def alg_indexes(filename):
    with open(filename, 'r') as f:
        text = f.read().split("\n")[:-1]
        scores = sorted(text, key=lambda x: float(x.split(", ")[-1]))
        scores = [int(i.split(", ")[1]) for i in scores]

    return scores


def filenames_and_labels(resultsdir):
    filesAndFolders = os.listdir(resultsdir)
    labels = []
    filenames = []
    for i in filesAndFolders:
        if('.' in i):
            continue
        name = i
        if('-' in name):
            name = name[:name.index('-')]
        labels.append(name.replace('_', ' '))
        path = os.path.join(resultsdir, i, 'selections-{}.csv'.format(name))
        filenames.append(path)

    return filenames, labels


def validation_labels(filename):
    with open(filename, 'r') as f:
        text = f.read().split("\n")[:-1]

    labels = {}
    for i in text:
        line = i.split(",")
        labels[int(line[0])] = int(line[1])

    return labels


def get_curve(scores, validationLabels):
    x = list(range(1, len(scores)+1))
    y = []
    numOutliers = 0

    for i in range(len(scores)):
        if(validationLabels[scores[i]] == 1):
            numOutliers += 1
        y.append(numOutliers)

    return x, y


def combine_plots(resultsdir, label_path):
    filenames, labels = filenames_and_labels(resultsdir)

    maxX, maxY = -1, -1
    fig, axes = plt.subplots()

    validationLabels = validation_labels(label_path)
    for i in range(len(filenames)):
        scores = alg_indexes(filenames[i])

        x, y = get_curve(scores, validationLabels)
        maxX = max(maxX, x[-1])
        maxY = max(maxY, y[-1])

        index = x.index(y[-1])
        # area = np.trapz(y, x)
        area = np.trapz(y[:index+1], x[:index+1])

        plt.plot(x, y, label="{} (AUC: {})".format(labels[i], area))

    bestLine = list(range(1, maxX+1))
    plt.plot(bestLine, bestLine, label='Best Line', linestyle='--', color='k')
    plt.title('True Outliers vs. Algorithm Selections')
    plt.xlabel('Number of selections')
    plt.ylabel('Number of true outliers')
    plt.legend(loc='upper left')
    axes.set_xlim(1, maxX)
    axes.set_ylim(1, maxY)
    plt.savefig(f'{resultsdir}/comparison_plot_combined.png')
    plt.savefig(f'{resultsdir}/comparison_plot_combined.pdf')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--resultsdir', type=str,
                        help='Path to the results directory')
    parser.add_argument('-l', '--label_path', type=str,
                        help='Path to the evaluation labels file')

    args = parser.parse_args()
    combine_plots(**vars(args))


main()
