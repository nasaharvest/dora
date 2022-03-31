--------------------------------------------------------------
 01 March 2022
--------------------------------------------------------------

Dear Dr. Kerner,

I am attaching the reports of the two reviewers below. Please make the necessary corrections/changes as suggested in the reports and submit a revised manuscript.

Please do not hesitate to contact me if you have any questions.

Sincerely,
Bala Poduval
-------------------------

Reviewer 2:

1) Please provide references supporting these arguments "OOD detection can be used for cleaning datasets, e.g., flagging ground-truth labels with GPS or human entry error or identifying wrongly categorized objects in a catalog. It could also be used for discovery, e.g., to flag novel samples in order to guide instrument acquisition or scientific analysis. Another application is the detection of rare objects that are known to exist but the known examples are too few to create a large enough labeled dataset for supervised classification algorithms."

2) Please provide the contributions of the paper in a highlighted manner. For example, you can use bullets for listing down the contribution. Ex: 1) a tool for applying outlier detection algorithms to various scientific data, 2) outlier score to each sample in a given dataset using interactive visualizations, etc.

3) Can you add a short, high-level description of how to integrate more datasets and algorithms into your framework. It will be an important section as it allows researchers to utilize your framework for their specific domains. You can add a more detailed description in the git repository.

Reviewer 3:

This article is particularly well written and very pleasant to read. The proposed python package, called DORA and already available to the scientific community, allowing the detection of outliers via many approaches already available in the literature, is of great interest for users. As mentioned by the authors and observed on the 4 datasets considered, obviously no method dominates the others, each one having its own numerical qualities in the detection of outliers.

There is just one clarification that I missed when reading the article: it concerns the outlier score. Has this been standardized so that it is comparable for all methods, or does each method remain on its own score scale (the latter potentially changing depending on the data set considered)? And how, if at all?
----------------


--------------------------------------------------------------
 30 March 2022
--------------------------------------------------------------

Dear Dr. Poduval and anonymous reviewers,

Thank you for your review of our paper and for your helpful comments and suggestions. We have addressed them all and I am attaching the revised manuscript here. Below are responses to individual reviewer comments:

Reviewer 2

1) Please provide references supporting these arguments "OOD detection can be used for cleaning datasets, e.g., flagging ground-truth labels with GPS or human entry error or identifying wrongly categorized objects in a catalog. It could also be used for discovery, e.g., to flag novel samples in order to guide instrument acquisition or scientific analysis. Another application is the detection of rare objects that are known to exist but the known examples are too few to create a large enough labeled dataset for supervised classification algorithms."

We have added references to multiple relevant papers (lines 26-33).

2) Please provide the contributions of the paper in a highlighted manner. For example, you can use bullets for listing down the contribution. Ex: 1) a tool for applying outlier detection algorithms to various scientific data, 2) outlier score to each sample in a given dataset using interactive visualizations, etc.

Thank you for the suggestion. We have added a bulleted list of the key contributions at the end of the Introduction on lines 53-61.

3) Can you add a short, high-level description of how to integrate more datasets and algorithms into your framework. It will be an important section as it allows researchers to utilize your framework for their specific domains. You can add a more detailed description in the git repository.

Thank you for the suggestion. We have added a description of how to add new data loaders, outlier ranking algorithms, and results interpretation modules to DORA as well as apply DORA to other datasets (lines 275-292).



Reviewer 3

This article is particularly well written and very pleasant to read. The proposed python package, called DORA and already available to the scientific community, allowing the detection of outliers via many approaches already available in the literature, is of great interest for users. As mentioned by the authors and observed on the 4 datasets considered, obviously no method dominates the others, each one having its own numerical qualities in the detection of outliers.

1) There is just one clarification that I missed when reading the article: it concerns the outlier score. Has this been standardized so that it is comparable for all methods, or does each method remain on its own score scale (the latter potentially changing depending on the data set considered)? And how, if at all?


Thank you for your positive feedback. The outlier scores are not standardized; we use the scores that are output by the algorithms which have different scales across the algorithms and datasets. To inter-compare the algorithms directly, we compare the relative ranking order rather than the absolute scores of each dataset in our experiments and the results modules in DORA.