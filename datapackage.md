# vega-datasets
`3.2.1` | [GitHub](git+http://github.com/vega/vega-datasets.git) | 2026-02-06 03:18:08 [UTC]

Common repository for example datasets used by Vega related projects. 
BSD-3-Clause license applies only to package code and infrastructure. Users should verify their use of datasets 
complies with the license terms of the original sources. Dataset license information, where included, 
is a reference starting point only and is provided without any warranty of accuracy or completeness.


## licenses
| name         | path                                        | title                    |
|:-------------|:--------------------------------------------|:-------------------------|
| BSD-3-Clause | https://opensource.org/license/bsd-3-clause | The 3-Clause BSD License |

## contributors
| title                      | path                                                      |
|:---------------------------|:----------------------------------------------------------|
| Vega                       | https://vega.github.io                                    |
| vega-datasets contributors | https://github.com/vega/vega-datasets/graphs/contributors |

# resources
## `icon_7zip`
### path
7zip.png
### description
Application icon from open-source software project. Used in [Image-based Scatter Plot example](https://vega.github.io/vega-lite/examples/scatter_image.html).
### sources
| title   | path                   |
|:--------|:-----------------------|
| 7-Zip   | https://www.7-zip.org/ |
### licenses
| name     | title                             | path                              |
|:---------|:----------------------------------|:----------------------------------|
| LGPL-2.1 | GNU Lesser General Public License | https://www.7-zip.org/license.txt |
## `airports`
### path
airports.csv
### description
Airports in the United States and its territories, including major commercial, regional, 
and municipal airports. Contains information about each airport's location (latitude/longitude 
coordinates), identification codes, name, city, state, and country. While the exact generation 
source of this file is unknown, this data is consistent with files provided on a monthly 
frequency by the FAA's [National Airspace System Resource](https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/).
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
### sources
| title                           | path                                                                             |
|:--------------------------------|:---------------------------------------------------------------------------------|
| Federal Aviation Administration | https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/ |
### licenses
| name       | title                                |
|:-----------|:-------------------------------------|
| other-open | https://www.usa.gov/government-works |
## `annual_precip`
### path
annual-precip.json
### description
A raster grid of global annual precipitation for the year 2016 at a resolution 1 degree of lon/lat per cell.
### sources
| title                             | path                                                                    |
|:----------------------------------|:------------------------------------------------------------------------|
| Climate Forecast System Version 2 | https://www.cpc.ncep.noaa.gov/products/people/wwang/cfsv2_fcst_history/ |
### licenses
| name     | title         | path                                |
|:---------|:--------------|:------------------------------------|
| other-pd | Public Domain | https://www.weather.gov/disclaimer/ |
## `anscombe`
### path
anscombe.json
### description
Eleven (x,y) pairs of numbers, with means x̄=9.0 and ȳ=7.5, and identical linear regression 
lines (same slope and intercept) and correlation coefficients (approximately 0.816). When plotted, reveals starkly 
different patterns: one shows a linear relationship, another a non-linear curve, the third a near-perfect linear 
relationship disrupted by a single outlier, and the fourth a near-vertical line of points where a single outlier 
entirely dictates the regression.

In his 1973 paper "Graphs in Statistical Analysis" Yale Professor [Francis Anscombe](https://archives.yale.edu/repositories/12/resources/3711) uses these four datasets 
to argue that visualization is essential to good statistical work, not merely an optional supplement. This was a radical position at a 
time when most statistical analysis was done through batch processing on mainframes with no graphical output. Serves 
as a powerful demonstration that identical summary statistics can mask radically different patterns in data, making the case that 
statistical analysis should combine both numerical calculations and graphical examination.  

### schema
    
| name   | type    |
|:-------|:--------|
| Series | string  |
| X      | integer |
| Y      | number  |
### sources
| title                                                                                           | path                                                    |
|:------------------------------------------------------------------------------------------------|:--------------------------------------------------------|
| Anscombe's quartet (Wikipedia)                                                                  | https://en.wikipedia.org/wiki/Anscombe%27s_quartet#Data |
| Anscombe, F. J. (1973). Graphs in Statistical Analysis. The American Statistician, 27(1):17-21. | https://www.jstor.org/stable/2682899                    |
## `barley`
### path
barley.json
### description
Yields of barley varieties from experiments conducted by the Minnesota Agricultural
Experiment Station (MAES) across six sites in Minnesota. The USDA Technical Bulletin No. 735
(December 1940) republished these yields data with explicit credit to MAES as the source.

It was analyzed by agronomists F.R. Immer, H.K. Hayes, and L. Powers in the 1934 paper "Statistical Determination of Barley Varietal Adaption".

R.A. Fisher popularized its use in the field of statistics when he included it in his book "The Design of Experiments".

Since then it has been used to demonstrate new visualization techniques, including the trellis charts developed by Richard Becker, William Cleveland and others in the 1990s.

### schema
    
| name    | type    |
|:--------|:--------|
| yield   | number  |
| variety | string  |
| year    | integer |
| site    | string  |
### sources
| title                                                                                                                                                                      | path                                                    |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------|
| The Design of Experiments Reference                                                                                                                                        | https://en.wikipedia.org/wiki/The_Design_of_Experiments |
| Wiebe, G. A., Reinbach-Welch, L., Cowan, P. R. (1940). Yields of Barley Varieties in the United States and Canada, 1932-36. United States: U.S. Department of Agriculture. | https://books.google.com/books?id=OUfxLocnpKkC&pg=PA19  |
### licenses
| name         | title                                                                                       |
|:-------------|:--------------------------------------------------------------------------------------------|
| notspecified | Dataset collected by Minnesota Agricultural Experiment Station - license status unspecified |
## `birdstrikes`
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
### licenses
| name     | title                   | path                                      |
|:---------|:------------------------|:------------------------------------------|
| other-pd | U.S. Government Dataset | https://resources.data.gov/open-licenses/ |
## `budget`
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
### licenses
| name     | title                   | path                                      |
|:---------|:------------------------|:------------------------------------------|
| other-pd | U.S. Government Dataset | https://resources.data.gov/open-licenses/ |
## `budgets`
### path
budgets.json
### description
U.S. federal budget projections and actual outcomes from 1980 through 2010. Originally [analyzed](https://archive.nytimes.com/www.nytimes.com/interactive/2010/02/02/us/politics/20100201-budget-porcupine-graphic.html) by The New York Times in 2010. 
Reveals how budget forecasts made in any given year compared to what actually happened, 
with positive values indicating surpluses (briefly seen around 2000) and negative values 
representing deficits (reaching a particularly large value of -$1.78 trillion during the 2008-2009 financial crisis).
### schema
    
| name         | type    | description                                                           |
|:-------------|:--------|:----------------------------------------------------------------------|
| budgetYear   | integer | The year for which the budget outcome is being reported               |
| forecastYear | integer | The year for which the budget was forecast                            |
| value        | number  | The budget outcome or projection value (in trillions of 2010 dollars) |
### sources
| title                           | path                            |
|:--------------------------------|:--------------------------------|
| Office of Management and Budget | https://www.whitehouse.gov/omb/ |
### licenses
| name     | title                   | path                                      |
|:---------|:------------------------|:------------------------------------------|
| other-pd | U.S. Government Dataset | https://resources.data.gov/open-licenses/ |
## `burtin`
### path
burtin.json
### description
Compares the performance of three antibiotics against 16 different bacteria. Based on graphic designer 
Will Burtin's 1951 visualization of antibiotic effectiveness, originally published in Scope Magazine and
featured as an example in the Protovis project, a precursor to D3.js.

Numerical values represent the minimum inhibitory concentration (MIC) of each antibiotic, 
measured in units per milliliter, with lower values indicating higher antibiotic
effectiveness.

As noted in the Protovis example, "Recreating this display revealed some minor errors in the original: a missing grid line at 0.01 μg/ml, and an exaggeration of some values for penicillin".

The vega-datsets version is largely consistent with the Protovis version, with one correction (changing 'Brucella antracis' to the correct 'Bacillus anthracis') and the addition of a new column, 'Genus', to group related bacterial species together.

The caption of the original 1951 [visualization](https://graphicdesignarchives.org/wp-content/uploads/wmgda_8616c.jpg) 
reads as follows:

> #### Antibacterial ranges of Neomycin, Penicillin and Streptomycin
>
>
> The chart compares the in vitro sensitivities to neomycin of some of the common pathogens (gram+ in red and gram- in blue) with their sensitivities to penicillin, and streptomycin.
>
> The effectiveness of the antibiotics is expressed as the highest dilution in μ/ml. which inhibits the test organism.
>
> High dilutions are toward the periphery; consequently the length of the colored bar is proportional to the effectiveness.
>
> It is apparent that neomycin is especially effective against Staph. albus and aureus, Streph. fecalis, A. aerogenes, S. typhosa, E. coli, Ps. aeruginosa, Br. abortus, K. pneumoniae, Pr. vulgaris, S. schottmuelleri and M. tuberculosis.
>
> Unfortunately, some strains of proteus, pseudomonas and hemolytic streptococcus are resistant to neomycin, although the majority of these are sensitive to neomycin.
>
> It also inhibits actinomycetes, but is inactive against viruses and fungi. Its mode of action is not understood.

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
### licenses
| name         | title                      | path                                 |
|:-------------|:---------------------------|:-------------------------------------|
| BSD-3-Clause | BSD License (via Protovis) | https://mbostock.github.io/protovis/ |
## `cars`
### path
cars.json
### description
Collection of car specifications and performance metrics from various automobile manufacturers.
### schema
    
| name             | type    |
|:-----------------|:--------|
| Name             | string  |
| Miles_per_Gallon | number  |
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
### licenses
| name         | title                                                                         | path                                       |
|:-------------|:------------------------------------------------------------------------------|:-------------------------------------------|
| notspecified | The original was distributed in 1982 for educational and scientific purposes. | http://lib.stat.cmu.edu/datasets/cars.desc |
## `co2_concentration`
### path
co2-concentration.csv
### description
Atmospheric CO2 concentration measurements from Mauna Loa Observatory, Hawaii. 
Contains monthly readings from 1958-2020 with two key measurements:
1. CO2 concentrations in millionths of a [mole](https://en.wikipedia.org/wiki/Mole_(unit)) of CO2 
per mole of air (parts per million), reported on the 2012 
SIO manometric mole fraction scale
2. Seasonally adjusted values where a [4-harmonic fit](https://en.wikipedia.org/wiki/Harmonic_analysis) with linear gain factor 
has been subtracted to remove the quasi-regular seasonal cycle
Values are adjusted to 24:00 hours on the 15th of each month. 
Only includes rows with valid data.

### schema
    
| name         | type   |
|:-------------|:-------|
| Date         | date   |
| CO2          | number |
| adjusted CO2 | number |
### sources
| title               | path                                                                                                         |
|:--------------------|:-------------------------------------------------------------------------------------------------------------|
| Scripps CO2 Program | https://scrippsco2.ucsd.edu/data/atmospheric_co2/primary_mlo_co2_record                                      |
| In-situ CO2 Data    | https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/monthly/monthly_in_situ_co2_mlo.csv |
### licenses
| name      | title                            | path                                         |
|:----------|:---------------------------------|:---------------------------------------------|
| CC-BY-4.0 | Creative Commons Attribution 4.0 | https://creativecommons.org/licenses/by/4.0/ |
## `countries`
### path
countries.json
### description
Key demographic indicators (life expectancy at birth and fertility rate measured 
as babies per woman) for various countries from 1955 to 2000 at 5-year intervals. Includes both 
current values and adjacent time period values (previous and next) for each indicator. Gapminder's 
[data documentation](https://www.gapminder.org/data/documentation/) notes that its philosophy is to fill data gaps with 
estimates and use current geographic boundaries for historical data. Gapminder states that it 
aims to "show people the big picture" rather than support detailed numeric analysis.
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
| name      | title                                          | path                                     |
|:----------|:-----------------------------------------------|:-----------------------------------------|
| CC-BY-4.0 | Creative Commons Attribution 4.0 International | https://www.gapminder.org/free-material/ |
## `crimea`
### path
crimea.json
### description
Monthly mortality rates from British military hospitals during the Crimean War (1854-1856), which informed 
Florence Nightingale's groundbreaking work in public health. Nightingale credits Dr. William Farr for 
compiling the data from the 1858 [Medical and Surgical History of the British Army](http://resource.nlm.nih.gov/62510370R). Categorizes 
deaths into "zymotic" diseases (preventable infectious diseases), wounds/injuries, and other causes. 
Covering the period from April 1854 to March 1856, it includes monthly army strength 
alongside mortality figures. Transformed by Nightingale into her now-famous [polar area 
diagrams](https://iiif.lib.harvard.edu/manifests/view/drs:7420433$25i). 

The annual mortality rates plotted in the chart can be calculated using the formula 
> (Deaths &times; 1000 &times; 12) &divide; Army Size. 

As [The Lancet](https://pmc.ncbi.nlm.nih.gov/articles/PMC7252134/) argued in 2020, Nightingale's 
innovative visualizations proved that "far more men died of disease, infection, and exposure 
than in battle—a fact that shocked the British nation." Her work also vividly illustrated 
the dramatic impact of sanitary reforms, particularly in reducing preventable deaths.
### schema
    
| name      | type    | description                                                                                                                                                                                                                                                                             |
|:----------|:--------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| date      | date    | First day of each month during the observation period, in ISO 8601 format (YYYY-MM-DD)                                                                                                                                                                                                  |
| wounds    | integer | Deaths from "Wounds and Injuries" which comprised: Luxatio (dislocation), Sub-Luxatio (partial dislocation), Vulnus Sclopitorum (gunshot wounds), Vulnus Incisum (incised wounds), Contusio (bruising), Fractura (fractures), Ambustio (burns) and Concussio-Cerebri (brain concussion) |
| other     | integer | Deaths from All Other Causes                                                                                                                                                                                                                                                            |
| disease   | integer | Deaths from Zymotic Diseases (preventable infectious diseases)                                                                                                                                                                                                                          |
| army_size | integer | Estimated Average Monthly Strength of the Army                                                                                                                                                                                                                                          |
### sources
| title                                                                                                                                                                                                                                                                                                                                                                                            | path                                                     |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------|
| Nightingale, Florence. A contribution to the sanitary history of the British army during the late war with Russia. London : John W. Parker and Son, 1859. Table II. Table showing the Estimated Average Monthly Strength of the Army; and the Deaths and Annual Rate of Mortality per 1,000 in each month, from April 1854, to March 1856 (inclusive), in the Hospitals of the Army in the East. | https://nrs.lib.harvard.edu/urn-3:hms.count:1177146?n=21 |
### licenses
| name         | title                                                               | path                                                                                 |
|:-------------|:--------------------------------------------------------------------|:-------------------------------------------------------------------------------------|
| notspecified | Harvard Library - Digitized Content Copyright & Viewer Terms of Use | https://library.harvard.edu/privacy-terms-use-copyright-information#digitizedcontent |
## `disasters`
### path
disasters.csv
### description
Annual number of deaths from disasters, sourced from EM-DAT (Emergency Events Database) 
maintained by the Centre for Research on the Epidemiology of Disasters (CRED) at UCLouvain, Belgium. 
Processed by Our World in Data to standardize country names and world region definitions, converting units,
calculating derived indicators, and adapting metadata. Deaths are reported as absolute numbers.
### schema
    
| name   | type    |
|:-------|:--------|
| Entity | string  |
| Year   | integer |
| Deaths | integer |
### sources
| title                                                                 | path                                            |
|:----------------------------------------------------------------------|:------------------------------------------------|
| EM-DAT: The Emergency Events Database                                 | https://www.emdat.be                            |
| Hannah Ritchie, Pablo Rosado and Max Roser (2022) - Natural Disasters | https://ourworldindata.org/natural-catastrophes |
### licenses
| name         | title                                           | path                                          |
|:-------------|:------------------------------------------------|:----------------------------------------------|
| notspecified | EM-DAT terms of use                             | https://doc.emdat.be/docs/legal/terms-of-use/ |
| CC-BY-4.0    | Creative Commons BY license (Our World in Data) | https://creativecommons.org/licenses/by/4.0/  |
## `driving`
### path
driving.json
### description
Tracks the relationship between driving habits and gasoline prices 
in the United States during a period spanning multiple significant events, including 
the cheap gas era, Arab oil embargo, energy crisis, record low prices, and the 
"swing backward" from 1956 to 2010.

### schema
    
| name   | type    | description                                                                        | categories                         |
|:-------|:--------|:-----------------------------------------------------------------------------------|:-----------------------------------|
| side   | string  | Label positioning indicator used in the original visualization to optimize         | ['left', 'right', 'top', 'bottom'] |
|        |         | readability and prevent overlap                                                    |                                    |
| year   | integer | Year of observation from 1956 to 2010                                              |                                    |
| miles  | integer | Miles driven per capita per year, ranging from approximately 4,000 to 10,000 miles |                                    |
| gas    | number  | Price of a gallon of regular grade gasoline, adjusted for inflation                |                                    |
### sources
| title                                                                                                                     | path                                                                                      |
|:--------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------|
| New York Times (citing U.S. Energy Information Administration, Federal Highway Administration, and Brookings Institution) | https://archive.nytimes.com/www.nytimes.com/imagepages/2010/05/02/business/02metrics.html |
## `earthquakes`
### path
earthquakes.json
### description
Represents approximately one week of continuous monitoring from USGS's "all earthquakes" 
real-time feed, which includes 1,703 seismic events of all magnitudes recorded by the 
USGS Earthquake Hazards Program from January 31 to February 7, 2018 (UTC). 
### sources
| title                | path                                                                       |
|:---------------------|:---------------------------------------------------------------------------|
| USGS Earthquake Feed | https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson |
### licenses
| name     | title              | path                                                                              |
|:---------|:-------------------|:----------------------------------------------------------------------------------|
| other-pd | U.S. Public Domain | https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits |
## `ffox`
### path
ffox.png
### description
Application icon from open-source software project. Used in [Image-based Scatter Plot example](https://vega.github.io/vega-lite/examples/scatter_image.html).
### sources
| title           | path                             |
|:----------------|:---------------------------------|
| Mozilla Firefox | https://www.mozilla.org/firefox/ |
### licenses
| name         | title                     | path                                                        |
|:-------------|:--------------------------|:------------------------------------------------------------|
| notspecified | Mozilla Trademark License | https://www.mozilla.org/en-US/foundation/trademarks/policy/ |
## `flare_dependencies`
### path
flare-dependencies.json
### description
Network of class dependencies for the Flare visualization library. Each entry
represents a directed edge where the `source` class depends on (imports) the `target` class.
IDs correspond to those in `flare.json`.
### schema
    
| name   | type    | description                                            | constraints        |
|:-------|:--------|:-------------------------------------------------------|:-------------------|
| source | integer | ID of the class that has the dependency (the importer) | {'required': True} |
| target | integer | ID of the class being depended upon (the imported)     | {'required': True} |
## `flare`
### path
flare.json
### description
Class hierarchy of the Flare visualization library. Used with `flare-dependencies.json`
to represent the complete package/class structure.

Represents a tree structure where nodes have different fields depending on their role:
- Root node: only `id` and `name`
- Branch nodes: `id`, `name`, and `parent`
- Leaf nodes: `id`, `name`, `parent`, and `size`

### schema
    
| name   | type    | description                       | constraints        |
|:-------|:--------|:----------------------------------|:-------------------|
| id     | integer | Unique identifier for the node    | {'required': True} |
| name   | string  | Name of the node in the hierarchy | {'required': True} |
## `flights_10k`
### path
flights-10k.json
### description
Flight delay statistics (10,000 rows) from U.S. Bureau of Transportation Statistics. 
Collected under regulatory reporting requirements (14 CFR Part 234), which mandate 
that qualifying airlines report on-time performance data to BTS. Transformed using 
`/scripts/flights.py`
### schema
    
| name        | type     | format         |
|:------------|:---------|:---------------|
| date        | datetime | %Y/%m/%d %H:%M |
| delay       | integer  |                |
| distance    | integer  |                |
| origin      | string   |                |
| destination | string   |                |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
### licenses
| name       | path                                                                   | title                                                                                          |
|:-----------|:-----------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|
| other-open | https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-234 | Data Collected Under U.S. DOT Regulatory Requirements - License Terms Not Explicitly Specified |
## `flights_200k_arrow`
### path
flights-200k.arrow
### description
Flight delay statistics (200,000 rows) from U.S. Bureau of Transportation Statistics. 
Collected under regulatory reporting requirements (14 CFR Part 234), which mandate 
that qualifying airlines report on-time performance data to BTS. Transformed using 
`/scripts/flights.py`
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
### licenses
| name       | path                                                                   | title                                                                                          |
|:-----------|:-----------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|
| other-open | https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-234 | Data Collected Under U.S. DOT Regulatory Requirements - License Terms Not Explicitly Specified |
## `flights_200k_json`
### path
flights-200k.json
### description
Flight delay statistics (200,000 rows) from U.S. Bureau of Transportation Statistics. 
Collected under regulatory reporting requirements (14 CFR Part 234), which mandate 
that qualifying airlines report on-time performance data to BTS. Transformed using 
`/scripts/flights.py`
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
### licenses
| name       | path                                                                   | title                                                                                          |
|:-----------|:-----------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|
| other-open | https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-234 | Data Collected Under U.S. DOT Regulatory Requirements - License Terms Not Explicitly Specified |
## `flights_20k`
### path
flights-20k.json
### description
Flight delay statistics (20,000 rows) from U.S. Bureau of Transportation Statistics. 
Collected under regulatory reporting requirements (14 CFR Part 234), which mandate 
that qualifying airlines report on-time performance data to BTS. Transformed using 
`/scripts/flights.py`
### schema
    
| name        | type     | format         |
|:------------|:---------|:---------------|
| date        | datetime | %Y/%m/%d %H:%M |
| delay       | integer  |                |
| distance    | integer  |                |
| origin      | string   |                |
| destination | string   |                |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
### licenses
| name       | path                                                                   | title                                                                                     |
|:-----------|:-----------------------------------------------------------------------|:------------------------------------------------------------------------------------------|
| other-open | https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-234 | Data Collected Under DOT Regulatory Requirements - License Terms Not Explicitly Specified |
## `flights_2k`
### path
flights-2k.json
### description
Flight delay statistics (2,000 rows) from U.S. Bureau of Transportation Statistics. 
Collected under regulatory reporting requirements (14 CFR Part 234), which mandate 
that qualifying airlines report on-time performance data to BTS. Transformed using 
`/scripts/flights.py`
### schema
    
| name        | type     | format         |
|:------------|:---------|:---------------|
| date        | datetime | %Y/%m/%d %H:%M |
| delay       | integer  |                |
| distance    | integer  |                |
| origin      | string   |                |
| destination | string   |                |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
### licenses
| name       | path                                                                   | title                                                                                          |
|:-----------|:-----------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|
| other-open | https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-234 | Data Collected Under U.S. DOT Regulatory Requirements - License Terms Not Explicitly Specified |
## `flights_3m`
### path
flights-3m.parquet
### description
Flight delay statistics (3 million rows) from U.S. Bureau of Transportation Statistics. 
Collected under regulatory reporting requirements (14 CFR Part 234), which mandate 
that qualifying airlines report on-time performance data to BTS. Transformed using 
`/scripts/flights.py`
### schema
    
| name        | type     | format         |
|:------------|:---------|:---------------|
| date        | datetime | %Y/%m/%d %H:%M |
| delay       | integer  |                |
| distance    | integer  |                |
| origin      | string   |                |
| destination | string   |                |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
### licenses
| name       | path                                                                   | title                                                                                          |
|:-----------|:-----------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|
| other-open | https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-234 | Data Collected Under U.S. DOT Regulatory Requirements - License Terms Not Explicitly Specified |
## `flights_5k`
### path
flights-5k.json
### description
Flight delay statistics (5,000 rows) from U.S. Bureau of Transportation Statistics. 
Collected under regulatory reporting requirements (14 CFR Part 234), which mandate 
that qualifying airlines report on-time performance data to BTS. Transformed using 
`/scripts/flights.py`
### schema
    
| name        | type     | format         |
|:------------|:---------|:---------------|
| date        | datetime | %Y/%m/%d %H:%M |
| delay       | integer  |                |
| distance    | integer  |                |
| origin      | string   |                |
| destination | string   |                |
### sources
| title                                    | path                                                                                 |
|:-----------------------------------------|:-------------------------------------------------------------------------------------|
| U.S. Bureau of Transportation Statistics | https://www.transtats.bts.gov/DL_SelectFields.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr |
### licenses
| name       | path                                                                   | title                                                                                          |
|:-----------|:-----------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|
| other-open | https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-234 | Data Collected Under U.S. DOT Regulatory Requirements - License Terms Not Explicitly Specified |
## `flights_airport`
### path
flights-airport.csv
### description
Flight information for the year 2008. Each record consists of an origin airport (identified by IATA id),
a destination airport, and the count of flights along this route.
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
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `football`
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
### licenses
| name     | path                                                                     |
|:---------|:-------------------------------------------------------------------------|
| other-pd | https://github.com/openfootball/football.json?tab=readme-ov-file#license |
## `gapminder_health_income`
### path
gapminder-health-income.csv
### description
Per-capita income, life expectancy, population and regional grouping. Reference year for the data is not specified. 
Gapminder historical data is subject to revisions.

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
| name      | title                                          | path                                     |
|:----------|:-----------------------------------------------|:-----------------------------------------|
| CC-BY-4.0 | Creative Commons Attribution 4.0 International | https://www.gapminder.org/free-material/ |
## `gapminder`
### path
gapminder.json
### description
Combines key demographic indicators (life expectancy at birth, 
population, and fertility rate measured as babies per woman) for various countries from 1955 
to 2005 at 5-year intervals. Includes a 'cluster' column, a categorical variable 
grouping countries. Gapminder's data documentation notes that its philosophy is to fill data 
gaps with estimates and use current geographic boundaries for historical data. Gapminder 
states that it aims to "show people the big picture" rather than support detailed numeric 
analysis.

Notes:
1. Country Selection: The set of countries matches the version of this dataset 
   originally added to this collection in 2015. The specific criteria for country selection 
   in that version are not known. Data for Aruba are no longer available in the new version. 
   Hong Kong has been revised to Hong Kong, China in the new version.

2. Data Precision: The precision of float values may have changed from the original version. 
   These changes reflect the most recent source data used for each indicator.

3. Regional Groupings: To preserve continuity with previous versions of this dataset, we have retained the column 
   name 'cluster' instead of renaming it to 'six_regions'. 

### schema
    
| name        | type    | description                                          | categories                                                                                                                                                                                                                                                        |
|:------------|:--------|:-----------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| year        | integer | Years from 1955 to 2005 at 5-year intervals          |                                                                                                                                                                                                                                                                   |
| country     | string  | Name of the country                                  |                                                                                                                                                                                                                                                                   |
| cluster     | integer | A categorical variable grouping countries by region  | [{'value': 0, 'label': 'south_asia'}, {'value': 1, 'label': 'europe_central_asia'}, {'value': 2, 'label': 'sub_saharan_africa'}, {'value': 3, 'label': 'america'}, {'value': 4, 'label': 'east_asia_pacific'}, {'value': 5, 'label': 'middle_east_north_africa'}] |
| pop         | integer | Population of the country                            |                                                                                                                                                                                                                                                                   |
| life_expect | number  | Life expectancy in years                             |                                                                                                                                                                                                                                                                   |
| fertility   | number  | Fertility rate (average number of children per woman |                                                                                                                                                                                                                                                                   |
### sources
| title                                                          | path                                                                                                                   |   version |
|:---------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|----------:|
| Gapminder Foundation - Life Expectancy (Data)                  | https://docs.google.com/spreadsheets/d/1RehxZjXd7_rG8v2pJYV6aY0J3LAsgUPDQnbY4dRdiSs/edit?gid=176703676#gid=176703676   |        14 |
| Gapminder Foundation - Life Expectancy (Documentation)         | https://www.gapminder.org/data/documentation/gd004/                                                                    |           |
| Gapminder Foundation - Population (Data)                       | https://docs.google.com/spreadsheets/d/1c1luQNdpH90tNbMIeU7jD__59wQ0bdIGRFpbMm8ZBTk/edit?gid=176703676#gid=176703676   |         7 |
| Gapminder Foundation - Population (Documentation)              | https://www.gapminder.org/data/documentation/gd003/                                                                    |           |
| Gapminder Foundation - Fertility (Data)                        | https://docs.google.com/spreadsheets/d/1aLtIpAWvDGGa9k2XXEz6hZugWn0wCd5nmzaRPPjbYNA/edit?gid=176703676#gid=176703676   |        14 |
| Gapminder Foundation - Fertility Documentation (Documentation) | https://www.gapminder.org/data/documentation/gd008/                                                                    |           |
| Gapminder Foundation - Data Geographies (Data)                 | https://docs.google.com/spreadsheets/d/1qHalit8sXC0R8oVXibc2wa2gY7bkwGzOybEMTWp-08o/edit?gid=1597424158#gid=1597424158 |         2 |
| Gapminder Foundation - Data Geographies (Documentation)        | https://www.gapminder.org/data/geo/                                                                                    |           |
| Gapminder Data Documentation                                   | https://www.gapminder.org/data/documentation/                                                                          |           |
### licenses
| name      | title                                          | path                                     |
|:----------|:-----------------------------------------------|:-----------------------------------------|
| CC-BY-4.0 | Creative Commons Attribution 4.0 International | https://www.gapminder.org/free-material/ |
## `gimp`
### path
gimp.png
### description
Application icon from open-source software project. Used in [Image-based Scatter Plot example](https://vega.github.io/vega-lite/examples/scatter_image.html).
### sources
| title             | path                        |
|:------------------|:----------------------------|
| GIMP - About GIMP | https://www.gimp.org/about/ |
### licenses
| name         | path                                                                                       |
|:-------------|:-------------------------------------------------------------------------------------------|
| notspecified | https://www.gimp.org/docs/userfaq.html#whats-the-gimps-license-and-how-do-i-comply-with-it |
## `github`
### path
github.csv
### description
Simulated GitHub contribution data showing hourly commit counts across 
different times of day. Designed to demonstrate typical patterns of developer activity 
in a GitHub-style punchcard visualization format.
### schema
    
| name   | type    | description                                         |
|:-------|:--------|:----------------------------------------------------|
| time   | string  | Hourly timestamp from January 1st to May 30th, 2015 |
| count  | integer | Simulated hourly commit counts                      |
### sources
| title                                 | path                                                              |
|:--------------------------------------|:------------------------------------------------------------------|
| Generated using `/scripts/github.py`. | https://github.com/vega/vega-datasets/blob/main/scripts/github.py |
### licenses
| name         | path                                                            |
|:-------------|:----------------------------------------------------------------|
| BSD-3-Clause | https://github.com/vega/vega-datasets/blob/main/scripts/LICENSE |
## `global_temp`
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
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `income`
### path
income.json
### description
Household income distribution by US state, derived from the 
Census Bureau's American Community Survey 3-Year Data (2013). The dataset 
shows the percentage of households within different income brackets for each state.
Generated using `/scripts/income.py`. This product uses the Census Bureau Data API 
but is not endorsed or certified by the Census Bureau.
### schema
    
| name   | type    |
|:-------|:--------|
| name   | string  |
| region | string  |
| id     | integer |
| pct    | number  |
| total  | integer |
| group  | string  |
### sources
| title                                                           | path                                                                 |
|:----------------------------------------------------------------|:---------------------------------------------------------------------|
| U.S. Census Bureau American Community Survey 3-Year Data (2013) | https://www.census.gov/data/developers/data-sets/acs-3year/2013.html |
| Census Bureau Data API User Guide                               | https://www.census.gov/data/developers/guidance/api-user-guide.html  |
### licenses
| name       | title                                   | path                                                               |
|:-----------|:----------------------------------------|:-------------------------------------------------------------------|
| other-open | U.S. Census Bureau API Terms of Service | https://www.census.gov/data/developers/about/terms-of-service.html |
## `iowa_electricity`
### path
iowa-electricity.csv
### description
Annual net generation of electricity in Iowa by source, in thousand megawatthours. U.S. EIA data downloaded on May 6, 2018. 
Useful for illustrating stacked area charts. Demonstrates dramatic increase in wind power production.
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
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `jobs`
### path
jobs.json
### description
U.S. census data on [occupations](https://usa.ipums.org/usa-action/variables/OCC1950#codes_section) by sex and year across decades between 1850 and 2000. Obtained from IPUMS USA, which "collects, preserves and harmonizes U.S. census microdata" from as early as 1790.

Originally created for a 2006 data visualization project called *sense.us* by IBM Research (Jeff Heer, Martin Wattenberg and Fernanda Viégas), described [here](https://homes.cs.washington.edu/~jheer/files/bdata_ch12.pdf). 
The dataset is also referenced in this vega [example](https://vega.github.io/vega/examples/job-voyager/).

Based on a tabulation of the [OCC1950](https://usa.ipums.org/usa-action/variables/OCC1950) variable by sex across IPUMS USA samples. Appears to be derived from Version 6.0 (2015) of IPUMS USA, according to 2024 correspondence with the IPUMS Project. IPUMS has made improvements to occupation coding since version 6, particularly for 19th-century samples, which may result in discrepancies between this dataset and current IPUMS data. Details on data revisions are available [here](https://usa.ipums.org/usa-action/revisions).

IPUMS USA confirmed in 2024 correspondence that hosting this dataset on vega-datasets is permissible, stating:
>We're excited to hear that this dataset made its way to this repository and is being used by students for data visualization. We allow for these types of redistributions of summary data so long as the underlying microdata records are not shared.

1. Represents summary data. Underlying microdata records are not included.
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
### licenses
| name         | title              | path                              |
|:-------------|:-------------------|:----------------------------------|
| notspecified | IPUMS Terms of Use | https://www.ipums.org/about/terms |
## `la_riots`
### path
la-riots.csv
### description
A comprehensive record of fatalities during the five days of civil unrest in Los Angeles beginning 
April 29, 1992, documenting over 60 deaths with associated geographic coordinates where each person lost their life.
Originally compiled and published by the Los Angeles Times Data Desk.
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
## `london_boroughs`
### path
londonBoroughs.json
### description
Boundaries of London boroughs reprojected and simplified from `London_Borough_Excluding_MHW` shapefile. 
Original data "contains National Statistics data © Crown copyright and database right (2015)" 
and "Contains Ordnance Survey data © Crown copyright and database right [2015].
### sources
| title                                            | path                                                                                |
|:-------------------------------------------------|:------------------------------------------------------------------------------------|
| Statistical GIS Boundary Files, London Datastore | https://data.london.gov.uk/dataset/statistical-gis-boundary-files-for-london-20od9/ |
### licenses
| name       | title                      | path                                                                       |
|:-----------|:---------------------------|:---------------------------------------------------------------------------|
| OGL-UK-3.0 | UK Open Government License | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
## `london_centroids`
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
### sources
| title                                                                                                                                                                      | path                                                                     |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------|
| [londonBoroughs.json](https://github.com/vega/vega-datasets/blob/main/data/londonBoroughs.json) from the [vega-datasets](https://github.com/vega/vega-datasets) repository | https://github.com/vega/vega-datasets/blob/main/data/londonBoroughs.json |
### licenses
| name       | title                      | path                                                                       |
|:-----------|:---------------------------|:---------------------------------------------------------------------------|
| OGL-UK-3.0 | UK Open Government License | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
## `london_tube_lines`
### path
londonTubeLines.json
### description
A [topologically-encoded](https://github.com/topojson/topojson) representation of select London Underground rail lines, derived from OpenStreetMap
data. These 394 LineString geometries, encoded using 406 arcs, depict transport paths between stations with stations marked as nodes
along the lines. Originally transformed from a GeoJSON intermediary `tfl_lines.json` into TopoJSON format, this network configuration 
reflects the system as of February 4, 2018, and may not incorporate subsequent modifications or expansions.

### sources
| title                                         | path                                                                        |
|:----------------------------------------------|:----------------------------------------------------------------------------|
| OpenStreetMap Data (processed by oobrien/vis) | https://github.com/oobrien/vis/blob/master/tubecreature/data/tfl_lines.json |
### licenses
| name     | title                                          | path                                       |
|:---------|:-----------------------------------------------|:-------------------------------------------|
| ODbL-1.0 | Open Data Commons Open Database License (ODbL) | https://opendatacommons.org/licenses/odbl/ |
## `lookup_groups`
### path
lookup_groups.csv
### description
A nine-row lookup table for the `lookup_people.csv` dataset, 
mapping people to groups. Used to [demonstrate](https://vega.github.io/vega-lite/examples/lookup.html) `lookup` transforms.
### schema
    
| name   | type    |
|:-------|:--------|
| group  | integer |
| person | string  |
### sources
| title          |
|:---------------|
| Generated Data |
### licenses
| name         | path                                                            |
|:-------------|:----------------------------------------------------------------|
| BSD-3-Clause | https://github.com/vega/vega-datasets/blob/main/scripts/LICENSE |
## `lookup_people`
### path
lookup_people.csv
### description
A synthetic list of nine people and their associated name, age, 
and height in centimeters. Used in conjunction with `lookup_groups.csv` 
to [demonstrate](https://vega.github.io/vega-lite/examples/lookup.html) `lookup` transforms.
### schema
    
| name   | type    |
|:-------|:--------|
| name   | string  |
| age    | integer |
| height | integer |
### sources
| title          |
|:---------------|
| Generated Data |
### licenses
| name         | path                                                            |
|:-------------|:----------------------------------------------------------------|
| BSD-3-Clause | https://github.com/vega/vega-datasets/blob/main/scripts/LICENSE |
## `miserables`
### path
miserables.json
### description
A weighted network of coappearances of characters in Victor Hugo's novel "Les Miserables". 
Nodes represent characters as indicated by the labels and edges connect any pair of characters 
that appear in the same chapter of the book. The values on the edges are the number of such 
coappearances.

### sources
| title                                                                                                            | path                                                |
|:-----------------------------------------------------------------------------------------------------------------|:----------------------------------------------------|
| D. E. Knuth, The Stanford GraphBase: A Platform for Combinatorial Computing, Addison-Wesley, Reading, MA (1993). | https://www-cs-faculty.stanford.edu/~knuth/sgb.html |
### licenses
| name         | path                                      |
|:-------------|:------------------------------------------|
| notspecified | https://websites.umich.edu/~mejn/netdata/ |
## `monarchs`
### path
monarchs.json
### description
A chronological list of English and British monarchs from Elizabeth I through George IV.

Contains two intentional inaccuracies to maintain compatibility with 
the [Wheat and Wages](https://vega.github.io/vega/examples/wheat-and-wages/) example visualization:
1. the start date for the reign of Elizabeth I is shown as 1565, instead of 1558;
2. the end date for the reign of George IV is shown as 1820, instead of 1830.
These discrepancies align the `monarchs.json` dataset with the start and end dates of the `wheat.json` dataset used in the visualization.
The entry "W&M" represents the joint reign of William III and Mary II. While the dataset shows their reign as 1689-1702, 
the official Web site of the British royal family indicates that Mary II's reign ended in 1694, though William III continued to rule until 1702.
The `commonwealth` field is used to flag the period from 1649 to 1660, which includes the Commonwealth of England, the Protectorate, 
and the period leading to the Restoration. While historically more accurate to call this the "interregnum," the field name of `commonwealth` 
from the original dataset is retained for backwards compatibility.

> [!IMPORTANT]
> Revised in Aug. 2024 to show James II's reign now ends in 1688 (previously 1689).

Source data has been verified against the kings & queens and interregnum pages of the official website of the British royal family (retrieved in Aug. 2024).

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
### licenses
| name       | title                             | path                                                                       |
|:-----------|:----------------------------------|:---------------------------------------------------------------------------|
| OGL-UK-3.0 | Open Government Licence v3.0 (UK) | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
## `movies`
### path
movies.json
### description
A collection of films and their performance metrics, including box office earnings, budgets,
and audience ratings. Contains known data quality issues typical of real-world datasets:
- Some movie titles with numeric names (1776, 2012, 300, etc.) are stored as JSON numbers rather than strings
- Release dates use 'MMM DD YYYY' format rather than ISO 8601

These characteristics make it suitable as a teaching resource for developing data cleaning
and validation skills in real-world analysis workflows.
### schema
    
| name                   | type    | format   |
|:-----------------------|:--------|:---------|
| Title                  | string  |          |
| US Gross               | integer |          |
| Worldwide Gross        | integer |          |
| US DVD Sales           | integer |          |
| Production Budget      | integer |          |
| Release Date           | date    | %b %d %Y |
| MPAA Rating            | string  |          |
| Running Time min       | integer |          |
| Distributor            | string  |          |
| Source                 | string  |          |
| Major Genre            | string  |          |
| Creative Type          | string  |          |
| Director               | string  |          |
| Rotten Tomatoes Rating | integer |          |
| IMDB Rating            | number  |          |
| IMDB Votes             | integer |          |
## `normal_2d`
### path
normal-2d.json
### description
Five hundred paired coordinates sampled from a bivariate normal distribution. The data is centered near the 
origin with standard deviations indicating a relatively equal spread in both dimensions. 
The variables exhibit negligible correlation (0.026), suggesting independence. 
[Normality tests](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.normaltest.html) for each variable yield high p-values, supporting the normal distribution assumption. 
These characteristics make it well-suited for demonstrating statistical visualization techniques 
in Vega and Vega-Lite, including scatter plots, density plots, heatmaps, and marginal histograms/density curves. 
It can also serve as a clean baseline for testing new visualization methods or for educational purposes 
in data visualization and statistics.
A contrast to uniformly distributed data in `uniform-2d.json`

### schema
    
| name   | type   | description                                                      |
|:-------|:-------|:-----------------------------------------------------------------|
| u      | number | mean: 0.005, std: 0.192, range: [-0.578, 0.533], p-value: 0.680  |
| v      | number | mean: -0.011, std: 0.199, range: [-0.534, 0.606], p-value: 0.763 |
### sources
| title          |
|:---------------|
| Generated Data |
### licenses
| name         | path                                                            |
|:-------------|:----------------------------------------------------------------|
| BSD-3-Clause | https://github.com/vega/vega-datasets/blob/main/scripts/LICENSE |
## `obesity`
### path
obesity.json
### description
State-level obesity rates (BMI >= 30) for the U.S. in 1995. 
Originally [Behavioral Risk Factor Surveillance System (BRFSS)](https://www.cdc.gov/brfss/index.html) statistics.
### schema
    
| name   | type    |
|:-------|:--------|
| id     | integer |
| rate   | number  |
| state  | string  |
### sources
| title    | path                                               |
|:---------|:---------------------------------------------------|
| Protovis | https://mbostock.github.io/protovis/ex/us_stats.js |
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `ohlc`
### path
ohlc.json
### description
Performance of the Chicago Board Options Exchange 
[Volatility Index](https://en.wikipedia.org/wiki/VIX) (VIX) in the summer of 2009.

The precise methodology used to derive the signal and calculate the ret columns is unclear.

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
| title                      | path                                                            |
|:---------------------------|:----------------------------------------------------------------|
| Yahoo Finance VIX Data     | https://finance.yahoo.com/chart/%5EVIX                          |
| CBOE - VIX Historical Data | https://www.cboe.com/tradable_products/vix/vix_historical_data/ |
## `penguins`
### path
penguins.json
### description
Records of morphological measurements and demographic information from 344 Palmer Archipelago 
penguins across three species. Collected by [Dr. Kristen Gorman](https://www.uaf.edu/cfos/people/faculty/detail/kristen-gorman.php) and the Palmer Station Antarctica [LTER](https://lternet.edu/). 
Data gathering occurred as part of Palmer Station's long-term ecological research, contributing to studies of Antarctic marine
ecosystems and penguin biology. All measurements follow standardized units, enabling research into morphological 
variations between species and sexual dimorphism in Antarctic penguins. 

### schema
    
| name                | type    | description                                                         |
|:--------------------|:--------|:--------------------------------------------------------------------|
| Species             | string  | Penguin species (Adelie, Gentoo, or Chinstrap)                      |
| Island              | string  | Island where the penguin was observed (Torgersen, Biscoe, or Dream) |
| Beak Length (mm)    | number  | Beak length in millimeters                                          |
| Beak Depth (mm)     | number  | Beak depth in millimeters                                           |
| Flipper Length (mm) | integer | Flipper length in millimeters                                       |
| Body Mass (g)       | integer | Body mass in grams                                                  |
| Sex                 | string  | Sex of the penguin (MALE, FEMALE or null)                           |
### sources
| title                               | path                                     |
|:------------------------------------|:-----------------------------------------|
| Palmer Station Antarctica LTER      | https://pallter.marine.rutgers.edu/      |
| Allison Horst's Penguins Repository | https://github.com/allisonhorst/penguins |
### licenses
| name    | title                               | path                                                                        |
|:--------|:------------------------------------|:----------------------------------------------------------------------------|
| CC0-1.0 | Creative Commons Zero 1.0 Universal | https://github.com/allisonhorst/palmerpenguins?tab=CC0-1.0-1-ov-file#readme |
## `platformer_terrain`
### path
platformer-terrain.json
### description
Assets from the video game Celeste. Added in [#376](https://github.com/vega/vega-datasets/pull/376)
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
## `political_contributions`
### path
political-contributions.json
### description
Summary financial information on contributions to candidates for U.S. 
elections. An updated version is available from the "all candidates" files (in pipe-delimited format)
on the bulk data download page of the U.S. Federal Election Commission, or, alternatively, via OpenFEC. 
Information on each of the 25 columns is available from the [FEC All Candidates File Description](https://www.fec.gov/campaign-finance-data/all-candidates-file-description/).
The sample dataset in `political-contributions.json` contains 58 records with dates from 2015.

FEC data is subject to the commission's:
- [Sale or Use Policy](https://www.fec.gov/updates/sale-or-use-contributor-information/)
- [Privacy and Security Policy](https://www.fec.gov/about/privacy-and-security-policy/)
- [Acceptable Use Policy](https://github.com/fecgov/FEC/blob/master/ACCEPTABLE-USE-POLICY.md)

Additionally, the FEC's Github [repository](https://github.com/fecgov/FEC) states:
> This project is in the public domain within the United States, and we waive worldwide 
> copyright and related rights through [CC0 universal public domain](https://creativecommons.org/publicdomain/zero/1.0/)
> dedication. Read more on our [license](https://github.com/fecgov/FEC?tab=License-1-ov-file) page.
> A few restrictions limit the way you can use FEC data. For example, you can't use 
> contributor lists for commercial purposes or to solicit donations. Learn more on 
> [FEC.gov](https://www.fec.gov/).
### schema
    
| name                                          | type    | format   |
|:----------------------------------------------|:--------|:---------|
| Candidate_Identification                      | string  |          |
| Candidate_Name                                | string  |          |
| Incumbent_Challenger_Status                   | string  |          |
| Party_Code                                    | integer |          |
| Party_Affiliation                             | string  |          |
| Total_Receipts                                | number  |          |
| Transfers_from_Authorized_Committees          | integer |          |
| Total_Disbursements                           | number  |          |
| Transfers_to_Authorized_Committees            | number  |          |
| Beginning_Cash                                | number  |          |
| Ending_Cash                                   | number  |          |
| Contributions_from_Candidate                  | number  |          |
| Loans_from_Candidate                          | integer |          |
| Other_Loans                                   | integer |          |
| Candidate_Loan_Repayments                     | number  |          |
| Other_Loan_Repayments                         | integer |          |
| Debts_Owed_By                                 | number  |          |
| Total_Individual_Contributions                | integer |          |
| Candidate_State                               | string  |          |
| Candidate_District                            | integer |          |
| Contributions_from_Other_Political_Committees | integer |          |
| Contributions_from_Party_Committees           | integer |          |
| Coverage_End_Date                             | date    | %m/%d/%Y |
| Refunds_to_Individuals                        | integer |          |
| Refunds_to_Committees                         | integer |          |
### sources
| title                                 | path                                                |
|:--------------------------------------|:----------------------------------------------------|
| Federal Election Commission Bulk Data | https://www.fec.gov/data/browse-data/?tab=bulk-data |
| OpenFEC API                           | https://api.open.fec.gov/developers/                |
### licenses
| name    | title                               | path                                               |
|:--------|:------------------------------------|:---------------------------------------------------|
| CC0-1.0 | Creative Commons Zero 1.0 Universal | https://creativecommons.org/publicdomain/zero/1.0/ |
## `population`
### path
population.json
### description
U.S. population counts by age group (0-90+ in 5-year intervals) and sex 
for each decade between 1850 and 2000, collected and harmonized from historical census records by IPUMS USA.

IPUMS updates and revises datasets over time, which may result in discrepancies with current IPUMS data.

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
### licenses
| name         | title              | path                              |
|:-------------|:-------------------|:----------------------------------|
| notspecified | IPUMS Terms of Use | https://www.ipums.org/about/terms |
## `population_engineers_hurricanes`
### path
population_engineers_hurricanes.csv
### description
Per-state population (2016 ACS 1-Year), ratio of engineers to total civilian employed population (2016 ACS 1-Year), and total hurricane landfalls (possibly 1851-2015). Used in Vega-Lite example,
[Three Choropleths Representing Disjoint Data from the Same Table](https://vega.github.io/vega-lite/examples/geo_repeat.html)
### schema
    
| name       | type    |
|:-----------|:--------|
| state      | string  |
| id         | integer |
| population | integer |
| engineers  | number  |
| hurricanes | integer |
### sources
| title                                                                                           | path                                                                 |
|:------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------|
| U.S. Census Bureau, 2016 ACS 1-Year Estimates: Total Population (B01001) and Occupation (S2401) | https://www.census.gov/data/developers/data-sets/acs-1year/2016.html |
| Continental United States Hurricane Impacts/Landfalls                                           | https://www.aoml.noaa.gov/hrd/hurdat/All_U.S._Hurricanes.html        |
| NOAA FAQ: How Many Landfalling Hurricanes Have Hit Eact State?                                  | https://www.aoml.noaa.gov/hrd-faq/#landfalls-by-state                |
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `seattle_weather_hourly_normals`
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
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `seattle_weather`
### path
seattle-weather.csv
### description
Daily weather in metric units. Transformed using `/scripts/weather.py`. 
The categorical "weather" field is synthesized from multiple fields in the original dataset. 
This data is intended for instructional purposes.
### schema
    
| name          | type   | description                                                                                                                 | categories                                |
|:--------------|:-------|:----------------------------------------------------------------------------------------------------------------------------|:------------------------------------------|
| date          | date   | Date of the weather observation                                                                                             |                                           |
| precipitation | number | Amount of precipitation in millimeters                                                                                      |                                           |
| temp_max      | number | Maximum daily temperature in degrees Celsius                                                                                |                                           |
| temp_min      | number | Minimum daily temperature in degrees Celsius                                                                                |                                           |
| wind          | number | Wind speed in kilometers per hour                                                                                           |                                           |
| weather       | string | Categorical weather type synthesized from original NOAA data fields. Categories include: drizzle, rain, snow, sun, and fog. | ['drizzle', 'rain', 'snow', 'sun', 'fog'] |
### sources
| title                              | path                                                |
|:-----------------------------------|:----------------------------------------------------|
| NOAA National Climatic Data Center | https://www.ncdc.noaa.gov/cdo-web/datatools/records |
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `sp500_2000`
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
## `sp500`
### path
sp500.csv
### description
Monthly closing values of the S&P 500 stock market index 
from January 2000 to March 2010. Captures several significant market events including 
the dot-com bubble burst (2000-2002), the mid-2000s bull market, and the 2008 financial crisis. 

### schema
    
| name   | type   | description                                            | format   |
|:-------|:-------|:-------------------------------------------------------|:---------|
| date   | date   | Date of monthly observation in the format 'MMM D YYYY' | %b %d %Y |
| price  | number | Closing price of the S&P 500 index for the given month |          |
## `species`
### path
species.csv
### description
Percentage of year-round habitat for four species -- American robin, white-tailed deer, 
American bullfrog, and common gartersnake -- within US counties, derived from USGS 
Gap Analysis Project (GAP) Species Habitat Maps. Data is provided at a 30-meter 
resolution and covers the contiguous United States. Habitat percentages are calculated 
by overlaying species habitat rasters (year-round habitat represented by value 3) with 
US county boundaries.

The habitat maps are in Albers Conical Equal Area projection (EPSG:5070). County boundaries 
are derived from US Census Bureau cartographic boundary files (1:10,000,000 scale), from 
`US-10m.json` in this repository. This dataset only includes *year-round* habitat. 
The original raster data also contains values for summer and winter habitat, which are 
*not* included in this dataset. Data was processed using the `exactextract` library 
for zonal statistics.

### schema
    
| name                  | type    | description                                                                                                           |
|:----------------------|:--------|:----------------------------------------------------------------------------------------------------------------------|
| item_id               | string  | Unique identifier for the species data item on ScienceBase.                                                           |
| common_name           | string  | Common name of the species.                                                                                           |
| scientific_name       | string  | Scientific name of the species.                                                                                       |
| gap_species_code      | string  | GAP Species Code, a unique identifier for the species within the GAP dataset.                                         |
| county_id             | integer | Combined state and county FIPS code, identifying the US county.                                                       |
| habitat_yearround_pct | number  | Percentage of the county area that is classified as year-round habitat for the species (rounded to 4 decimal places). |
### sources
| title                                                       | path                                                                                        |
|:------------------------------------------------------------|:--------------------------------------------------------------------------------------------|
| USGS Gap Analysis Project (GAP) Species Habitat Maps        | https://www.usgs.gov/programs/gap-analysis-project                                          |
| US Census Bureau Cartographic Boundary Files (1:10,000,000) | https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html |
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `stocks`
### path
stocks.csv
### description
Monthly stock prices for five companies from 2000 to 2010.
### schema
    
| name   | type   | format   |
|:-------|:-------|:---------|
| symbol | string |          |
| date   | date   | %b %d %Y |
| price  | number |          |
## `udistrict`
### path
udistrict.json
### description
Point locations of restaurants and cafes in Seattle's University 
District, categorized by cuisine type. Used to create a [ridgeline plot example](https://vega.github.io/vega/examples/u-district-cuisine/) 
showing the prevalence of various food and beverage categories. The example graphic 
using this dataset states that it originally appeared in Alaska Airlines Beyond Magazine (Sep 2017, p. 120)
### schema
    
| name   | type   |
|:-------|:-------|
| key    | string |
| lat    | number |
## `unemployment_across_industries`
### path
unemployment-across-industries.json
### description
Industry-level unemployment from the Current Population Survey 
(CPS), published monthly by the U.S. Bureau of Labor Statistics. Includes unemployed persons 
and unemployment rate across 11 private industries, as well as agricultural, government, and 
self-employed workers. Covers January 2000 through February 2010. Industry classification 
follows format of CPS Table A-31. Transformed using `scripts/make-unemployment-across-industries.py`

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
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `unemployment`
### path
unemployment.tsv
### description
County-level unemployment rates in the United States, with data generally
consistent with levels reported in 2009. The dataset is structured as tab-separated values.
The unemployment rate represents the number of unemployed persons as a percentage of the labor
force. According to the Bureau of Labor Statistics (BLS) glossary:

Unemployed persons (Current Population Survey) [are] persons aged 16 years and older who had
no employment during the reference week, were available for work, except for temporary
illness, and had made specific efforts to find employment sometime during the 4-week period
ending with the reference week. Persons who were waiting to be recalled to a job from which
they had been laid off need not have been looking for work to be classified as unemployed.

Derived from the [Local Area Unemployment Statistics (LAUS)](https://www.bls.gov/lau/) program, 
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
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `uniform_2d`
### path
uniform-2d.json
### description
Five hundred paired coordinates (u, v) sampled from a bivariate uniform distribution. Centered near the
origin with ranges spanning approximately [-0.5, 0.5] in both dimensions. The variables exhibit negligible
correlation (-0.019), suggesting independence, as expected for a uniform distribution.
A contrast to normally distributed data in `normal-2d.json`.

### schema
    
| name   | type   | description                                      |
|:-------|:-------|:-------------------------------------------------|
| u      | number | mean: 0.015, std: 0.277, range: [-0.499, 0.500]  |
| v      | number | mean: -0.013, std: 0.276, range: [-0.500, 0.498] |
### sources
| title          |
|:---------------|
| Generated Data |
### licenses
| name         | path                                                            |
|:-------------|:----------------------------------------------------------------|
| BSD-3-Clause | https://github.com/vega/vega-datasets/blob/main/scripts/LICENSE |
## `us_10m`
### path
us-10m.json
### description
US county boundaries represented at a 1:10,000,000 scale in 
[TopoJSON](https://github.com/topojson/topojson) format, which optimizes for 
smaller file sizes. Similar to offerings in the TopoJSON US Atlas collection, which 
in turn is a redistribution of the Census Bureau's cartographic boundary shapefiles.

### sources
| title                                        | path                                                                                        |
|:---------------------------------------------|:--------------------------------------------------------------------------------------------|
| TopoJSON US Atlas                            | https://github.com/topojson/us-atlas                                                        |
| US Census Bureau Cartographic Boundary FIles | https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html |
### licenses
| name   | title                         | path                                                     |
|:-------|:------------------------------|:---------------------------------------------------------|
| ISC    | TopoJSON US Atlas ISC License | https://github.com/topojson/us-atlas/blob/master/LICENSE |
## `us_employment`
### path
us-employment.csv
### description
Monthly employment total in a variety of job categories from January 2006 through December 2015, 
seasonally adjusted and reported in thousands. Downloaded and reformatted on Nov. 11, 2018.

In the mid 2000s the global economy was hit by a crippling recession. One result: Massive job 
losses across the United States. The downturn in employment, and the slow recovery in hiring that 
followed, was tracked each month by the Current Employment Statistics program at the U.S. Bureau 
of Labor Statistics.

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
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `us_state_capitals`
### path
us-state-capitals.json
### description
Geographical coordinates and names of U.S. state capitals, transformed using `scripts/us-state-capitals.py`. 
Includes latitude, longitude, state name, and capital city name for all 50 U.S. states. 
Cities are represented as point locations of their capitol buildings using coordinates in the 
WGS84 geographic coordinate system.

According to [USGS]((https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map))
> "Map services and data downloaded from The National Map are free and in the public domain. 
> There are no restrictions; however, we request that the following acknowledgment statement 
> of the originating agency be included in products and data derived from our map services 
> when citing, copying, or reprinting: Map services and data available from U.S. 
> Geological Survey, National Geospatial Program."

### schema
    
| name   | type   |
|:-------|:-------|
| lon    | number |
| lat    | number |
| state  | string |
| city   | string |
### sources
| title                                                                 | path                                                                   |
|:----------------------------------------------------------------------|:-----------------------------------------------------------------------|
| U.S. Geological Survey National Geospatial Program - The National Map | https://www.usgs.gov/programs/national-geospatial-program/national-map |
### licenses
| name     | title                   | path                                                                              |
|:---------|:------------------------|:----------------------------------------------------------------------------------|
| other-pd | U.S. Public Domain      | https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits |
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works                                              |
## `volcano`
### path
volcano.json
### description
Elevation measurements of Maunga Whau (Mt Eden), a volcano in Auckland, New Zealand, representing 
a rectangular area of 870 meters by 610 meters. Spacing between measurement points is approximately 
10 meters in both directions. Digitized from a topographic map by Ross Ihaka and adapted from R datasets, 
Should not be regarded as accurate.
### sources
| title      | path                                                                       |
|:-----------|:---------------------------------------------------------------------------|
| R Datasets | https://stat.ethz.ch/R-manual/R-patched/library/datasets/html/volcano.html |
## `weather`
### path
weather.csv
### description
Daily weather observations from Seattle and New York.
Transformed from NOAA data using the script `/scripts/weather.py`.
The categorical "weather" field is synthesized from multiple fields in the original dataset.
Intended for instructional purposes.
### schema
    
| name          | type   | description                                                                                                                 | categories                                |
|:--------------|:-------|:----------------------------------------------------------------------------------------------------------------------------|:------------------------------------------|
| location      | string | City location of the weather observation (Seattle or New York)                                                              |                                           |
| date          | date   | Date of the weather observation                                                                                             |                                           |
| precipitation | number | Amount of precipitation in millimeters                                                                                      |                                           |
| temp_max      | number | Maximum daily temperature in degrees Celsius                                                                                |                                           |
| temp_min      | number | Minimum daily temperature in degrees Celsius                                                                                |                                           |
| wind          | number | Wind speed in kilometers per hour                                                                                           |                                           |
| weather       | string | Categorical weather type synthesized from original NOAA data fields. Categories include: drizzle, rain, snow, sun, and fog. | ['drizzle', 'rain', 'snow', 'sun', 'fog'] |
### sources
| title                    | path                                                   |
|:-------------------------|:-------------------------------------------------------|
| NOAA Climate Data Online | http://www.ncdc.noaa.gov/cdo-web/datatools/findstation |
### licenses
| name     | title                   | path                                 |
|:---------|:------------------------|:-------------------------------------|
| other-pd | U.S. Government Dataset | https://www.usa.gov/government-works |
## `weekly_weather`
### path
weekly-weather.json
### description
Instructional dataset showing actual and predicted temperature data.

> [!IMPORTANT]
> Named `weather.json` in previous versions (`v1.4.0` - `v2.11.0`).

## `wheat`
### path
wheat.json
### description
As noted by in this protovis [example](https://mbostock.github.io/protovis/ex/wheat.html),
"In an 1822 letter to Parliament, [William Playfair](https://en.wikipedia.org/wiki/William_Playfair), a Scottish engineer 
who is often credited as the founder of statistical graphics, published an elegant chart 
on the price of wheat. It plots 250 years of prices alongside weekly wages and the reigning monarch. 
He intended to demonstrate that:
> 'never at any former period was wheat so cheap, in proportion to mechanical labour, as it is at the present time.'"

### schema
    
| name   | type    |
|:-------|:--------|
| year   | integer |
| wheat  | number  |
| wages  | number  |
### sources
| title               | path                                                                                                                                                        |
|:--------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1822 Playfair Chart | https://commons.wikimedia.org/wiki/File:Chart_Showing_at_One_View_the_Price_of_the_Quarter_of_Wheat,_and_Wages_of_Labour_by_the_Week,_from_1565_to_1821.png |
### licenses
| name     | title         | path                                             |
|:---------|:--------------|:-------------------------------------------------|
| other-pd | Public Domain | https://commons.wikimedia.org/wiki/Public_domain |
## `windvectors`
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
## `world_110m`
### path
world-110m.json
### description
A 1:110,000,000-scale world map in [TopoJSON](https://github.com/topojson/topojson) format, optimized for 
web-based visualization. The simplified geographic boundaries focus on two key elements: 
land masses and country borders with their corresponding codes. The high level of 
generalization removes small geographic details while maintaining recognizable global 
features, making it ideal for overview maps and basic world visualizations. This format 
provides efficient compression compared to GeoJSON, reducing file size for web use. 
Part of the widely-used TopoJSON World Atlas collection, this has become a standard 
resource for creating web-based world maps where precise boundary detail isn't required.

### sources
| title                                                                            | path                                                                                     |
|:---------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------|
| TopoJSON World Atlas (Likely original source, processed from Natural Earth data) | https://github.com/topojson/world-atlas                                                  |
| Natural Earth Data - Admin 0 Countries (1:110m)                                  | https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/ |
### licenses
| name     | title                            | path                                                        |
|:---------|:---------------------------------|:------------------------------------------------------------|
| ISC      | TopoJSON World Atlas ISC License | https://github.com/topojson/world-atlas/blob/master/LICENSE |
| other-pd | Natural Earth Data Public Domain | https://www.naturalearthdata.com/about/terms-of-use/        |
## `zipcodes`
### path
zipcodes.csv
### description
Postal codes mapped to their geographical coordinates (latitude/longitude in WGS84) 
and administrative hierarchies, for the United States and Puerto Rico. The GeoNames 
geographical database provides worldwide postal code data with associated geographical 
and administrative information. 

Historical snapshot first contributed to vega-datasets in 2017 and no longer current. 
Administrative boundaries have been redrawn, counties reorganized and renamed, and postal 
codes modified. Latitude/longitude coordinates have been updated by Geonames since this 
data was collected. For current postal code data, refer to the main GeoNames database.
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
| title                 | path                                      |
|:----------------------|:------------------------------------------|
| GeoNames Postal Codes | https://download.geonames.org/export/zip/ |
### licenses
| name      | title                                          | path                                         |
|:----------|:-----------------------------------------------|:---------------------------------------------|
| CC-BY-4.0 | Creative Commons Attribution 4.0 International | https://creativecommons.org/licenses/by/4.0/ |
## `gallery_examples`
### path
gallery_examples.json
### description
Cross-reference catalog mapping gallery examples to vega-datasets resources.
Tracks which datasets from the vega-datasets collection are used in example
visualizations across Vega, Vega-Lite, and Altair galleries. Enables discovery
of visualization patterns by dataset or technique, supports learning paths,
and provides structured context for AI coding assistants.
### schema
    
| name         | type    | description                                                                       | constraints                               |
|:-------------|:--------|:----------------------------------------------------------------------------------|:------------------------------------------|
| id           | integer | Unique sequential identifier for the example                                      |                                           |
| gallery_name | string  | Name of the gallery this example belongs to                                       | {'enum': ['vega', 'vega-lite', 'altair']} |
| example_name | string  | Human-readable example title                                                      |                                           |
| example_url  | string  | URL to rendered example in the gallery                                            |                                           |
| spec_url     | string  | URL to source specification or code                                               |                                           |
| categories   | array   | Tags or categories for the example (e.g., 'Bar Charts', 'Interactive')            |                                           |
| description  | string  | Optional description of what the example demonstrates (may be null)               |                                           |
| datasets     | array   | Dataset names referencing resource.name in this package                           |                                           |
| techniques   | array   | Visualization techniques used (e.g., 'transform:window', 'interaction:selection') |                                           |
### sources
| title             | path                                       |
|:------------------|:-------------------------------------------|
| Vega Gallery      | https://vega.github.io/vega/examples/      |
| Vega-Lite Gallery | https://vega.github.io/vega-lite/examples/ |
| Altair Gallery    | https://altair-viz.github.io/gallery/      |
### licenses
| name         | title                    | path                                        |
|:-------------|:-------------------------|:--------------------------------------------|
| BSD-3-Clause | The 3-Clause BSD License | https://opensource.org/license/bsd-3-clause |