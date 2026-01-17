# Glossary

A disciplined vocabulary for the data platform.

| Term | Definition |
|------|------------|
| **Universe** | The total population or phenomenon to which a dataset's values apply. |
| **Reference Unit** | An identifiable entity used to index data (e.g., geo area, facility, school, program). |
| **Reference System** | A versioned catalogue of reference units with optional crosswalks. |
| **Reference System Version** | A snapshot of units valid for a time period. |
| **Geographic Unit** | A reference unit with spatial identity (polygon or point). |
| **Geography System** | A reference system specialized for geographic units, with geometry type and hierarchy. |
| **Dimension** | A categorical variable used to classify or filter data (e.g., age group, sex). |
| **Measure** | A numeric variable that is additive across dimensions (e.g., count, population). |
| **Indicator** | A derived value computed from one or more measures using a defined methodology. |
| **Observation (Microdata)** | A single recorded instance of data collection (e.g., one person, one visit). |
| **Aggregate** | A summary computed by grouping observations along dimensions. |
| **Dataset** | A structured collection of data values with shared dimensions, measures, and metadata. |
| **Study** | A bounded data collection effort defined by universe, methodology, and time frame. |
| **Instrument** | The tool or protocol used to collect data (e.g., questionnaire, survey form). |
| **Domain** | The allowed set of values for a variable. |
| **Methodology** | The formal description of how data was collected, processed, and validated. |
| **Provenance** | The origin, ownership, and transformation history of a dataset. |
| **Comparability** | The degree to which two datasets can be meaningfully compared. |
| **Data Product** | The unit dashboards consume; a dataset at a specific grain with declared variables. |
| **Grain** | What one row means (e.g., geography × sex × age_group × year). |
| **Crosswalk** | A mapping between two reference system versions (e.g., boundary changes, facility registry updates). |
| **Suppression** | The hiding of small counts to protect privacy or prevent disclosure risk. |
