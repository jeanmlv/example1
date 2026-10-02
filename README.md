# example1

PS C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash> .\sync_arges_to_thea.ps1

==============================================
 ARGES Commons -> Thea Dashboard Sync
==============================================

Source:
C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\..\arges_commons_dashboard

Destination:
C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\structure\Arges\Commons Dashboard

Checking ARGES Commons repository...

ARGES Commons working tree is clean.
ARGES Commons branch: main

Checking ARGES Commons remote...

ARGES Commons upstream: origin/main
ARGES Commons is synchronized with remote.

The following items will be synchronized:

  - src
  - views
  - ARGES_COMMONS.xlsx

Excluded:

  - __pycache__
  - *.pyc

IMPORTANT:
ARGES Commons is the source of truth.

Files inside src/ and views/ that do not exist
in ARGES Commons may be removed from the Thea copy.

Continue synchronization? (y/n): y

Starting synchronization...

----------------------------------------------
 Synchronizing src
----------------------------------------------


-------------------------------------------------------------------------------
   ROBOCOPY     ::     Robust File Copy for Windows                              
-------------------------------------------------------------------------------

  Started : Friday, October 2, 2026 1:45:25 PM
   Source : C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard\src\
     Dest : C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\structure\Arges\Commons Dashboard\src\

    Files : *.*
            
Exc Files : *.pyc
            
 Exc Dirs : __pycache__
            
  Options : *.* /S /E /DCOPY:DA /COPY:DAT /PURGE /MIR /R:2 /W:2 

------------------------------------------------------------------------------

                           6    C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard\src\
100%        Older                   6450        ard_loader.py
100%        Older                    598        config.py
100%        Older                   1061        data_loader.py
100%        New File                1821        filters.py
100%        Older                   5551        ui.py

------------------------------------------------------------------------------

               Total    Copied   Skipped  Mismatch    FAILED    Extras
    Dirs :         2         0         2         0         0         0
   Files :         6         5         1         0         0         0
   Bytes :    15.1 k    15.1 k         0         0         0         0
   Times :   0:00:00   0:00:00                       0:00:00   0:00:00


   Speed :             159,597 Bytes/sec.
   Speed :               9.132 MegaBytes/min.
   Ended : Friday, October 2, 2026 1:45:25 PM


src synchronized successfully.

----------------------------------------------
 Synchronizing views
----------------------------------------------


-------------------------------------------------------------------------------
   ROBOCOPY     ::     Robust File Copy for Windows                              
-------------------------------------------------------------------------------

  Started : Friday, October 2, 2026 1:45:28 PM
   Source : C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard\views\
     Dest : C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\structure\Arges\Commons Dashboard\views\

    Files : *.*
            
Exc Files : *.pyc
            
 Exc Dirs : __pycache__
            
  Options : *.* /S /E /DCOPY:DA /COPY:DAT /PURGE /MIR /R:2 /W:2 

------------------------------------------------------------------------------

                          10    C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard\views\
100%        Older                   1682        ard.py
100%        Older                    785        data_analysis.py
100%        Older                  14224        data_availability.py
100%        Older                   1318        data_splits.py
100%        Older                   1126        external_data.py
100%        Older                  11361        overview.py
100%        Older                   1202        processing.py
100%        Older                    786        studies_assets.py
100%        Older                   1802        variable_definitions.py

------------------------------------------------------------------------------

               Total    Copied   Skipped  Mismatch    FAILED    Extras
    Dirs :         2         0         2         0         0         0
   Files :        10         9         1         0         0         0
   Bytes :    33.4 k    33.4 k         0         0         0         0
   Times :   0:00:00   0:00:00                       0:00:00   0:00:00


   Speed :             228,573 Bytes/sec.
   Speed :              13.079 MegaBytes/min.
   Ended : Friday, October 2, 2026 1:45:28 PM


views synchronized successfully.

----------------------------------------------
 Synchronizing ARGES_COMMONS.xlsx
----------------------------------------------

ARGES_COMMONS.xlsx synchronized successfully.

==============================================
 Synchronization completed
==============================================

ARGES source branch:
  main

ARGES upstream:
  origin/main

Review the Thea Dashboard changes with:

    git status

    git diff --stat

    git diff

IMPORTANT:
Nothing has been committed or pushed to Thea.

Recommended next steps:

  1. Review git status
  2. Review git diff --stat
  3. Review important code changes
  4. Test the dashboard
  5. Commit the Thea changes
  6. Push the Thea branch
  7. Open/update the PR
