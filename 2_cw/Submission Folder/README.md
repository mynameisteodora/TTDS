## How to use the evaluation system

Make sure that the following files are placed in the folder named 'systems':
- qrels.txt - a file containing query numbers and relevant documents
- S[1-6].results - files containing ordered results for queries, for each of the systems being evaluated

Then, from the same location as the 'systems' folder, run the following command:

$ python Eval.py

This will start the module and produce the evaluation files per system, together with a file with averages for each metric.

You should not need any special packages to run this module.