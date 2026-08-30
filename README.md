# UC Admissions Data Analysis Methodology

### Data Sourcing & Preparation

This analysis relies on publicly available University of California admissions datasets, primarily evaluating the Fall 2025 application cycle. The data was processed using Python and Pandas to ensure accurate filtering and aggregation.

* **Filtering Parameters:** Data was strictly scoped to `fall_term = 2025` unless multi-year historical analysis was required.
* **Missing Data Handling:** Schools missing formal `school_type` classifications (recorded as `NaN`) were manually verified and included in public school aggregates if they functioned as public/charter institutions (e.g., Encinal High School).

### Calculating Unique High Schools

To accurately count the number of distinct physical California public high schools sending applicants to the UC system, the methodology prioritizes system-wide applicant rows over raw string matching.

* **De-duplication:** Filtered the dataset exclusively for `campus = 'Universitywide'` to prevent double-counting schools that sent applicants to multiple UC branches.
* **Physical Campus Verification:** Ignored standard string counts of the `high_school` column, as several distinct schools in different cities share identical names (e.g., Abraham Lincoln High School). Relying on the `Universitywide` summary rows provided the true count of 248 physical locations.

### Measuring School Outperformance

To determine which high schools outperformed their expected admission outcomes, the analysis utilized the `admit_rate_residual` metric over a multi-year window (2022–2025).

* **Control Variables:** The residual metric isolates actual admissions performance by controlling for school size, applicant GPA, a-g course completion rates, and poverty levels.
* **Aggregation:** Calculated the mean residual for each target school across the 4-year window to find the highest sustained positive variance from the expected admit rate.

### Socioeconomic Equity Analysis

To evaluate the impact of socioeconomic status on aggregate UC Berkeley admit rates, high schools were segmented into extreme cohorts using the Free or Reduced-Price Meal (`frpm_pct`) metric.

* **Low-Poverty Cohort:** High schools where fewer than 25% of students qualify for FRPM.
* **High-Poverty Cohort:** High schools where over 75% of students qualify for FRPM.
* **Aggregate Calculation:** Summed all admits within each cohort and divided by the sum of all applicants in that cohort to find the true aggregate rate, preventing smaller high schools from skewing the final percentages.
