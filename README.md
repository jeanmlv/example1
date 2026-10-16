# example1

feat: add ARGES Models section and sync latest dashboard updates

## Summary

Synchronized the latest ARGES Commons updates into the Thea Dash repository using `sync_arges_to_thea.ps1`, including the new ARGES Models section, updated clinical data inventory, and dashboard improvements.

## Changes

- **ARGES Models:** Added the new `arges_models.py` view and integrated the `09_ARGES_MODELS` worksheet into the dashboard configuration.
- **Clinical Data Inventory:** Updated `ARGES_COMMONS.xlsx` with the latest available study information and metadata.
- **Overview:** Updated dashboard metrics and variable exploration functionality.
- **Data Availability:** Improved data presentation and visualization.
- **ARD:** Updated ARD processing and supporting Python scripts.
- **UI:** Synchronized dashboard interface and configuration changes.

## Validation

- Successfully synchronized the ARGES Commons repository with Thea Dash.
- Confirmed that the updated files were copied into the Thea Dash project.
- Local application validation to be confirmed before deployment.

## Next Steps

- Review and merge this PR into `dev`.
- Restart the Domino Thea Dash application to deploy the latest changes.
- Verify that the ARGES Models section and updated clinical data are available in the published application.

**Reviewer:** Eric Ho
