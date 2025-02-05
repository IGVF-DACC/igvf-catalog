# End-to-end and Response Time Testing

The current state of the IGVF Catalog API can be evaluated by running the `response_times.py` script present at `tests/response_times`.

The `urls.txt` file contains a list of API calls covering all available endpoints of the IGVF Catalog Production API with a combination of params. This file serves as input for the testing script.

Each JSON response for each API call will be stored in a folder called `responses`. Each filename is an MD5 of the entire URL string, so we avoid very large filenames. If a conflicting response from a previous execution is already present in the folder, the script will compare values. Any differences in any response will be reported in the `differences.txt` file.

In case any endpoint fails (HTTP response != 200), the error message will be printed on the screen and saved in the `responses` folder.

Each response time will be stored in the `average_response_time.csv` file. If the same call has already been performed and stored in the CSV file, the script will compute the average between the response times and save in the same CSV file. It gives the feature of running the script multiple times to get fair response time values.

Testing against our development environment is also available by running the same script and setting the global variable `TEST_DEV = True` at the top of the script.

```
$ tests/response_times> cd tests/response_times; python3 response_times.py
Fetching: https://api.catalog.igvf.org/api/variants?spdi=NC_000020.11%3A3658947%3AA%3AG&organism=Homo%20sapiens&page=0
Fetching: https://api.catalog.igvf.org/api/variants?hgvs=NC_000020.11%3Ag.3658948A%3EG&organism=Homo%20sapiens&page=0
Fetching: https://api.catalog.igvf.org/api/variants?region=chr1%3A1157520-1158189&organism=Homo%20sapiens&page=0
Fetching: https://api.catalog.igvf.org/api/variants?mouse_strain=A_J&organism=Mus%20musculus&page=0
...

Saved responses in 'responses/', average times in 'average_response_time.csv', and differences in 'differences.txt' if any.
```
