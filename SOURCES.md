# Sources

Still incomplete. See https://github.com/vega/vega-datasets/issues/15.

## `7zip.png`, `ffox.png`, `gimp.png`

Application icons from open-source software projects.

## `annual-precip.json`

A raster grid of global annual precipitation for the year 2016 at a resolution 1 degree of lon/lat per cell, from [CFSv2](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/climate-forecast-system-version2-cfsv2).

## `airports.csv`

## `anscombe.json`

Graphs in Statistical Analysis, F. J. Anscombe, The American Statistician.

## `barley.json`

The result of a 1930s agricultural experiment in Minnesota, this dataset contains yields for 10 different varieties of barley at six different sites. It was first published by agronomists F.R. Immer, H.K. Hayes, and L. Powers in the 1934 paper "Statistical Determination of Barley Varietal Adaption." R.A. Fisher's popularized its use in the field of statistics when he included it in his book ["The Design of Experiments."](https://en.wikipedia.org/wiki/The_Design_of_Experiments) Since then it has been used to demonstrate new statistical techniques, including the [trellis charts](http://ml.stat.purdue.edu/stat695t/writings/TrellisDesignControl.pdf) developed by Richard Becker, William Cleveland and others in the 1990s.

## `birdstrikes.csv`

http://wildlife.faa.gov

## `budget.json`

Source: Office of Management and Budget (U.S.)
[Budget FY 2016 - Receipts](https://www.govinfo.gov/app/details/BUDGET-2016-DB/BUDGET-2016-DB-3)

## `budgets.json`

## `burtin.json`

The burtin.json dataset is based on graphic designer [Will Burtin's](https://en.wikipedia.org/wiki/Will_Burtin) 1951 visualization of antibiotic effectiveness, originally published in [Scope Magazine](https://graphicdesignarchives.org/projects/scope-magazine-vol-iii-5/). The dataset compares the performance of three antibiotics against 16 different bacteria. The numerical values in the dataset represent the minimum inhibitory concentration (MIC) of each antibiotic, measured in units per milliliter, with lower values indicating higher antibiotic effectiveness. The dataset was featured as an [example](https://mbostock.github.io/protovis/ex/antibiotics-burtin.html) in the Protovis project, a precursor to D3.js. The Protovis example notes that, "Recreating this display revealed some minor errors in the original: a missing grid line at 0.01 μg/ml, and an exaggeration of some values for penicillin." The vega-datsets version is largely consistent with the Protovis version of the dataset, with one correction  (changing 'Brucella antracis' to the correct 'Bacillus anthracis') and the addition of a new column, 'Genus', to group related bacterial species together.

The caption of the original 1951 [visualization](https://graphicdesignarchives.org/wp-content/uploads/wmgda_8616c.jpg) reads as follows:

> ## Antibacterial ranges of Neomycin, Penicillin and Streptomycin
> 
> The chart compares the in vitro sensitivities to neomycin of some of the common pathogens (gram+ in red and gram- in blue) with their sensitivities to penicillin, and streptomycin. The effectiveness of the antibiotics is expressed as the highest dilution in μ/ml. which inhibits the test organism. High dilutions are toward the periphery; consequently the length of the colored bar is proportional to the effectiveness. It is apparent that neomycin is especially effective against Staph. albus and aureus, Streph. fecalis, A. aerogenes, S. typhosa, E. coli, Ps. aeruginosa, Br. abortus, K. pneumoniae, Pr. vulgaris, S. schottmuelleri and M. tuberculosis. Unfortunately, some strains of proteus, pseudomonas and hemolytic streptococcus are resistant to neomycin, although the majority of these are sensitive to neomycin. It also inhibits actinomycetes, but is inactive against viruses and fungi. Its mode of action is not understood.

## `cars.json`

http://lib.stat.cmu.edu/datasets/

## `co2-concentration.csv`

https://scrippsco2.ucsd.edu/data/atmospheric_co2/primary_mlo_co2_record but modified to only include date, CO2, seasonally adjusted CO2 and only include rows with valid data.

## `countries.json`
### Source
- **Original Data**: [Gapminder Foundation](https://www.gapminder.org/)
- **URLs**: 
  - Life Expectancy (v14): [Data](https://docs.google.com/spreadsheets/d/1RehxZjXd7_rG8v2pJYV6aY0J3LAsgUPDQnbY4dRdiSs/edit?gid=176703676#gid=176703676) | [Reference](https://www.gapminder.org/data/documentation/gd004/)
  - Fertility (v14): [Data](https://docs.google.com/spreadsheets/d/1aLtIpAWvDGGa9k2XXEz6hZugWn0wCd5nmzaRPPjbYNA/edit?gid=176703676#gid=176703676) | [Reference](https://www.gapminder.org/data/documentation/gd008/) 

- **Date Accessed**: July 31, 2024
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0) | [Reference](https://www.gapminder.org/free-material/)

### Description
This dataset combines key demographic indicators (life expectancy at birth and fertility rate measured as babies per woman) for various countries from 1955 to 2000 at 5-year intervals. It includes both current values and adjacent time period values (previous and next) for each indicator. Gapminder's [data documentation](https://www.gapminder.org/data/documentation/) notes that its philosophy is to fill data gaps with estimates and use current geographic boundaries for historical data. Gapminder states that it aims to "show people the big picture" rather than support detailed numeric analysis.

#### Columns:
1. `year` (type: integer): Years from 1955 to 2000 at 5-year intervals
2. `country` (type: string): Name of the country
3. `fertility` (type: float): Fertility rate (average number of children per woman) for the given year
4. `life_expect` (type: float): Life expectancy in years for the given year
5. `p_fertility` (type: float): Fertility rate for the previous 5-year interval
6. `n_fertility` (type: float): Fertility rate for the next 5-year interval
7. `p_life_expect` (type: float): Life expectancy for the previous 5-year interval
8. `n_life_expect` (type: float): Life expectancy for the next 5-year interval

## `crimea.json`

## `disasters.csv`

https://ourworldindata.org/natural-catastrophes

## `driving.json`

https://archive.nytimes.com/www.nytimes.com/imagepages/2010/05/02/business/02metrics.html

## `earthquakes.json`

https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson
(Feb 6, 2018)

## `flare.json`

## `flights-?k.json`, `flights-200k.arrow`, `flights-airport.csv`

Flight delay statistics from U.S. Bureau of Transportation Statistics, https://www.transtats.bts.gov/OT_Delay/OT_DelayCause1.asp.

Transformed using `/scripts/flights.js`. Arrow file generated with [json2arrow](https://github.com/domoritz/arrow-tools/tree/main/crates/json2arrow).

## `football.json`

Football match outcomes across multiple divisions from 2013 to 2017. This dataset is a subset of a larger dataset from https://github.com/openfootball/football.json. The subset was made such that there are records for all five chosen divisions over the time period.

## `gapminder.json`
### Source
- **Original Data**: [Gapminder Foundation](https://www.gapminder.org/)
- **URLs**: 
  - Life Expectancy (v14): [Data](https://docs.google.com/spreadsheets/d/1RehxZjXd7_rG8v2pJYV6aY0J3LAsgUPDQnbY4dRdiSs/edit?gid=176703676#gid=176703676) | [Reference](https://www.gapminder.org/data/documentation/gd004/)
  - Population (v7): [Data](https://docs.google.com/spreadsheets/d/1c1luQNdpH90tNbMIeU7jD__59wQ0bdIGRFpbMm8ZBTk/edit?gid=176703676#gid=176703676) | [Reference](https://www.gapminder.org/data/documentation/gd003/)
  - Fertility (v14): [Data](https://docs.google.com/spreadsheets/d/1aLtIpAWvDGGa9k2XXEz6hZugWn0wCd5nmzaRPPjbYNA/edit?gid=176703676#gid=176703676) | [Reference](https://www.gapminder.org/data/documentation/gd008/) 
  - Data Geographies (v2): [Data](https://docs.google.com/spreadsheets/d/1qHalit8sXC0R8oVXibc2wa2gY7bkwGzOybEMTWp-08o/edit?gid=1597424158#gid=1597424158) | [Reference](https://www.gapminder.org/data/geo/)

- **Date Accessed**: July 11, 2024
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0) | [Reference](https://www.gapminder.org/free-material/)

### Description
This dataset combines key demographic indicators (life expectancy at birth, population, and fertility rate measured as babies per woman) for various countries from 1955 to 2005 at 5-year intervals. It also includes a 'cluster' column, a categorical variable grouping countries. Gapminder's [data documentation](https://www.gapminder.org/data/documentation/) notes that its philosophy is to fill data gaps with estimates and use current geographic boundaries for historical data. Gapminder states that it aims to "show people the big picture" rather than support detailed numeric analysis.

#### Columns:
1. `year` (type: integer): Years from 1955 to 2005 at 5-year intervals
2. `country` (type: string): Name of the country
3. `cluster` (type: integer): A categorical variable (values 0-5) grouping countries. See Revision Notes for details.
4. `pop` (type: integer): Population of the country
5. `life_expect` (type: float): Life expectancy in years
6. `fertility` (type: float): Fertility rate (average number of children per woman)

### Revision Notes
1. Country Selection: The set of countries in this file matches the version of this dataset originally added to this collection in 2015. The specific criteria for country selection in that version are not known. Data for Aruba are no longer available in the new version. Hong Kong has been revised to Hong Kong, China in the new version.
2. Data Precision: The precision of float values may have changed from the original version. These changes reflect the most recent source data used for each indicator.
3. Regional Groupings: The 'cluster' column represents a regional mapping of countries corresponding to the 'six_regions' schema in Gapminder's Data Geographies dataset. To preserve continuity with previous versions of this dataset, we have retained the column name 'cluster' instead of renaming it to 'six_regions'. The six regions represented are:
`0: south_asia, 1: europe_central_asia, 2: sub_saharan_africa, 3: america, 4: east_asia_pacific, 5: middle_east_north_africa`.

## `gapminder-health-income.csv`
**Original Data**: [Gapminder Foundation](https://www.gapminder.org/)

**Description** Per-capita income, life expectancy, population and regional grouping. Dataset does not specify the reference year for the data. Gapminder historical data is subject to revisions.

Gapminder (v30, 2023) defines per-capita income as follows: 

>"This is real GDP per capita (gross domestic product per person adjusted for inflation) converted to international dollars using purchasing power parity rates. An international dollar has the same purchasing power over GDP as the U.S. dollar has in the United States." | [Source](https://docs.google.com/spreadsheets/d/1i5AEui3WZNZqh7MQ4AKkJuCz4rRxGR_pw_9gtbcBOqQ/edit?gid=501532268#gid=501532268)

**License**: Creative Commons Attribution 4.0 International (CC BY 4.0) | [Reference](https://www.gapminder.org/free-material/)

## `github.csv`

Generated using `/scripts/github.py`.

## `global-temp.csv`

Combined Land-Surface Air and Sea-Surface Water Temperature Anomalies (Land-Ocean Temperature Index, L-OTI), 1880-2023. Source: NASA's Goddard Institute for Space Studies https://data.giss.nasa.gov/gistemp/

## `population_engineers_hurricanes.csv`

Data about engineers from https://www.bls.gov/oes/tables.htm. Hurricane data from http://www.nhc.noaa.gov/paststate.shtml. Income data from https://factfinder.census.gov/faces/tableservices/jsf/pages/productview.xhtml?pid=ACS_07_3YR_S1901&prodType=table.

## `iowa-electricity.csv`

The state of Iowa has dramatically increased its production of renewable wind power in recent years. This file contains the annual net generation of electricity in the state by source in thousand megawatthours. The dataset was compiled by the [U.S. Energy Information Administration](https://www.eia.gov/beta/electricity/data/browser/#/topic/0?agg=2,0,1&fuel=vvg&geo=00000g&sec=g&linechart=ELEC.GEN.OTH-IA-99.A~ELEC.GEN.COW-IA-99.A~ELEC.GEN.PEL-IA-99.A~ELEC.GEN.PC-IA-99.A~ELEC.GEN.NG-IA-99.A~~ELEC.GEN.NUC-IA-99.A~ELEC.GEN.HYC-IA-99.A~ELEC.GEN.AOR-IA-99.A~ELEC.GEN.HPS-IA-99.A~&columnchart=ELEC.GEN.ALL-IA-99.A&map=ELEC.GEN.ALL-IA-99.A&freq=A&start=2001&end=2017&ctype=linechart&ltype=pin&tab=overview&maptype=0&rse=0&pin=) and downloaded on May 6, 2018. It is useful for illustrating stacked area charts.

## `jobs.json`
U.S. census data on [occupations](https://usa.ipums.org/usa-action/variables/OCC1950#codes_section) by sex and year across decades between 1850 and 2000. The dataset was obtained from IPUMS USA, which "collects, preserves and harmonizes U.S. census microdata" from as early as 1790.

Originally created for a 2006 data visualization project called *sense.us* by IBM Research (Jeff Heer, Martin Wattenberg and Fernanda Viégas), described [here](https://homes.cs.washington.edu/~jheer/files/bdata_ch12.pdf). The dataset is also referenced in this vega [example](https://vega.github.io/vega/examples/job-voyager/).

### Notes on Data Origin
Data is based on a tabulation of the [OCC1950](https://usa.ipums.org/usa-action/variables/OCC1950) variable by sex across IPUMS USA samples. The dataset appears to be derived from Version 6.0 (2015) of [IPUMS USA](https://usa.ipums.org/usa/), according to 2024 correspondence with the IPUMS Project. IPUMS has made improvements to occupation coding since version 6, particularly for 19th-century samples, which may result in discrepancies between this dataset and current IPUMS data. Details on data revisions are available [here](https://usa.ipums.org/usa-action/revisions).

### Data Structure
The dataset is structured as follows:
- job: The occupation title
- sex: Sex (men/women)
- year: Census year
- count: Number of individuals in the occupation
- perc: Percentage of the workforce in the occupation

### Redistribution
IPUMS USA confirmed in 2024 correspondence that hosting this dataset on vega-datasets is permissible, stating:

>We're excited to hear that this dataset made its way to this repository and is being used by students for data visualization. We allow for these types of redistributions of summary data so long as the underlying microdata records are not shared.

This dataset contains only summary statistics and does not include any underlying microdata records.

### Usage Notes
1. This dataset represents summary data. The underlying microdata records are not included.
2. Users attempting to replicate or extend this data should use the [PERWT](https://usa.ipums.org/usa-action/variables/PERWT#description_section) (person weight) variable as an expansion factor when working with IPUMS USA extracts.
3. Due to coding revisions, figures for earlier years (particularly 19th century) may not match current IPUMS USA data exactly.

### Terms of Use and Citation
When using this dataset, please refer to IPUMS USA [terms of use](https://usa.ipums.org/usa/terms.shtml). The organization requests use of the following citation for this json file: 

Steven Ruggles, Katie Genadek, Ronald Goeken, Josiah Grover, and Matthew Sobek. Integrated Public Use Microdata Series: Version 6.0. Minneapolis: University of Minnesota, 2015. http://doi.org/10.18128/D010.V6.0


## `la-riots.csv`

More than 60 people lost their lives amid the looting and fires that ravaged Los Angeles for five days starting on April 29, 1992. This file contains metadata about each person, including the geographic coordinates of their death. It was compiled and published by the [Los Angeles Times Data Desk](http://spreadsheets.latimes.com/la-riots-deaths/).

## `londonBoroughs.json`

Boundaries of London boroughs reprojected and simplified from `London_Borough_Excluding_MHW` shapefile held at https://data.london.gov.uk/dataset/statistical-gis-boundary-files-london. Original data "contains National Statistics data © Crown copyright and database right (2015)" and "Contains Ordnance Survey data © Crown copyright and database right [2015].

## `londonCentroids.json`

Calculated from `londongBoroughs.json` using `d3.geoCentroid`.

## `londonTubeLines.json`

Selected rail lines simplified from `tfl_lines.json` at https://github.com/oobrien/vis/tree/master/tube/data

## `miserables.json`

## `monarchs.json`

## `movies.json`

The dataset has well known and intentionally included errors. This dataset is used for instructional purposes, including the need to reckon with dirty data.

## `ohlc.json`

This dataset contains the performance of the Chicago Board Options Exchange [Volatility Index](https://en.wikipedia.org/wiki/VIX) ([VIX](https://finance.yahoo.com/chart/%5EVIX?ltr=1#eyJpbnRlcnZhbCI6ImRheSIsInBlcmlvZGljaXR5IjoxLCJ0aW1lVW5pdCI6bnVsbCwiY2FuZGxlV2lkdGgiOjgsInZvbHVtZVVuZGVybGF5Ijp0cnVlLCJhZGoiOnRydWUsImNyb3NzaGFpciI6dHJ1ZSwiY2hhcnRUeXBlIjoibGluZSIsImV4dGVuZGVkIjpmYWxzZSwibWFya2V0U2Vzc2lvbnMiOnt9LCJhZ2dyZWdhdGlvblR5cGUiOiJvaGxjIiwiY2hhcnRTY2FsZSI6ImxpbmVhciIsInN0dWRpZXMiOnsidm9sIHVuZHIiOnsidHlwZSI6InZvbCB1bmRyIiwiaW5wdXRzIjp7ImlkIjoidm9sIHVuZHIiLCJkaXNwbGF5Ijoidm9sIHVuZHIifSwib3V0cHV0cyI6eyJVcCBWb2x1bWUiOiIjMDBiMDYxIiwiRG93biBWb2x1bWUiOiIjRkYzMzNBIn0sInBhbmVsIjoiY2hhcnQiLCJwYXJhbWV0ZXJzIjp7IndpZHRoRmFjdG9yIjowLjQ1LCJjaGFydE5hbWUiOiJjaGFydCJ9fX0sInBhbmVscyI6eyJjaGFydCI6eyJwZXJjZW50IjoxLCJkaXNwbGF5IjoiXlZJWCIsImNoYXJ0TmFtZSI6ImNoYXJ0IiwidG9wIjowfX0sInNldFNwYW4iOnt9LCJsaW5lV2lkdGgiOjIsInN0cmlwZWRCYWNrZ3JvdWQiOnRydWUsImV2ZW50cyI6dHJ1ZSwiY29sb3IiOiIjMDA4MWYyIiwiZXZlbnRNYXAiOnsiY29ycG9yYXRlIjp7ImRpdnMiOnRydWUsInNwbGl0cyI6dHJ1ZX0sInNpZ0RldiI6e319LCJzeW1ib2xzIjpbeyJzeW1ib2wiOiJeVklYIiwic3ltYm9sT2JqZWN0Ijp7InN5bWJvbCI6Il5WSVgifSwicGVyaW9kaWNpdHkiOjEsImludGVydmFsIjoiZGF5IiwidGltZVVuaXQiOm51bGwsInNldFNwYW4iOnt9fV19)) in the summer of 2009.

## `penguins.json`

Palmer Archipelago (Antarctica) penguin data collected and made available by [Dr. Kristen Gorman](https://www.uaf.edu/cfos/people/faculty/detail/kristen-gorman.php) and the [Palmer Station, Antarctica LTER](https://pal.lternet.edu/), a member of the [Long Term Ecological Research Network](https://lternet.edu/). For more information visit [allisonhorst/penguins](https://github.com/allisonhorst/penguins) on GitHub.

## `platformer-terrain.json`

Assets from the video game [Celeste](http://www.celestegame.com/).

## `political-contributions.json`

## `population.json`

## `seattle-weather.csv`

Data from [NOAA](https://www.ncdc.noaa.gov/cdo-web/datatools/records). Daily weather records with metric units. Transformed using `/scripts/weather.py`. We synthesized the categorical "weather" field from multiple fields in the original dataset. This data is intended for instructional purposes.

## `seattle-weather-hourly-normals.csv`

Data from [NOAA](https://www.ncdc.noaa.gov/cdo-web/datatools/normals). Hourly weather normals with metric units. The 1981-2010 Climate Normals are NCDC's three-decade averages of climatological variables, including temperature and precipitation. Learn more in the [documentation](https://www1.ncdc.noaa.gov/pub/data/cdo/documentation/NORMAL_HLY_documentation.pdf). We only included temperature, wind, and pressure and updated the format to be easier to parse.

## `sp500.csv`

## `sp500-2000.csv`

S&amp;P 500 index values from 2000 to 2020, retrieved from [Yahoo Finance](https://finance.yahoo.com/quote/%5EDJI/history/).

## `stocks.csv`

## `unemployment-across-industries.json`

## `unemployment.tsv`

## `us-10m.json`

## `us-employment.csv`

In the mid 2000s the global economy was hit by a crippling recession. One result: Massive job losses across the United States. The downturn in employment, and the slow recovery in hiring that followed, was tracked each month by the [Current Employment Statistics](https://www.bls.gov/ces/) program at the U.S. Bureau of Labor Statistics.

This file contains the monthly employment total in a variety of job categories from January 2006 through December 2015. The numbers are seasonally adjusted and reported in thousands. The data were downloaded on Nov. 11, 2018, and reformatted for use in this library.

Totals are included for the [22 "supersectors"](https://download.bls.gov/pub/time.series/ce/ce.supersector) tracked by the BLS. The "nonfarm" total is the category typically used by economists and journalists as a stand-in for the country's employment total.

A calculated "nonfarm_change" column has been appended with the month-to-month change in that supersector's employment. It is useful for illustrating how to make bar charts that report both negative and positive values.

## `volcano.json`

Maunga Whau (Mt Eden) is one of about 50 volcanos in the Auckland volcanic field. This data set gives topographic information for Maunga Whau on a 10m by 10m grid. Digitized from a topographic map by Ross Ihaka, adapted from [R datasets](https://stat.ethz.ch/R-manual/R-patched/library/datasets/html/volcano.html). These data should not be regarded as accurate.

## `weather.json`

Instructional dataset showing actual and predicted temperature data.

## `weather.csv`

Data from [NOAA](http://www.ncdc.noaa.gov/cdo-web/datatools/findstation). Transformed using `/scripts/weather.py`. We synthesized the categorical "weather" field from multiple fields in the original dataset. This data is intended for instructional purposes.

## `wheat.json`

In an 1822 letter to Parliament, [William Playfair](https://en.wikipedia.org/wiki/William_Playfair), a Scottish engineer who is often credited as the founder of statistical graphics, published [an elegant chart on the price of wheat](http://dh101.humanities.ucla.edu/wp-content/uploads/2014/08/Vis_2.jpg). It plots 250 years of prices alongside weekly wages and the reigning monarch. He intended to demonstrate that “never at any former period was wheat so cheap, in proportion to mechanical labour, as it is at the present time.”

## `windvectors.csv`

Simulated wind patterns over northwestern Europe.

## `world-110m.json`

## `zipcodes.csv`

GeoNames.org
