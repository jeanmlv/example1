# example1

Hi Eric, thanks — I checked the new Thea Dash Prod app and it looks like the latest ARGES Commons updates are now reflected correctly.
Just to make sure I follow the correct workflow going forward: whenever I update the ARGES_COMMONS.xlsx or make changes to the Streamlit dashboard, I’ll first commit and push those changes to the arges-commons repository as usual.
After that, should I run sync_arges_to_thea.ps1 locally to bring those updates into the thea_dash repository, validate thea_dash locally, and then open a PR to merge the changes into main?
Since the new Prod app is using the latest changes from main, I just want to confirm whether merging into main will automatically update/redeploy the Prod app, or if there is an additional deployment step I should follow.
