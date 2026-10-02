# example1

PS C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash> git --no-pager diff --no-index -- `
>> "structure/Arges/Commons Dashboard/views/data_availability.py" `
>> "../arges_commons_dashboard/views/data_availability.py"
warning: in the working copy of '../arges_commons_dashboard/views/data_availability.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/structure/Arges/Commons Dashboard/views/data_availability.py b/../arges_commons_dashboard/views/data_availability.py
index 6bbd245..7d09621 100644
--- a/structure/Arges/Commons Dashboard/views/data_availability.py
+++ b/../arges_commons_dashboard/views/data_availability.py
@@ -49,7 +49,6 @@ ASSETS = {
 # HELPERS
 # =============================================================================
 
-
 def clean_value(value):
     """Return a clean string representation of a cell value."""
 
@@ -237,7 +236,10 @@ def render_location_asset(title, status, locations):
         if number_locations == 1:
             expander_label = f"View 1 {title.lower()} location"
         else:
-            expander_label = f"View {number_locations} " f"{title.lower()} locations"
+            expander_label = (
+                f"View {number_locations} "
+                f"{title.lower()} locations"
+            )
 
         with st.expander(expander_label):
             render_location_list(locations)
@@ -252,7 +254,6 @@ def render_location_asset(title, status, locations):
 # AVAILABILITY MATRIX
 # =============================================================================
 
-
 def create_availability_matrix(df):
     """Create the compact study-level availability matrix."""
 
@@ -276,9 +277,18 @@ def create_availability_matrix(df):
         }
 
         if "Study Name" in study_df.columns:
-            names = study_df["Study Name"].dropna().astype(str).str.strip()
+            names = (
+                study_df["Study Name"]
+                .dropna()
+                .astype(str)
+                .str.strip()
+            )
 
-            row["Study"] = names.iloc[0] if not names.empty else ""
+            row["Study"] = (
+                names.iloc[0]
+                if not names.empty
+                else ""
+            )
 
         # -------------------------------------------------------------
         # Standard availability fields
@@ -339,7 +349,6 @@ def status_symbol(value):
 # KPI CALCULATIONS
 # =============================================================================
 
-
 def count_studies_with_asset(df, asset_name):
     """Count studies where an asset is available."""
 
@@ -375,7 +384,6 @@ def count_studies_with_asset(df, asset_name):
 # DATA LOCATIONS
 # =============================================================================
 
-
 def render_data_locations(df):
     """
     Show detailed locations when exactly one study is selected.
@@ -387,17 +395,25 @@ def render_data_locations(df):
     if "Study ID" not in df.columns:
         return
 
-    study_ids = df["Study ID"].dropna().astype(str).unique()
+    study_ids = (
+        df["Study ID"]
+        .dropna()
+        .astype(str)
+        .unique()
+    )
 
     if len(study_ids) != 1:
         st.info(
-            "Select a single study from the sidebar " "to view detailed data locations."
+            "Select a single study from the sidebar "
+            "to view detailed data locations."
         )
         return
 
     study_id = study_ids[0]
 
-    study_df = df[df["Study ID"].astype(str) == study_id].copy()
+    study_df = df[
+        df["Study ID"].astype(str) == study_id
+    ].copy()
 
     # -------------------------------------------------------------------------
     # Study identification
@@ -407,7 +423,12 @@ def render_data_locations(df):
 
     if "Study Name" in study_df.columns:
 
-        names = study_df["Study Name"].dropna().astype(str).str.strip()
+        names = (
+            study_df["Study Name"]
+            .dropna()
+            .astype(str)
+            .str.strip()
+        )
 
         if not names.empty:
             study_name = names.iloc[0]
@@ -444,7 +465,6 @@ def render_data_locations(df):
 # MAIN RENDER
 # =============================================================================
 
-
 def render(filtered, data):
 
     # -------------------------------------------------------------------------
@@ -480,17 +500,31 @@ def render(filtered, data):
     # KPI CARDS
     # -------------------------------------------------------------------------
 
-    number_studies = df["Study ID"].nunique() if "Study ID" in df.columns else 0
+    number_studies = (
+        df["Study ID"].nunique()
+        if "Study ID" in df.columns
+        else 0
+    )
 
-    sdtm_available = len(get_locations(df, "SDTM/ADaM Location"))
+    sdtm_available = len(
+    get_locations(df, "SDTM/ADaM Location")
+    )
 
-    ard_available = len(get_locations(df, "ARD Location"))
+    ard_available = len(
+    get_locations(df, "ARD Location")
+    )
 
-    annotations_available = len(get_locations(df, "Annotations Location"))
+    annotations_available = len(
+    get_locations(df, "Annotations Location")
+    )
 
-    clinical_gt_available = len(get_locations(df, "Clinical GT Location"))
+    clinical_gt_available = len(
+    get_locations(df, "Clinical GT Location")
+    )
 
-    feature_vectors_available = len(get_locations(df, "Feature Vectors Location"))
+    feature_vectors_available = len(
+    get_locations(df, "Feature Vectors Location")
+    )
 
     c1, c2, c3, c4, c5, c6 = st.columns(6)
 
@@ -551,15 +585,17 @@ def render(filtered, data):
         status_columns = [
             column
             for column in display_matrix.columns
-            if column
-            not in [
+            if column not in [
                 "Study ID",
                 "Study",
             ]
         ]
 
         for column in status_columns:
-            display_matrix[column] = display_matrix[column].apply(status_symbol)
+            display_matrix[column] = (
+                display_matrix[column]
+                .apply(status_symbol)
+            )
 
         show_table(
             display_matrix,
PS C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash> "
