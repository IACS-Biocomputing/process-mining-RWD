# Code Stroke analysis using process mining on RWD datasets
The current repository contain the materials to reproduce the Code Stroke analyses using process mining from RWD datasets detailed in the paper "*Construction of Empirical Clinical Pathways Process Models from Multiple Real-World Datasets*".

## Repository contents

* `activity_log_builder.py` :  main Python script that creates the activity log from the RWD datasets.
* `episode_linking`: Python classes used by the event log builder script.
* `process_mining_dashboard.Rmd`: RMarkdown dashboard that presents the resulting process traces, process maps (with frequency and timining information) and a time-line of the processes detected within the datasets.
* `data/stroke_codes.csv`: ICD-9-CM and ICD-10-CM stroke codes used to properly capture the type of stoke in the episodes.
* `R_Packages`:  source codes of four [bupaR](https://www.bupar.net/) packages forked from the main project, required to the analysis dashboard. See below the installation instructions.
* `sample_input_data`: set of three sample input data files to check the proper execution of the analysis package.

## Requirements

There are three main software packages required for a proper execution of the analysis: Python, R, pandoc and MongoDB.

### Python

The activity log builder requires Python v3. The script has the following package dependencies:

* `datetime` `pytz` `pandas` `numpy` `pymongo`  `tabulate`

### R

The process mining analysis has been tested with R v3.5.x. I thes the following package dependencies:

* `tidyverse` `mongolite` `data.table` `shiny` `miniUI` `eventdataR` `xesreadR` `petrinetR` `ggthemes` `shinyTime` `zoo` `plotly`

In addition, it is required to install the four bupaR forked packages from source code. To do so, launch the R  interpreter, and execute the following commands:

```R
> install.packages("<path_to_R_Packages>/edeaR.IACSmod", repos=NULL, type="source")
> install.packages("<path_to_R_Packages>/processmapR.IACSmod", repos=NULL, type="source")
> install.packages("<path_to_R_Packages>/processmonitR.IACSmod", repos=NULL, type="source")
> install.packages("<path_to_R_Packages>/bupaR.IACSmod", repos=NULL, type="source")
```

### Pandoc

To properly execute the RMarkdown dashboard, Pandoc v1.12.3 or higher is required.

### MongoDB

A MongoDB v4.x.x instance running in the default port (27017) is required.

## Example execution

Using the example data available in `sample_data ` directoy the process mining runs in two steps.

1. Activity log generation, using the Python script

   ```bash
   $ python3 event_log_builder.py sample_input_data/stroke_hospital_events_AR_SAMPLE.csv sample_input_data/stroke_urgent_care_events_AR_SAMPLE.csv sample_input_data/stroke_patients_data_AR_SAMPLE.csv
   ```

   (NOTE: to properly execute the activity log script, `event_log_builder.py`and `episode_linking.py` must be in the same directory)

2. Process mining dashboard generation:

   ```bash
   $ Rscript -e "library(rmarkdown); rmarkdown::render('process_mining_dashboard.Rmd', output_file='process_mining_dashboard.html')" --args "--root_dir=$PWD"
   ```

Once having executed this two commands, a the file `process_mining_dashboard.html` contains a HTML page with the process mining dashboard. 



## Running on Docker

For a fastest reproduction of the experiments, it is also possible to execute the process mining analysis within a docker container following this steps:

1. Pull the `iacsbiocomputing/process_mining_rwd`docker image and create a container

   ```bash
   $ docker run -d --name process_mining_rwd_container iacsbiocomputing/process_mining_rwd
   ```

2. Enter in the docker container 

   ```bash
   $ docker exec -it process_mining_rwd_container bash
   ```

3. Within the docker container, locate the process mining package distribution

   ```bash
   [DOCKER]$ cd process-mining-RWD
   ```

4. Run the example execution using the commands listed in previous section

   ```bash
   [DOCKER]$ python3 event_log_builder.py sample_input_data/stroke_hospital_events_AR_SAMPLE.csv sample_input_data/stroke_urgent_care_events_AR_SAMPLE.csv sample_input_data/stroke_patients_data_AR_SAMPLE.csv
   [DOCKER]$ Rscript -e "library(rmarkdown); rmarkdown::render('process_mining_dashboard.Rmd', output_file='process_mining_dashboard.html')" --args "--root_dir=$PWD"
   ```

5. Exit docker, and pull the resulting dashboard

   ```bash
   [DOCKER]$ exit
   $ docker cp process_mining_rwd_container:process-mining-RWD/process_mining_dashboard.html .
   ```

   

