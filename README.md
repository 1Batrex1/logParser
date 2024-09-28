# logParser
Program to parse logs from any file with custom configuration
## How to use

### Configuration

Create a configuration file with the following format with extension .ini:

```
[Main_config]
	[regexp]
		regexp = <(.*?):\s+(\w+):\s+(.*)>([\s\S]*?)<

	[regexp_column_map] < Column name and position in the log file >
		Server = 1
		Date = LOG_TIME_FID
		Log_text = 4
		Log_Level = LOG_MAP_FID
	[log_level_map] < Log level and its corresponding number >
		LOG_MAP_FID = 2
		level1 = "Info"
		level2 = "Warning"
		level3 = "Alert"
	[time_map] < Time format and its corresponding number >
		LOG_TIME_FID = 3
		TIME_FORMAT = %%a %%b %%d %%H:%%M:%%S %%Y
		REQ_FORMAT = %%Y/%%m/%%d %%H:%%M:%%S
```

Put the configuration file in the /configs directory.

### Running the program

When running the program you have to load the configuration file and the log file to parse from the
menu.

After that click load data to table button if your regex is correct the data will be loaded to the table.

You can also filter the data by the log level and export data to a csv file.





