# Influx Prophet for Ceph

Forecast Storage Usage for Ceph Cluster Pools. This is supposed to be an Enterprise Feature of Enterprise Storage Vendors. Now you can build it your own.

Reads your historics ceph pool utilisation and generates forecast and writes it back to InfluxDB. From there you can easily integrate it into existing Dashboards or set alterts.

1. Load notebook into jupyter.
2. Adjust variables
3. Run

![](screenhots/fbprophet_plot.png)