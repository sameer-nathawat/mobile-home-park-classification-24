## Introduction
Understanding the built environment is essential to the overall study of population dynamics, grid infrastructure, emergency response, among others. In the United States there are multiple classifications for buildings within the built environment such as residential, signifying family homes while commercial buildings consist of apartments or larger structures which are multi-purpose. While there is a high level of understanding of where these aforementioned structures are located, there is a third class of structures, mobile home parks (MHP) which have been under-represented in the literature despite there being an estimated 2.7 million of them within the United States. Research has shown that individuals who reside in MHP are at higher risk to extreme events due to their location and structural integrity of residence.

## Methodology
### Data
#### Building Footprints
The footprint data leveraged in this study comes from the USA structures dataset. This dataset covers the entirity of the U.S. and is a compilation of footprints which are derived from both satellite and lidar imagery. It was developed by Oak Ridge National Laboratory (ORNL), Federal Emergency Management Agency Geospatial Response Office, and the Department of Homeland Security Science and Technology Directorate.

#### Parcel Information
We leverage a proprietary dataset, Lightbox smart parcels,4 which includes landuse codes for the entirety of the U.S. and are provided through a data agreement for federal use cases. Includes a landuse code for every parcel of land within the U.S. and therefore, we are able to generate a binary feature which distinguishes structures on land classified for MHP versus non-MHP. This feature was added to the footprint dataset for each structure.

#### Morphology
We then follow the workflow presented by Hauser et al. [33] and generate 65 distinct morphology features for each individual building within our dataset. These include geometric, engineered, and contextual features.

### Data Preprocessing
We deploy a pre-processing step which discretizes individual MH from those within a MHP. We leverage the feature n count 100, which is the number of neighbors within a 100m radius. For all structures within our dataset which are identified as a MH, we further filter this metric to have at least a value of 3 for the n count 100 to segment a singular MH from a MH within a MHP. To reduce dimensionality of the dataset, we then ran recursive feature elimination, similar to the approach presented by Adams et al. and leverage a XGBoost regressor.

### Model Development
We apply 4 distinct classifier models Logistic Regresssion, Decision Tree, Random Forest, and XGBoost.
