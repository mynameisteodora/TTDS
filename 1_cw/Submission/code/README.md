# This is a guide for using the simple query tool for the TTDS Coursework 1.

### Required packages
To run the system, you need to have the following packages installed:
* re (included in Python)
* os (included in Python)
* Porter2 (https://pypi.org/project/stemming/1.0/)
* xml.etree (https://docs.python.org/2/library/xml.etree.elementtree.html)
* bisect (https://pymotw.com/2/bisect/)
* pickle

### Collection file structure
Please make sure that the collection used for building the index is in TREC form, as the collection provided in the labs.

### Query file structure
The system can read queries from a specified file and expects one single query per line.
Each line must begin with the query number followed by a space.

Example:
1 "income tax"
2 this is a free text query
3 #10(proximity, query)
4 write AND NOT me
5 "income tax" AND NOT #10(middle,east)

### Loaded index
If run in default mode, the program will load the inverted index generated on the new
collection. This index is pickled in the file `index.p`, so please make sure you don't remove this file from the folder.

### Folder structure
In the `code.zip` file, you should find the following files.
.
├── collections
|   ├── sample.xml
|   └── trec.sample.xml
|   └── trec.5000.xml
├── englishST.txt
├── index.p
├── indices
|   ├── index.lab.collection.txt
|   └── index.new.collection.txt
├── InvertedIndex.py
├── queries
|   ├── queries.lab2.txt
|   └── queries.lab3.txt
|   └── queries.boolean.txt
|   └── queries.ranked.txt
├── README.md
├── Term.py
└── RunSearch.py

### Running the search
Make sure you are in the `code` folder. In the terminal, enter:

$ python ./RunSearch.py

This will prompt you with some questions about how you want to load the index or whether
you want to build a new one.

Options:
* [L] Load an existing index => you have to specify the path to a pickle file (.p)
* [C] Create new index from collection => you have to specify the path to a TREC collection
  * You will also be asked to specify a path for the new index to be saved (.txt)
  * `index.p` will be replaced by this newly created index
* [D] Use the default index => it will be loaded from the `index.p` file

Then, you will have the choice of whether to enter queries manually or read them from a file.

Options:
* [M] Manually enter queries => queries have to be Boolean, phrase, proximity or free word
                                but DO NOT have to contain the query number
* [F] Read queries from a file => you have to specify the path to a query file
  * You will also be asked to specify a path for the results to be saved (.txt)

Finally, the system will ask if you want to continue with another query.

Options:
* [Y] Yes => the system will loop back to the query input step
* [N] No => the system will exit
