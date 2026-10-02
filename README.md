# example1

PS C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash> git diff --no-index -- `
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
:
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
:
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
:
