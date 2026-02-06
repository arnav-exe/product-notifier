# TODO
 * figure out how to 'register' each src to main (esp in the future when new sources get added)
 * figure out how to select data source to call based on identifier <- maybe some kind of func that compares 'Product.retailer_name'?

 - RETRIES + EXPONENTIAL BACKOFF WILL HAVE TO BE A FUNCTION DECORATOR OR SMTN GLOBAL - DO NOT IMPLEMENT THIS PER DATASOURCE
 - PASS LOGGER TO EACH DATASOURCE INSTANTIATION, FOR GRANULAR, PER-DATASOURCE LOGGING. FORMAT SHOUDL LOOKE LIKE THIS:
 "{timestamp} [{error_severity} - {data_source}]: {log_message}"
 CAN POTENTIALLY DEFINE THIS IN THE FORMATTER


 - MAJOR RESTRUCTURING REQUIRED:
    - PUT EVERYTHING EXCEPT MAIN INSIDE SRC
    - DEFINE ALL FOLDERS AS PACKAGES (ADD '__init__.py')
    - EDIT IMPORT STATEMENTS TO IMPORT FOLDERS
    - FOR FILES THAT CALL EACH OTHER WITHIN A FOLDER ADD '.' PREFIX
