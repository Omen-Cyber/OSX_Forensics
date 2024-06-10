# Description

## A tool for extracting OSX files containing artifacts.

Currently has options for db, plist, ips, and segb files.

## How To Use

### Run the script

-d, (--directory) and -t, (--file-type) are required arguments

Pass a file type (db, plist, ips, segb) as an argument

```shell
python file_scraper.py -d /Path/to/input_dir -t {file_type} -o /Path/to/output_file
```

#### For parsing data please refer to the parsing tools tailored to the file type.