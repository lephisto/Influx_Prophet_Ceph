# Influx Prophet for Ceph

Forecast Storage Usage for Ceph Cluster Pools. This is supposed to be an Enterprise Feature of Enterprise Storage Vendors. Now you can build it your own.

Reads your historics ceph pool utilisation and generates forecast and writes it back to InfluxDB. From there you can easily integrate it into existing Dashboards or set alterts.

1. Load notebook into jupyter.
2. Adjust variables
3. Run



![](https://github.com/lephisto/Influx_Prophet_Ceph/raw/master/screenshots/fbprophet_plot.png)

![](https://github.com/lephisto/Influx_Prophet_Ceph/raw/master/screenshots/Grafana_Capacity_forecast.png)

This is just a real-world example on a Ceph Storage Pool. Storage Usage is usually subject to a strong seasonality and therefor a pretty good showcase for timeseries forecasting. Daily and weekly Snapshots + snapshot trimming usually produces a "heartbeat" with a high seasonality. It should easily be able to adapt to ZFS or any other Type of Storage.

This notebook uses the Python-InfluxDB Client Library and Facebooks Prophet to make forecasts. The basic approach is derived from the quick-start example notebook in the prophet repo.

Thanks do anaisdg for providing a basic sample on how to glue InfluxDB with fbProphet.