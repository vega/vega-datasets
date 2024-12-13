# vega-datasets
`2.11.0` | [GitHub](http://github.com/vega/vega-datasets.git) | 2024-12-13 21:05:54 [UTC]

Common repository for example datasets used by Vega related projects.

## licenses
| name         | path                                        | title                    |
|:-------------|:--------------------------------------------|:-------------------------|
| BSD-3-Clause | https://opensource.org/license/bsd-3-clause | The 3-Clause BSD License |

## contributors
| title                      | path                                                      |
|:---------------------------|:----------------------------------------------------------|
| UW Interactive Data Lab    | http://idl.cs.washington.edu                              |
| vega-datasets contributors | https://github.com/vega/vega-datasets/graphs/contributors |

# resources
## `7zip.png`
### path
7zip.png
### description
Application icons from open-source software projects.
## `airports.csv`
### path
airports.csv
### schema
    
| name      | type   |
|:----------|:-------|
| iata      | string |
| name      | string |
| city      | string |
| state     | string |
| country   | string |
| latitude  | number |
| longitude | number |
## `annual-precip.json`
### path
annual-precip.json
### description
A raster grid of global annual precipitation for the year 2016 at a resolution 1 degree of lon/lat per cell.
### sources
| title                             | path                                                                                                   |
|:----------------------------------|:-------------------------------------------------------------------------------------------------------|
| Climate Forecast System Version 2 | https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/climate-forecast-system-version2-cfsv2 |
## `anscombe.json`
### path
anscombe.json
### description
Graphs in Statistical Analysis, F. J. Anscombe, The American Statistician.
### schema
    
| name   | type    |
|:-------|:--------|
| Series | string  |
| X      | integer |
| Y      | number  |
## `barley.json`
### path
barley.json
### description
The result of a 1930s agricultural experiment in Minnesota, this dataset contains yields for 10 different varieties of barley at six different sites.

    It was first published by agronomists F.R. Immer, H.K. Hayes, and L. Powers in the 1934 paper "Statistical Determination of Barley Varietal Adaption".

    R.A. Fisher's popularized its use in the field of statistics when he included it in his book "The Design of Experiments".

    Since then it has been used to demonstrate new statistical techniques, including the trellis charts developed by Richard Becker, William Cleveland and others in the 1990s.

### schema
    
| name    | type    |
|:--------|:--------|
| yield   | number  |
| variety | string  |
| year    | integer |
| site    | string  |
### sources
| title                               | path                                                                 |
|:------------------------------------|:---------------------------------------------------------------------|
| The Design of Experiments Reference | https://en.wikipedia.org/wiki/The_Design_of_Experiments              |
| Trellis Charts Paper                | http://ml.stat.purdue.edu/stat695t/writings/TrellisDesignControl.pdf |
## `birdstrikes.csv`
### path
birdstrikes.csv
### description
Records of reported wildlife strikes received by the U.S. FAA
### schema
    
| name                      | type    |
|:--------------------------|:--------|
| Airport Name              | string  |
| Aircraft Make Model       | string  |
| Effect Amount of damage   | string  |
| Flight Date               | date    |
| Aircraft Airline Operator | string  |
| Origin State              | string  |
| Phase of flight           | string  |
| Wildlife Size             | string  |
| Wildlife Species          | string  |
| Time of day               | string  |
| Cost Other                | integer |
| Cost Repair               | integer |
| Cost Total $              | integer |
| Speed IAS in knots        | integer |
### sources
| title                        | path                    |
|:-----------------------------|:------------------------|
| FAA Wildlife Strike Database | http://wildlife.faa.gov |
## `budget.json`
### path
budget.json
### description
Historical and forecasted federal revenue/receipts produced in 2016 by the U.S. Office of Management and Budget.
### schema
    
| name                    | type    |
|:------------------------|:--------|
| Source Category Code    | integer |
| Source category name    | string  |
| Source subcategory      | integer |
| Source subcategory name | string  |
| Agency code             | integer |
| Agency name             | string  |
| Bureau code             | integer |
| Bureau name             | string  |
| Account code            | integer |
| Account name            | string  |
| Treasury Agency code    | integer |
| On- or off-budget       | string  |
| 1962                    | string  |
| 1963                    | string  |
| 1964                    | string  |
| 1965                    | string  |
| 1966                    | string  |
| 1967                    | string  |
| 1968                    | string  |
| 1969                    | string  |
| 1970                    | string  |
| 1971                    | string  |
| 1972                    | string  |
| 1973                    | string  |
| 1974                    | string  |
| 1975                    | string  |
| 1976                    | string  |
| TQ                      | string  |
| 1977                    | string  |
| 1978                    | string  |
| 1979                    | string  |
| 1980                    | string  |
| 1981                    | string  |
| 1982                    | string  |
| 1983                    | string  |
| 1984                    | string  |
| 1985                    | string  |
| 1986                    | string  |
| 1987                    | string  |
| 1988                    | string  |
| 1989                    | string  |
| 1990                    | string  |
| 1991                    | string  |
| 1992                    | string  |
| 1993                    | string  |
| 1994                    | string  |
| 1995                    | string  |
| 1996                    | string  |
| 1997                    | string  |
| 1998                    | string  |
| 1999                    | string  |
| 2000                    | string  |
| 2001                    | string  |
| 2002                    | string  |
| 2003                    | string  |
| 2004                    | string  |
| 2005                    | string  |
| 2006                    | string  |
| 2007                    | string  |
| 2008                    | string  |
| 2009                    | string  |
| 2010                    | string  |
| 2011                    | string  |
| 2012                    | string  |
| 2013                    | string  |
| 2014                    | string  |
| 2015                    | string  |
| 2016                    | string  |
| 2017                    | string  |
| 2018                    | string  |
| 2019                    | string  |
| 2020                    | string  |
### sources
| title                                                       | path                                                                |
|:------------------------------------------------------------|:--------------------------------------------------------------------|
| Office of Management and Budget - Budget FY 2016 - Receipts | https://www.govinfo.gov/app/details/BUDGET-2016-DB/BUDGET-2016-DB-3 |
## `budgets.json`
### path
budgets.json
### schema
    
| name         | type    |
|:-------------|:--------|
| budgetYear   | integer |
| forecastYear | integer |
| value        | number  |
## `burtin.json`
### path
burtin.json
### description
The burtin.json dataset is based on graphic designer Will Burtin's 1951 visualization of antibiotic effectiveness, originally published in Scope Magazine.

    The dataset compares the performance of three antibiotics against 16 different bacteria.

    Numerical values in the dataset represent the minimum inhibitory concentration (MIC) of each antibiotic, measured in units per milliliter, with lower values indicating higher antibiotic effectiveness.

    The dataset was featured as an example in the Protovis project, a precursor to D3.js.

    As noted in the Protovis example, "Recreating this display revealed some minor errors in the original: a missing grid line at 0.01 μg/ml, and an exaggeration of some values for penicillin".

    The vega-datsets version is largely consistent with the Protovis version of the dataset, with one correction (changing 'Brucella antracis' to the correct 'Bacillus anthracis') and the addition of a new column, 'Genus', to group related bacterial species together.

    The caption of the original 1951 [visualization](https://graphicdesignarchives.org/wp-content/uploads/wmgda_8616c.jpg) 
    reads as follows:

    > ## Antibacterial ranges of Neomycin, Penicillin and Streptomycin
    >
    >
    > The chart compares the in vitro sensitivities to neomycin of some of the common pathogens (gram+ in > red and gram- in blue) with their sensitivities to penicillin, and streptomycin.
    >
    > The effectiveness of the antibiotics is expressed as the highest dilution in μ/ml. which inhibits > the test organism.
    >
    > High dilutions are toward the periphery; consequently the length of the colored bar is proportional > to the effectiveness.
    >
    > It is apparent that neomycin is especially effective against Staph. albus and aureus, Streph. > fecalis, A. aerogenes, S. typhosa, E. coli, Ps. aeruginosa, Br. abortus, K. pneumoniae, Pr. > vulgaris, S. schottmuelleri and M. tuberculosis.
    >
    > Unfortunately, some strains of proteus, pseudomonas and hemolytic streptococcus are resistant to > neomycin, although the majority of these are sensitive to neomycin.
    >
    > It also inhibits actinomycetes, but is inactive against viruses and fungi. Its mode of action is > not understood.

### schema
    
| name          | type   |
|:--------------|:-------|
| Bacteria      | string |
| Penicillin    | number |
| Streptomycin  | number |
| Neomycin      | number |
| Gram_Staining | string |
| Genus         | string |
### sources
| title                        | path                                                                 |
|:-----------------------------|:---------------------------------------------------------------------|
| Scope Magazine               | https://graphicdesignarchives.org/projects/scope-magazine-vol-iii-5/ |
| Protovis Antibiotics Example | https://mbostock.github.io/protovis/ex/antibiotics-burtin.html       |
## `cars.json`
### path
cars.json
### description
Collection of car specifications and performance metrics from various automobile manufacturers.
### schema
    
| name             | type    |
|:-----------------|:--------|
| Name             | string  |
| Miles_per_Gallon | integer |
| Cylinders        | integer |
| Displacement     | number  |
| Horsepower       | integer |
| Weight_in_lbs    | integer |
| Acceleration     | number  |
| Year             | date    |
| Origin           | string  |
### sources
| title                    | path                              |
|:-------------------------|:----------------------------------|
| StatLib Datasets Archive | http://lib.stat.cmu.edu/datasets/ |
## `co2-concentration.csv`
### path
co2-concentration.csv
### description
Scripps CO2 program data ut modified to only include date, CO2, seasonally adjusted CO2. 
    Only includes rows with valid data.
### schema
    
| name         | type   |
|:-------------|:-------|
| Date         | date   |
| CO2          | number |
| adjusted CO2 | number |
### sources
| title               | path                                                                    |
|:--------------------|:------------------------------------------------------------------------|
| Scripps CO2 Program | https://scrippsco2.ucsd.edu/data/atmospheric_co2/primary_mlo_co2_record |
## `countries.json`
### path
countries.json
### description
This dataset combines key demographic indicators (life expectancy at birth and
    fertility rate measured as babies per woman) for various countries from 1955 to 2000 at 5-year
    intervals. It includes both current values and adjacent time period values (previous and next)
    for each indicator. Gapminder's [data documentation](https://www.gapminder.org/data/documentation/) 
    notes that its philosophy is to fill data gaps with estimates and use current
    geographic boundaries for historical data. Gapminder states that it aims to "show people the
    big picture" rather than support detailed numeric analysis.
### schema
    
| name          | type    | description                                                              |
|:--------------|:--------|:-------------------------------------------------------------------------|
| _comment      | string  |                                                                          |
| year          | integer | Years from 1955 to 2000 at 5-year intervals                              |
| fertility     | number  | Fertility rate (average number of children per woman) for the given year |
| life_expect   | number  | Life expectancy in years for the given year                              |
| n_fertility   | number  | Fertility rate for the next 5-year interval                              |
| n_life_expect | number  | Life expectancy for the next 5-year interval                             |
| country       | string  | Name of the country                                                      |
### sources
| title                                  | path                                                                                                                 |   version |
|:---------------------------------------|:---------------------------------------------------------------------------------------------------------------------|----------:|
| Gapminder Foundation - Life Expectancy | https://docs.google.com/spreadsheets/d/1RehxZjXd7_rG8v2pJYV6aY0J3LAsgUPDQnbY4dRdiSs/edit?gid=176703676#gid=176703676 |        14 |
| Gapminder Foundation - Fertility       | https://docs.google.com/spreadsheets/d/1aLtIpAWvDGGa9k2XXEz6hZugWn0wCd5nmzaRPPjbYNA/edit?gid=176703676#gid=176703676 |        14 |
### licenses
| title                                          | path                                     |
|:-----------------------------------------------|:-----------------------------------------|
| Creative Commons Attribution 4.0 International | https://www.gapminder.org/free-material/ |
## `crimea.json`
### path
crimea.json
### schema
    
| name    | type    |
|:--------|:--------|
| date    | date    |
| wounds  | integer |
| other   | integer |
| disease | integer |
## `disasters.csv`
### path
disasters.csv
### description
Annual number of deaths from disasters.
### schema
    
| name   | type    |
|:-------|:--------|
| Entity | string  |
| Year   | integer |
| Deaths | integer |
### sources
| title                                    | path                                            |
|:-----------------------------------------|:------------------------------------------------|
| Our World in Data - Natural Catastrophes | https://ourworldindata.org/natural-catastrophes |
## `driving.json`
### path
driving.json
### schema
    
| name   | type    |
|:-------|:--------|
| side   | string  |
| year   | integer |
| miles  | integer |
| gas    | number  |
### sources
| title          | path                                                                                      |
|:---------------|:------------------------------------------------------------------------------------------|
| New York Times | https://archive.nytimes.com/www.nytimes.com/imagepages/2010/05/02/business/02metrics.html |
## `earthquakes.json`
### path
earthquakes.json
### description
Earthquake data retrieved Feb 6, 2018
### sources
| title                | path                                                                       |
|:---------------------|:---------------------------------------------------------------------------|
| USGS Earthquake Feed | https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson |
## `ffox.png`
### path
ffox.png
### description
Application icons from open-source software projects.
## `flare-dependencies.json`
### path
flare-dependencies.json
### schema
    
| name   | type    |
|:-------|:--------|
| source | integer |
| target | integer |
## `flare.json`
### path
flare.json
### schema
    
| name   | type    |
|:-------|:--------|
| id     | integer |
| name   | string  |
## `flights-10k.json`
### path
flights-10k.json
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name        | type    |
|:------------|:--------|
| date        | string  |
| delay       | integer |
| distance    | integer |
| origin      | string  |
| destination | string  |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `flights-200k.arrow`
### path
flights-200k.arrow
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name     | type    |
|:---------|:--------|
| delay    | integer |
| distance | integer |
| time     | number  |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `flights-200k.json`
### path
flights-200k.json
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name     | type    |
|:---------|:--------|
| delay    | integer |
| distance | integer |
| time     | number  |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `flights-20k.json`
### path
flights-20k.json
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name        | type    |
|:------------|:--------|
| date        | string  |
| delay       | integer |
| distance    | integer |
| origin      | string  |
| destination | string  |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `flights-2k.json`
### path
flights-2k.json
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name        | type    |
|:------------|:--------|
| date        | string  |
| delay       | integer |
| distance    | integer |
| origin      | string  |
| destination | string  |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `flights-3m.parquet`
### path
flights-3m.parquet
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name        | type     |
|:------------|:---------|
| date        | datetime |
| delay       | integer  |
| distance    | integer  |
| origin      | string   |
| destination | string   |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `flights-5k.json`
### path
flights-5k.json
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name        | type    |
|:------------|:--------|
| date        | string  |
| delay       | integer |
| distance    | integer |
| origin      | string  |
| destination | string  |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `flights-airport.csv`
### path
flights-airport.csv
### description
Flight delay statistics from U.S. Bureau of Transportation Statistics. Transformed using `/scripts/flights.py`
### schema
    
| name        | type    |
|:------------|:--------|
| origin      | string  |
| destination | string  |
| count       | integer |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
## `football.json`
### path
football.json
### description
Football match outcomes across multiple divisions from 2013 to 2017, part of a
    larger dataset from OpenFootball. The subset was made such that there are records for all five
    chosen divisions over the time period.
### schema
    
| name       | type    |
|:-----------|:--------|
| date       | date    |
| division   | string  |
| home_team  | string  |
| away_team  | string  |
| home_score | integer |
| away_score | integer |
### sources
| title        | path                                          |
|:-------------|:----------------------------------------------|
| OpenFootball | https://github.com/openfootball/football.json |
## `gapminder-health-income.csv`
### path
gapminder-health-income.csv
### description
Per-capita income, life expectancy, population and regional grouping. Dataset does not specify 
    the reference year for the data. Gapminder historical data is subject to revisions.

    Gapminder (v30, 2023) defines per-capita income as follows:
    >"This is real GDP per capita (gross domestic product per person adjusted for inflation) 
    >converted to international dollars using purchasing power parity rates. An international dollar 
    >has the same purchasing power over GDP as the U.S. dollar has in the United States."

### schema
    
| name       | type    |
|:-----------|:--------|
| country    | string  |
| income     | integer |
| health     | number  |
| population | integer |
| region     | string  |
### sources
| title                         | path                                                                                                                 |
|:------------------------------|:---------------------------------------------------------------------------------------------------------------------|
| Gapminder Foundation          | https://www.gapminder.org                                                                                            |
| Gapminder GDP Per Capita Data | https://docs.google.com/spreadsheets/d/1i5AEui3WZNZqh7MQ4AKkJuCz4rRxGR_pw_9gtbcBOqQ/edit?gid=501532268#gid=501532268 |
### licenses
| title                                          | path                                     |
|:-----------------------------------------------|:-----------------------------------------|
| Creative Commons Attribution 4.0 International | https://www.gapminder.org/free-material/ |
## `gapminder.json`
### path
gapminder.json
### description
This dataset combines key demographic indicators (life expectancy at birth, 
    population, and fertility rate measured as babies per woman) for various countries from 1955 
    to 2005 at 5-year intervals. It also includes a 'cluster' column, a categorical variable 
    grouping countries. Gapminder's data documentation notes that its philosophy is to fill data 
    gaps with estimates and use current geographic boundaries for historical data. Gapminder 
    states that it aims to "show people the big picture" rather than support detailed numeric 
    analysis.

    Notes:
    1. Country Selection: The set of countries in this file matches the version of this dataset 
       originally added to this collection in 2015. The specific criteria for country selection 
       in that version are not known. Data for Aruba are no longer available in the new version. 
       Hong Kong has been revised to Hong Kong, China in the new version.

    2. Data Precision: The precision of float values may have changed from the original version. 
       These changes reflect the most recent source data used for each indicator.

    3. Regional Groupings: The 'cluster' column represents a regional mapping of countries 
       corresponding to the 'six_regions' schema in Gapminder's Data Geographies dataset. To 
       preserve continuity with previous versions of this dataset, we have retained the column 
       name 'cluster' instead of renaming it to 'six_regions'. The six regions represented are: 
       `0: south_asia, 1: europe_central_asia, 2: sub_saharan_africa, 3: america, 4: east_asia_pacific, 5: middle_east_north_africa`.
### schema
    
| name        | type    | description                                                      |
|:------------|:--------|:-----------------------------------------------------------------|
| year        | integer | Years from 1955 to 2005 at 5-year intervals                      |
| country     | string  | Name of the country                                              |
| cluster     | integer | A categorical variable (values 0-5) grouping countries by region |
| pop         | integer | Population of the country                                        |
| life_expect | number  | Life expectancy in years                                         |
| fertility   | number  | Fertility rate (average number of children per woman             |
### sources
| title                                                          | path                                                                                                                   |   version |
|:---------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|----------:|
| Gapminder Foundation - Life Expectancy (Data)                  | https://docs.google.com/spreadsheets/d/1RehxZjXd7_rG8v2pJYV6aY0J3LAsgUPDQnbY4dRdiSs/edit?gid=176703676#gid=176703676   |        14 |
| Gapminder Foundatio - Life Expectancy (Documentation)          | https://www.gapminder.org/data/documentation/gd004/                                                                    |           |
| Gapminder Foundation - Population (Data)                       | https://docs.google.com/spreadsheets/d/1c1luQNdpH90tNbMIeU7jD__59wQ0bdIGRFpbMm8ZBTk/edit?gid=176703676#gid=176703676   |         7 |
| Gapminder Foundation - Population (Documentation)              | https://www.gapminder.org/data/documentation/gd003/                                                                    |           |
| Gapminder Foundation - Fertility (Data)                        | https://docs.google.com/spreadsheets/d/1aLtIpAWvDGGa9k2XXEz6hZugWn0wCd5nmzaRPPjbYNA/edit?gid=176703676#gid=176703676   |        14 |
| Gapminder Foundation - Fertility Documentation (Documentation) | https://www.gapminder.org/data/documentation/gd008/                                                                    |           |
| Gapminder Foundation - Data Geographies (Data)                 | https://docs.google.com/spreadsheets/d/1qHalit8sXC0R8oVXibc2wa2gY7bkwGzOybEMTWp-08o/edit?gid=1597424158#gid=1597424158 |         2 |
| Gapminder Foundation - Data Geographies (Documentation)        | https://www.gapminder.org/data/geo/                                                                                    |           |
| Gapminder Data Documentation                                   | https://www.gapminder.org/data/documentation/                                                                          |           |
## `gimp.png`
### path
gimp.png
### description
Application icons from open-source software projects.
## `github.csv`
### path
github.csv
### description
Generated using `/scripts/github.py`.
### schema
    
| name   | type    |
|:-------|:--------|
| time   | string  |
| count  | integer |
## `global-temp.csv`
### path
global-temp.csv
### description
Combined Land-Surface Air and Sea-Surface Water Temperature Anomalies (Land-Ocean Temperature Index, L-OTI), 1880-2023.
### schema
    
| name   | type    |
|:-------|:--------|
| year   | integer |
| temp   | number  |
### sources
| title                                    | path                                |
|:-----------------------------------------|:------------------------------------|
| NASA Goddard Institute for Space Studies | https://data.giss.nasa.gov/gistemp/ |
## `income.json`
### path
income.json
### schema
    
| name   | type    |
|:-------|:--------|
| name   | string  |
| region | string  |
| id     | integer |
| pct    | number  |
| total  | integer |
| group  | string  |
## `iowa-electricity.csv`
### path
iowa-electricity.csv
### description
The state of Iowa has dramatically increased its production of renewable 
    wind power in recent years. This file contains the annual net generation of electricity in 
    the state by source in thousand megawatthours. U.S. EIA data downloaded on May 6, 2018. 
    It is useful for illustrating stacked area charts.
### schema
    
| name           | type    |
|:---------------|:--------|
| year           | date    |
| source         | string  |
| net_generation | integer |
### sources
| title                                  | path                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|:---------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| U.S. Energy Information Administration | https://www.eia.gov/beta/electricity/data/browser/#/topic/0?agg=2,0,1&fuel=vvg&geo=00000g&sec=g&linechart=ELEC.GEN.OTH-IA-99.A~ELEC.GEN.COW-IA-99.A~ELEC.GEN.PEL-IA-99.A~ELEC.GEN.PC-IA-99.A~ELEC.GEN.NG-IA-99.A~~ELEC.GEN.NUC-IA-99.A~ELEC.GEN.HYC-IA-99.A~ELEC.GEN.AOR-IA-99.A~ELEC.GEN.HPS-IA-99.A~&columnchart=ELEC.GEN.ALL-IA-99.A&map=ELEC.GEN.ALL-IA-99.A&freq=A&start=2001&end=2017&ctype=linechart&ltype=pin&tab=overview&maptype=0&rse=0&pin= |
## `jobs.json`
### path
jobs.json
### description
U.S. census data on [occupations](https://usa.ipums.org/usa-action/variables/OCC1950#codes_section) by sex and year across decades between 1850 and 2000. The dataset was obtained from IPUMS USA, which "collects, preserves and harmonizes U.S. census microdata" from as early as 1790.

    Originally created for a 2006 data visualization project called *sense.us* by IBM Research (Jeff Heer, Martin Wattenberg and Fernanda Viégas), described [here](https://homes.cs.washington.edu/~jheer/files/bdata_ch12.pdf). 
    The dataset is also referenced in this vega [example](https://vega.github.io/vega/examples/job-voyager/).

    Data is based on a tabulation of the [OCC1950](https://usa.ipums.org/usa-action/variables/OCC1950) variable by sex across IPUMS USA samples. The dataset appears to be derived from Version 6.0 (2015) of IPUMS USA, according to 2024 correspondence with the IPUMS Project. IPUMS has made improvements to occupation coding since version 6, particularly for 19th-century samples, which may result in discrepancies between this dataset and current IPUMS data. Details on data revisions are available [here](https://usa.ipums.org/usa-action/revisions).

    IPUMS USA confirmed in 2024 correspondence that hosting this dataset on vega-datasets is permissible, stating:
    >We're excited to hear that this dataset made its way to this repository and is being used by students for data visualization. We allow for these types of redistributions of summary data so long as the underlying microdata records are not shared.

    This dataset contains only summary statistics and does not include any underlying microdata records.

    1. This dataset represents summary data. The underlying microdata records are not included.
    2. Users attempting to replicate or extend this data should use the [PERWT](https://usa.ipums.org/usa-action/variables/PERWT#description_section) 
    (person weight) variable as an expansion factor when working with IPUMS USA extracts.
    3. Due to coding revisions, figures for earlier years (particularly 19th century) may not match current IPUMS USA data exactly.

    When using this dataset, please refer to IPUMS USA [terms of use](https://usa.ipums.org/usa/terms.shtml).
    The organization requests use of the following citation for this json file:

    Steven Ruggles, Katie Genadek, Ronald Goeken, Josiah Grover, and Matthew Sobek. Integrated Public Use Microdata Series: Version 6.0. Minneapolis: University of Minnesota, 2015. http://doi.org/10.18128/D010.V6.0

### schema
    
| name   | type    | description                                   |
|:-------|:--------|:----------------------------------------------|
| job    | string  | The occupation title                          |
| sex    | string  | Sex (men/women)                               |
| year   | integer | Census year                                   |
| count  | integer | Number of individuals in the occupation       |
| perc   | number  | Percentage of the workforce in the occupation |
### sources
| title     | path                       |   version |
|:----------|:---------------------------|----------:|
| IPUMS USA | https://usa.ipums.org/usa/ |         6 |
## `la-riots.csv`
### path
la-riots.csv
### description
More than 60 people lost their lives amid the looting and fires that ravaged Los Angeles 
    for five days starting on April 29, 1992. This file contains metadata about each person, including the geographic 
    coordinates of their death. Compiled and published by the Los Angeles Times Data Desk.
### schema
    
| name         | type    |
|:-------------|:--------|
| first_name   | string  |
| last_name    | string  |
| age          | integer |
| gender       | string  |
| race         | string  |
| death_date   | date    |
| address      | string  |
| neighborhood | string  |
| type         | string  |
| longitude    | number  |
| latitude     | number  |
### sources
| title                                        | path                                             |
|:---------------------------------------------|:-------------------------------------------------|
| LA Riots Deaths, Los Angeles Times Data Desk | http://spreadsheets.latimes.com/la-riots-deaths/ |
## `londonboroughs.json`
### path
londonBoroughs.json
### description
Boundaries of London boroughs reprojected and simplified from `London_Borough_Excluding_MHW` shapefile. 
    Original data "contains National Statistics data © Crown copyright and database right (2015)" 
    and "Contains Ordnance Survey data © Crown copyright and database right [2015].
### sources
| title                                            | path                                                                     |
|:-------------------------------------------------|:-------------------------------------------------------------------------|
| Statistical GIS Boundary Files, London Datastore | https://data.london.gov.uk/dataset/statistical-gis-boundary-files-london |
## `londoncentroids.json`
### path
londonCentroids.json
### description
Calculated from `londonBoroughs.json` using [`d3.geoCentroid`](https://d3js.org/d3-geo/math#geoCentroid).
### schema
    
| name   | type   |
|:-------|:-------|
| name   | string |
| cx     | number |
| cy     | number |
## `londontubelines.json`
### path
londonTubeLines.json
### description
Selected rail lines simplified from source.
### sources
| title            | path                                                 |
|:-----------------|:-----------------------------------------------------|
| London Tube Data | https://github.com/oobrien/vis/tree/master/tube/data |
## `lookup_groups.csv`
### path
lookup_groups.csv
### schema
    
| name   | type    |
|:-------|:--------|
| group  | integer |
| person | string  |
## `lookup_people.csv`
### path
lookup_people.csv
### schema
    
| name   | type    |
|:-------|:--------|
| name   | string  |
| age    | integer |
| height | integer |
## `miserables.json`
### path
miserables.json
## `monarchs.json`
### path
monarchs.json
### description
A chronological list of English and British monarchs from Elizabeth I through George IV.
    Each entry includes:

    The dataset contains two intentional inaccuracies to maintain compatibility with 
    the [Wheat and Wages](https://vega.github.io/vega/examples/wheat-and-wages/) example visualization:
    1. the start date for the reign of Elizabeth I is shown as 1565, instead of 1558;
    2. the end date for the reign of George IV is shown as 1820, instead of 1830.
    These discrepancies align the `monarchs.json` dataset with the start and end dates of the `wheat.json` dataset used i the visualization.
    The entry "W&M" represents the joint reign of William III and Mary II. While the dataset shows their reign as 1689-1702, 
    the official Web site of the British royal family indicates that Mary II's reign ended in 1694, though William III continued to rule until 1702.
    The `commonwealth` field is used to flag the period from 1649 to 1660, which includes the Commonwealth of England, the Protectorate, 
    and the period leading to the Restoration. While historically more accurate to call this the "interregnum," the field name of `commonwealth` 
    from the original dataset is retained for backwards compatibility.
    The dataset was revised in Aug. 2024. James II's reign now ends in 1688 (previously 1689).
    Source data has been verified against the kings & queens and interregnum pages of the official website of the British royal family (retrieved in Aug. 2024).
    Content on the site is protected by Crown Copyright. 
    Under the [UK Government Licensing Framework](https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/), most 
    Crown copyright information is available under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
### schema
    
| name   | type    | description                                                                                                 |
|:-------|:--------|:------------------------------------------------------------------------------------------------------------|
| name   | string  | The ruler's name or identifier (e.g., "W&M" for William and Mary, "Cromwell" for the period of interregnum) |
| start  | integer | The year their rule began                                                                                   |
| end    | integer | The year their rule ended                                                                                   |
| index  | integer | A zero-based sequential number assigned to each entry, representing the chronological order of rulers       |
### sources
| title                             | path                                       |
|:----------------------------------|:-------------------------------------------|
| The Royal Family - Kings & Queens | https://www.royal.uk/kings-and-queens-1066 |
| The Royal Family - Interregnum    | https://www.royal.uk/interregnum-1649-1660 |
## `movies.json`
### path
movies.json
### description
The dataset has well known and intentionally included errors. 
    This dataset is provided for instructional purposes, including the need to reckon with dirty data.
### schema
    
| name                   | type    |
|:-----------------------|:--------|
| Title                  | string  |
| US Gross               | integer |
| Worldwide Gross        | integer |
| US DVD Sales           | integer |
| Production Budget      | integer |
| Release Date           | string  |
| MPAA Rating            | string  |
| Running Time min       | integer |
| Distributor            | string  |
| Source                 | string  |
| Major Genre            | string  |
| Creative Type          | string  |
| Director               | string  |
| Rotten Tomatoes Rating | integer |
| IMDB Rating            | number  |
| IMDB Votes             | integer |
## `normal-2d.json`
### path
normal-2d.json
### schema
    
| name   | type   |
|:-------|:-------|
| u      | number |
| v      | number |
## `obesity.json`
### path
obesity.json
### schema
    
| name   | type    |
|:-------|:--------|
| id     | integer |
| rate   | number  |
| state  | string  |
## `ohlc.json`
### path
ohlc.json
### description
This dataset contains the performance of the Chicago Board Options Exchange 
    [Volatility Index](https://en.wikipedia.org/wiki/VIX) ([VIX](https://finance.yahoo.com/chart/
    %5EVIX#overview)) in the summer of 2009.
### schema
    
| name   | type   |
|:-------|:-------|
| date   | date   |
| open   | number |
| high   | number |
| low    | number |
| close  | number |
| signal | string |
| ret    | number |
### sources
| title                  | path                                   |
|:-----------------------|:---------------------------------------|
| Yahoo Finance VIX Data | https://finance.yahoo.com/chart/%5EVIX |
## `penguins.json`
### path
penguins.json
### description
Palmer Archipelago (Antarctica) penguin data collected and made available by 
    [Dr. Kristen Gorman](https://www.uaf.edu/cfos/people/faculty/detail/kristen-gorman.php) 
    and the Palmer Station, Antarctica LTER, a member of the [Long Term Ecological Research 
    Network](https://lternet.edu/).
### schema
    
| name                | type    |
|:--------------------|:--------|
| Species             | string  |
| Island              | string  |
| Beak Length (mm)    | number  |
| Beak Depth (mm)     | number  |
| Flipper Length (mm) | integer |
| Body Mass (g)       | integer |
| Sex                 | string  |
### sources
| title                               | path                                     |
|:------------------------------------|:-----------------------------------------|
| Palmer Station Antarctica LTER      | https://pal.lternet.edu/                 |
| Allison Horst's Penguins Repository | https://github.com/allisonhorst/penguins |
## `platformer-terrain.json`
### path
platformer-terrain.json
### description
Assets from the video game Celeste.
### schema
    
| name       | type    |
|:-----------|:--------|
| x          | integer |
| y          | integer |
| lumosity   | number  |
| saturation | integer |
| name       | string  |
| id         | string  |
| color      | string  |
| key        | string  |
### sources
| title        | path                        |
|:-------------|:----------------------------|
| Celeste Game | http://www.celestegame.com/ |
## `points.json`
### path
points.json
### schema
    
| name   | type   |
|:-------|:-------|
| x      | number |
| y      | number |
## `political-contributions.json`
### path
political-contributions.json
### description
Summary financial information on contributions to candidates for U.S. 
    elections. An updated version of this datset is available from the "all candidates" files 
    (in pipe-delimited format) on the bulk data download page of the U.S. Federal Election 
    Commission, or, alternatively, via OpenFEC. Information on each of the 25 columns is 
    available from the [FEC All Candidates File Description](https://www.fec.gov/campaign-finance-data/all-candidates-file-description/).
    The sample dataset in `political-contributions.json` contains 58 records with dates from 2015.

    FEC data is subject to the commission's:
    - [Sale or Use Policy](https://www.fec.gov/updates/sale-or-use-contributor-information/)
    - [Privacy and Security Policy](https://www.fec.gov/about/privacy-and-security-policy/)
    - [Acceptable Use Policy](https://github.com/fecgov/FEC/blob/master/ACCEPTABLE-USE-POLICY.md)

    Additionally, the FEC's Github [repository](https://github.com/fecgov/FEC) states:
    > This project is in the public domain within the United States, and we waive worldwide 
    > copyright and related rights through [CC0 universal public domain](https://creativecommons.org/publicdomain/zero/1.0/)
    > dedication. Read more on our license page.
    > A few restrictions limit the way you can use FEC data. For example, you can't use 
    > contributor lists for commercial purposes or to solicit donations. Learn more on 
    > [FEC.gov](https://www.fec.gov/).
### schema
    
| name                                          | type    |
|:----------------------------------------------|:--------|
| Candidate_Identification                      | string  |
| Candidate_Name                                | string  |
| Incumbent_Challenger_Status                   | string  |
| Party_Code                                    | integer |
| Party_Affiliation                             | string  |
| Total_Receipts                                | number  |
| Transfers_from_Authorized_Committees          | integer |
| Total_Disbursements                           | number  |
| Transfers_to_Authorized_Committees            | number  |
| Beginning_Cash                                | number  |
| Ending_Cash                                   | number  |
| Contributions_from_Candidate                  | number  |
| Loans_from_Candidate                          | integer |
| Other_Loans                                   | integer |
| Candidate_Loan_Repayments                     | number  |
| Other_Loan_Repayments                         | integer |
| Debts_Owed_By                                 | number  |
| Total_Individual_Contributions                | integer |
| Candidate_State                               | string  |
| Candidate_District                            | integer |
| Contributions_from_Other_Political_Committees | integer |
| Contributions_from_Party_Committees           | integer |
| Coverage_End_Date                             | string  |
| Refunds_to_Individuals                        | integer |
| Refunds_to_Committees                         | integer |
### sources
| title                                 | path                                                |
|:--------------------------------------|:----------------------------------------------------|
| Federal Election Commission Bulk Data | https://www.fec.gov/data/browse-data/?tab=bulk-data |
| OpenFEC API                           | https://api.open.fec.gov/developers/                |
## `population.json`
### path
population.json
### description
United States population statistics by sex and age group across decades between 1850 and 2000. 
    The dataset was obtained from IPUMS USA, which "collects, preserves and harmonizes U.S. census 
    microdata" from as early as 1790.

    IPUMS updates and revises datasets over time, which may result in discrepancies between this 
    dataset and current IPUMS data. Details on data revisions are available here.

    When using this dataset, please refer to IPUMS USA terms of use. The organization requests the 
    use of the following citation for this json file:
    Steven Ruggles, Katie Genadek, Ronald Goeken, Josiah Grover, and Matthew Sobek. Integrated 
    Public Use Microdata Series: Version 6.0. Minneapolis: University of Minnesota, 2015. 
    http://doi.org/10.18128/D010.V6.0

### schema
    
| name   | type    | description                                                         |
|:-------|:--------|:--------------------------------------------------------------------|
| year   | integer | Four-digit year of the survey                                       |
| age    | integer | Age group in 5-year intervals (0=0-4, 5=5-9, 10=10-14, ..., 90=90+) |
| sex    | integer | Sex (1=men, 2=women)                                                |
| people | integer | Number of individuals (IPUMS PERWT)                                 |
### sources
| title     | path                       |
|:----------|:---------------------------|
| IPUMS USA | https://usa.ipums.org/usa/ |
## `population_engineers_hurricanes.csv`
### path
population_engineers_hurricanes.csv
### description
Per-state data on population, number of engineers, and hurricanes. Used in Vega-Lite example,
    [Three Choropleths Representing Disjoint DAta from the Same Table](https://vega.github.io/vega-lite/examples/geo_repeat.html)
### schema
    
| name       | type    |
|:-----------|:--------|
| state      | string  |
| id         | integer |
| population | integer |
| engineers  | number  |
| hurricanes | integer |
### sources
| title                              | path                                                                                                              |
|:-----------------------------------|:------------------------------------------------------------------------------------------------------------------|
| Bureau of Labor Statistics         | https://www.bls.gov/oes/tables.htm                                                                                |
| American Community Survey          | https://factfinder.census.gov/faces/tableservices/jsf/pages/productview.xhtml?pid=ACS_07_3YR_S1901&prodType=table |
| NOAA National Climatic Data Center | https://www.ncdc.noaa.gov/cdo-web/datatools/records                                                               |
## `seattle-weather-hourly-normals.csv`
### path
seattle-weather-hourly-normals.csv
### description
Hourly weather normals with metric units. The 1981-2010 Climate Normals are 
    NCDC's three-decade averages of climatological variables, including temperature and 
    precipitation. Learn more in the [documentation](https://www1.ncdc.noaa.gov/pub/data/cdo/documentation/NORMAL_HLY_documentation.pdf).
    We only included temperature, wind, and pressure 
    and updated the format to be easier to parse.
### schema
    
| name        | type     |
|:------------|:---------|
| date        | datetime |
| pressure    | number   |
| temperature | number   |
| wind        | number   |
### sources
| title                                     | path                                                |
|:------------------------------------------|:----------------------------------------------------|
| NOAA National Climatic Data Center (NCDC) | https://www.ncdc.noaa.gov/cdo-web/datatools/normals |
## `seattle-weather.csv`
### path
seattle-weather.csv
### description
Daily weather records with metric units. Transformed using `/scripts/weather.py`. 
    The categorical "weather" field is synthesized from multiple fields in the original dataset. 
    This data is intended for instructional purposes.
### schema
    
| name          | type   |
|:--------------|:-------|
| date          | date   |
| precipitation | number |
| temp_max      | number |
| temp_min      | number |
| wind          | number |
| weather       | string |
### sources
| title                              | path                                                |
|:-----------------------------------|:----------------------------------------------------|
| NOAA National Climatic Data Center | https://www.ncdc.noaa.gov/cdo-web/datatools/records |
## `sp500-2000.csv`
### path
sp500-2000.csv
### description
S&amp;P 500 index values from 2000 to 2020.
### schema
    
| name     | type    |
|:---------|:--------|
| date     | date    |
| open     | number  |
| high     | number  |
| low      | number  |
| close    | number  |
| adjclose | number  |
| volume   | integer |
### sources
| title         | path                                            |
|:--------------|:------------------------------------------------|
| Yahoo Finance | https://finance.yahoo.com/quote/%5EDJI/history/ |
## `sp500.csv`
### path
sp500.csv
### schema
    
| name   | type   |
|:-------|:-------|
| date   | string |
| price  | number |
## `stocks.csv`
### path
stocks.csv
### schema
    
| name   | type   |
|:-------|:-------|
| symbol | string |
| date   | string |
| price  | number |
## `udistrict.json`
### path
udistrict.json
### schema
    
| name   | type   |
|:-------|:-------|
| key    | string |
| lat    | number |
## `unemployment-across-industries.json`
### path
unemployment-across-industries.json
### description
Industry-level unemployment statistics from the Current Population Survey 
    (CPS), published monthly by the U.S. Bureau of Labor Statistics. Includes unemployed persons 
    and unemployment rate across 11 private industries, as well as agricultural, government, and 
    self-employed workers. Covers January 2000 through February 2010. Industry classification 
    follows format of CPS Table A-31.

    The dataset can be replicated using the BLS API. For more, see the `scripts` folder of this 
    repository.

    The BLS Web site states:
    > "Users of the public API should cite the date that data were accessed or retrieved using 
    > the API. Users must clearly state that "BLS.gov cannot vouch for the data or analyses 
    > derived from these data after the data have been retrieved from BLS.gov." The BLS.gov logo 
    > may not be used by persons who are not BLS employees or on products (including web pages) 
    > that are not BLS-sponsored."

    See full BLS [terms of service](https://www.bls.gov/developers/termsOfService.htm).
### schema
    
| name   | type     | description                                                       |
|:-------|:---------|:------------------------------------------------------------------|
| series | string   | Industry name                                                     |
| year   | integer  | Year (2000-2010)                                                  |
| month  | integer  | Month (1-12)                                                      |
| count  | integer  | Number of unemployed persons (in thousands)                       |
| rate   | number   | Unemployment rate (percentage)                                    |
| date   | datetime | ISO 8601-formatted date string (e.g., "2000-01-01T08:00:00.000Z") |
### sources
| title                                        | path                                             |
|:---------------------------------------------|:-------------------------------------------------|
| U.S. Census Bureau Current Population Survey | https://www.census.gov/programs-surveys/cps.html |
| BLS LAUS Data Tools                          | https://www.bls.gov/lau/data.htm                 |
| Bureau of Labor Statistics Table A-31        | https://www.bls.gov/web/empsit/cpseea31.htm      |
## `unemployment.tsv`
### path
unemployment.tsv
### description
This dataset contains county-level unemployment rates in the United States, with data generally
    consistent with levels reported in 2009. The dataset is structured as tab-separated values.
    The unemployment rate represents the number of unemployed persons as a percentage of the labor
    force. According to the Bureau of Labor Statistics (BLS) glossary:

    Unemployed persons (Current Population Survey) [are] persons aged 16 years and older who had
    no employment during the reference week, were available for work, except for temporary
    illness, and had made specific efforts to find employment sometime during the 4-week period
    ending with the reference week. Persons who were waiting to be recalled to a job from which
    they had been laid off need not have been looking for work to be classified as unemployed.

    This dataset is derived from the [Local Area Unemployment Statistics (LAUS)](https://www.bls.gov/lau/) program, 
    a federal-state cooperative effort overseen by the Bureau of Labor Statistics (BLS). 
    The LAUS program produces monthly and annual employment, unemployment, and labor force data for census regions and divisions,
    states, counties, metropolitan areas, and many cities and towns.

    For the most up-to-date LAUS data:
    1. **Monthly and Annual Data Downloads**:
    - Visit the [LAUS Data Tools](https://www.bls.gov/lau/data.htm) page for [monthly](https://www.bls.gov/lau/tables.htm#mcounty) 
    and [annual](https://www.bls.gov/lau/tables.htm#cntyaa) county data.
    2. **BLS Public Data API**:
    - The BLS provides an API for developers to access various datasets, including LAUS data.
    - To use the API for LAUS data, refer to the [LAUS Series ID Formats](https://www.bls.gov/help/hlpforma.htm#LA) to construct your query.
    - API documentation and examples are available on the BLS Developers page.

    When using BLS public data API and datasets, users should adhere to the [BLS Terms of Service](https://www.bls.gov/developers/termsOfService.htm).
### schema
    
| name   | type    | description                             |
|:-------|:--------|:----------------------------------------|
| id     | integer | The combined state and county FIPS code |
| rate   | number  | The unemployment rate for the county    |
### sources
| title                   | path                                      |
|:------------------------|:------------------------------------------|
| BLS Developers API      | https://www.bls.gov/developers/           |
| BLS Handbook of Methods | https://www.bls.gov/opub/hom/lau/home.htm |
## `uniform-2d.json`
### path
uniform-2d.json
### schema
    
| name   | type   |
|:-------|:-------|
| u      | number |
| v      | number |
## `us-10m.json`
### path
us-10m.json
## `us-employment.csv`
### path
us-employment.csv
### description
In the mid 2000s the global economy was hit by a crippling recession. One result: Massive job 
    losses across the United States. The downturn in employment, and the slow recovery in hiring that 
    followed, was tracked each month by the Current Employment Statistics program at the U.S. Bureau 
    of Labor Statistics.

    This file contains the monthly employment total in a variety of job categories from January 2006 
    through December 2015. The numbers are seasonally adjusted and reported in thousands. The data 
    were downloaded on Nov. 11, 2018, and reformatted for use in this library.

    Totals are included for the [22 "supersectors"](https://download.bls.gov/pub/time.series/ce/ce.supersector)
    tracked by the BLS. The "nonfarm" total is the category typically used by 
    economists and journalists as a stand-in for the country's employment total.

    A calculated "nonfarm_change" column has been appended with the month-to-month change in that 
    supersector's employment. It is useful for illustrating how to make bar charts that report both 
    negative and positive values.

### schema
    
| name                               | type    |
|:-----------------------------------|:--------|
| month                              | date    |
| nonfarm                            | integer |
| private                            | integer |
| goods_producing                    | integer |
| service_providing                  | integer |
| private_service_providing          | integer |
| mining_and_logging                 | integer |
| construction                       | integer |
| manufacturing                      | integer |
| durable_goods                      | integer |
| nondurable_goods                   | integer |
| trade_transportation_utilties      | integer |
| wholesale_trade                    | number  |
| retail_trade                       | number  |
| transportation_and_warehousing     | number  |
| utilities                          | number  |
| information                        | integer |
| financial_activities               | integer |
| professional_and_business_services | integer |
| education_and_health_services      | integer |
| leisure_and_hospitality            | integer |
| other_services                     | integer |
| government                         | integer |
| nonfarm_change                     | integer |
### sources
| title                                                         | path                     |
|:--------------------------------------------------------------|:-------------------------|
| U.S. Bureau of Labor Statistics Current Employment Statistics | https://www.bls.gov/ces/ |
## `us-state-capitals.json`
### path
us-state-capitals.json
### schema
    
| name   | type   |
|:-------|:-------|
| lon    | number |
| lat    | number |
| state  | string |
| city   | string |
## `volcano.json`
### path
volcano.json
### description
Maunga Whau (Mt Eden) is one of about 50 volcanos in the Auckland volcanic field. 
    This data set gives topographic information for Maunga Whau on a 10m by 10m grid. Digitized from a 
    topographic map by Ross Ihaka, adapted from R datasets. These data should not be regarded as accurate.
### sources
| title      | path                                                                       |
|:-----------|:---------------------------------------------------------------------------|
| R Datasets | https://stat.ethz.ch/R-manual/R-patched/library/datasets/html/volcano.html |
## `weather.csv`
### path
weather.csv
### description
NOAA data transformed using `/scripts/weather.py`. Categorical "weather" field synthesized 
    from multiple fields in the original dataset. This data is intended for instructional purposes.
### schema
    
| name          | type   |
|:--------------|:-------|
| location      | string |
| date          | date   |
| precipitation | number |
| temp_max      | number |
| temp_min      | number |
| wind          | number |
| weather       | string |
### sources
| title                    | path                                                   |
|:-------------------------|:-------------------------------------------------------|
| NOAA Climate Data Online | http://www.ncdc.noaa.gov/cdo-web/datatools/findstation |
## `weather.json`
### path
weather.json
### description
Instructional dataset showing actual and predicted temperature data.
## `wheat.json`
### path
wheat.json
### description
In an 1822 letter to Parliament, [William Playfair](https://en.wikipedia.org/wiki/William_Playfair),
    a Scottish engineer who is often credited as the founder of statistical graphics, 
    published an elegant chart on the price of wheat. It plots 250 years of prices alongside 
    weekly wages and the reigning monarch. He intended to demonstrate that "never at any former period 
    was wheat so cheap, in proportion to mechanical labour, as it is at the present time."
### schema
    
| name   | type    |
|:-------|:--------|
| year   | integer |
| wheat  | number  |
| wages  | number  |
### sources
| title               | path                                                                  |
|:--------------------|:----------------------------------------------------------------------|
| 1822 Playfair Chart | http://dh101.humanities.ucla.edu/wp-content/uploads/2014/08/Vis_2.jpg |
## `windvectors.csv`
### path
windvectors.csv
### description
Simulated wind patterns over northwestern Europe.
### schema
    
| name      | type    |
|:----------|:--------|
| longitude | number  |
| latitude  | number  |
| dir       | integer |
| dirCat    | integer |
| speed     | number  |
## `world-110m.json`
### path
world-110m.json
## `zipcodes.csv`
### path
zipcodes.csv
### description
GeoNames.org
### schema
    
| name      | type    |
|:----------|:--------|
| zip_code  | integer |
| latitude  | number  |
| longitude | number  |
| city      | string  |
| state     | string  |
| county    | string  |
### sources
| title    | path                     |
|:---------|:-------------------------|
| GeoNames | https://www.geonames.org |