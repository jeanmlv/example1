# example1

PS C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash> .\sync_arges_to_thea.ps1

==============================================
 ARGES Commons -> Thea Dashboard Sync
==============================================

Source:
C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\..\arges_commons_dashboard

Destination:
C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\structure\Arges\Commons Dashboard

The following items will be synchronized:
  - src
  - views
  - ARGES_COMMONS.xlsx

Continue? (y/n): y

Starting synchronization...


-------------------------------------------------------------------------------
   ROBOCOPY     ::     Robust File Copy for Windows                              
-------------------------------------------------------------------------------

  Started : Friday, October 2, 2026 1:05:15 PM
   Source : C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard\src\
     Dest : C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\structure\Arges\Commons Dashboard\src\

    Files : *.*
            
Exc Files : *.pyc
            
 Exc Dirs : __pycache__
            
  Options : *.* /S /E /DCOPY:DA /COPY:DAT /R:1000000 /W:30 

------------------------------------------------------------------------------

                           6    C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard\src\
100%        Older                   6450        ard_loader.py
100%        Older                    598        config.py
100%        Older                   1061        data_loader.py
100%        New File                1821        filters.py
100%        Older                   5551        ui.py
100%        Older                      0        __init__.py

------------------------------------------------------------------------------

               Total    Copied   Skipped  Mismatch    FAILED    Extras
    Dirs :         2         0         2         0         0         0
   Files :         6         6         0         0         0         0
   Bytes :    15.1 k    15.1 k         0         0         0         0
   Times :   0:00:00   0:00:00                       0:00:00   0:00:00


   Speed :             143,342 Bytes/sec.
   Speed :               8.202 MegaBytes/min.
   Ended : Friday, October 2, 2026 1:05:15 PM


-------------------------------------------------------------------------------
   ROBOCOPY     ::     Robust File Copy for Windows                              
-------------------------------------------------------------------------------

  Started : Friday, October 2, 2026 1:05:17 PM
   Source : C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard\views\
     Dest : C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash\structure\Arges\Commons Dashboard\views\

    Files : *.*
            
Exc Files : *.pyc
            
 Exc Dirs : __pycache__
            
  Options : *.* /S /E /DCOPY:DA /COPY:DAT /R:1000000 /W:30 

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
100%        Older                      0        __init__.py

------------------------------------------------------------------------------

               Total    Copied   Skipped  Mismatch    FAILED    Extras
    Dirs :         2         0         2         0         0         0
   Files :        10        10         0         0         0         0
   Bytes :    33.4 k    33.4 k         0         0         0         0
   Times :   0:00:00   0:00:00                       0:00:00   0:00:00


   Speed :             233,238 Bytes/sec.
   Speed :              13.346 MegaBytes/min.
   Ended : Friday, October 2, 2026 1:05:18 PM


==============================================
 Synchronization completed
==============================================

Review the changes with:

    git status
    git diff --stat

Nothing has been committed or pushed.

PS C:\Users\JMende95\OneDrive - JNJ\Desktop\thea_dash> 
