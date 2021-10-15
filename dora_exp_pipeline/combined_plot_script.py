import os
import matplotlib.pyplot as plt
import argparse

alg_colors = {
                'demud': 'red',
                'pca': 'purple',
                'iforest': 'pink',
                'pae': 'blue',
                'negative sampling': 'brown',
                'random': 'gray',
                'rx': 'green',
                'lrx': 'orange'
             }


def alg_indexes(filename):
    with open(filename, 'r') as f:
        text = f.read().split("\n")[:-1]
        scores = sorted(text, key=lambda x: float(x.split(", ")[0]))
        # Field 2 is the sample id
        scores = [i.split(", ")[2] for i in scores]

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
        labels[line[0]] = int(line[1])

    return labels


def get_selections_curve(scores, validationLabels):
    x = list(range(1, len(scores)+1))
    y = []
    numOutliers = 0

    for i in range(len(scores)):
        if(validationLabels[scores[i]] == 1):
            numOutliers += 1
        y.append(numOutliers)

    return x, y


def get_precision_curve(scores, validationLabels):
    tot_outliers = sum([x for x in validationLabels.values()])
    x = list(range(1, len(scores)+1))
    y = []
    numOutliers = 0
    for i in range(len(scores)):
        if(validationLabels[scores[i]] == 1):
            numOutliers += 1
        y.append(float(numOutliers)/(i+1))
        if (i+1) == tot_outliers:
            print('Precision at N=%d: %f' %
                  (tot_outliers, float(numOutliers)/(i+1)))

    return x, y


def random_sel_EV(scores, labels, n):
    n_scores = len(scores)
    n_outliers = sum(labels.values())

    # Full formulation
    # return sum([comb(n_outliers, i) *
    #            comb(n_scores-n_outliers, n-i) * i
    #            for i in range(n+1)]) / comb(n_scores, n)

    # Simplified formulation
    return (n_outliers * n) / n_scores


def get_random_selections_curve(scores, validationLabels):
    x = list(range(1, len(scores)+1))
    y = []
    for i in range(len(scores)):
        y.append(random_sel_EV(scores, validationLabels, i))

    return x, y


def get_random_precision_curve(scores, validationLabels):
    x = list(range(1, len(scores)+1))
    y = []
    for i in range(len(scores)):
        numOutliers = random_sel_EV(scores, validationLabels, i)
        y.append(numOutliers / (i+1))

        if (i+1) == sum(validationLabels.values()):
            print('Precision at N=%d: %f' %
                  (sum(validationLabels.values()), float(numOutliers)/(i+1)))

    return x, y


def combine_plots(resultsdir, label_path, precision_at_n):
    filenames, labels = filenames_and_labels(resultsdir)

    fig, axes = plt.subplots()

    validationLabels = validation_labels(label_path)
    num_outliers = sum([x for x in validationLabels.values()])

    if precision_at_n:
        plt.axhline(y=1, label='Oracle', linestyle='--', color='k')
        plt.title('Precision at N')
        plt.xlabel('Number of selections (N)')
        plt.ylabel('Precision at N')
    else:
        bestLine = list(range(1, num_outliers+1))
        plt.plot(bestLine, bestLine, label='Oracle', linestyle='--',
                 color='k')
        plt.title('Known Outliers vs. Algorithm Selections')
        plt.xlabel('Number of selections')
        plt.ylabel('Number of known outliers')

    for i in range(len(filenames)):
        scores = alg_indexes(filenames[i])

        if precision_at_n:
            print(labels[i])
            x, y = get_precision_curve(scores, validationLabels)
            plt.plot(x, y, label="{}".format(labels[i]),
                     color=alg_colors[labels[i]])
        else:
            x, y = get_selections_curve(scores, validationLabels)
            area = sum(y)/sum([i for i in range(len(scores))])
            plt.plot(x, y, label="{} (MDR: {:.2f})".format(labels[i], area),
                     color=alg_colors[labels[i]])

    if precision_at_n:
        print("random_theoretical")
        x, y = get_random_precision_curve(scores, validationLabels)
        plt.plot(x, y, label="{}".format("Theoretical Random"), linestyle='--',
                 color=alg_colors['random'])
    else:
        x, y = get_random_selections_curve(scores, validationLabels)
        area = sum(y)/sum([i for i in range(len(scores))])
        plt.plot(x, y,
                 label="{} (MDR: {:.2f})".format("Theoretical Random", area),
                 linestyle='--', color=alg_colors['random'])

    axes.set_xlim(1, len(scores))
    plt.legend()
    if precision_at_n:
        axes.set_ylim(0, 1)
        plt.savefig(f'{resultsdir}/comparison_plot_combined_p-at-n.png')
        plt.savefig(f'{resultsdir}/comparison_plot_combined_p-at-n.pdf')
    else:
        axes.set_ylim(0, num_outliers)
        plt.savefig(f'{resultsdir}/comparison_plot_combined.png')
        plt.savefig(f'{resultsdir}/comparison_plot_combined.pdf')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--resultsdir', type=str,
                        help='Path to the results directory')
    parser.add_argument('-l', '--label_path', type=str,
                        help='Path to the evaluation labels file')
    parser.add_argument('--precision_at_n', action='store_true',
                        help='Plot in terms of precision at N')

    args = parser.parse_args()
    combine_plots(**vars(args))


main()
