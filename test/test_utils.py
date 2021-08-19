# Helper functions for pytests
import numpy as np

def read_selections(f):

    sels = []

    with open(f, 'r') as inf:
        for l in inf:
            if l[0] == '#':
                continue
            sels += [l.split(',')[2].split('.')[0]] # name excluding extension

    return sels


def read_selections_and_scores(f):

    sels = []
    scores = []

    with open(f, 'r') as inf:
        for l in inf:
            if l[0] == '#':
                continue
            # Get the image filename and numeric score
            vals = l.split(',')[2:4]
            sels += [vals[0].split('.')[0]]  # exclude extension
            scores += [float(vals[1])]  # convert score to float

    return sels, scores


def check_results(outfile, correct_file):

    sels, scores = read_selections_and_scores(outfile)
    correct_sels, correct_scores = read_selections_and_scores(correct_file)

    # Check the selections by name
    if sels != correct_sels:
        return False

    # Check the numeric scores
    return np.isclose(scores, correct_scores, atol=1e-6).all()


