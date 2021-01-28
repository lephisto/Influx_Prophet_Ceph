# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# Jupyter Notebook to achive capacity forecast for Ceph Storage Pools.
# To make this work you have to:
# 
# 1. Enable Telegraf Telemetry in Ceph:
# <pre>
# ceph mgr module enable telegraf
# ceph telegraf config-set address udp://:8094
# ceph telegraf config-set interval 10
# </pre>
# 
# Additionally you have to Configure your telegraf to forward those broadcasts to your InfluxDB Instance:
# 
# Create a file like /etc/telegraf/telegraf.d/ceph.conf with the following content:
# 
# <pre>
# [[inputs.socket_listener]] 
#   service_address = "udp://:8094" 
#   data_format = "influx"
# </pre>
# 
# 
# 2. Adjust the Variables in this script to match your Environment: Adjust the fsid (UUID for the Pool you want to Monitor) and the InfluxDB Credentials
# 
# 3. After tunning this Notebook you should have a new measurement called ceph_cluster_stats_fc for the next 365 days, based on the Data of the past 365 days. You can now easily create a Grafana Dashboard from it.
# 
# This is just a real-world example on a Ceph Storage Pool. Storage Usage is usually subject to a strong seasonality and therefor a pretty good showcase for timeseries forecasting. Daily and weekly Snapshots + snapshot trimming usually produces a "heartbeat" with a high seasonality. It should easily be able to adapt to ZFS or any other Type of Storage.
# 
# 
# This notebook uses the <a href="https://v2.docs.influxdata.com/v2.0/reference/client-libraries/">Python-InfluxDB Client Library</a> and Facebooks Prophet to make forecasts. The basic approach is derived from the <a href="https://github.com/facebook/prophet/blob/master/notebooks/quick_start.ipynb">quick-start example notebook </a> in the <a href="https://github.com/facebook/prophet">prophet repo</a>.
# 
# Thanks do anaisdg for providing a basic sample on how to glue InfluxDB with fbProphet.

# %%
import pandas as pd
import time
from datetime import datetime
from fbprophet import Prophet


# %%
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Forecast Configuration
dst_measurement_name = "ceph_cluster_stats_fc"

# Ceph Pool Info
fsid = "688287b9-0f7b-4c6b-9f93-ecdadf0af36b"

# Influx Database Credentials
url = "http://odo.fan:8086"
token = "f'root:root'"
bucket = "telegraf/autogen"
org = "-"
client = InfluxDBClient(url=url, token=token, org=org)
query_api = client.query_api()
write_api = client.write_api(write_options=SYNCHRONOUS)


# %%
query = 'from(bucket: "' + bucket + '")'         '  |> range(start: -365d)'         '  |> filter(fn: (r) => r._measurement == "ceph_cluster_stats" and r.type_instance == "data_bytes" and r.fsid == "' + fsid + '")'         '  |> aggregateWindow(fn: mean, every: 1h, createEmpty: false)'



result = client.query_api().query(org="-", query=query)


# %%
raw = []
for table in result:
    for record in table.records:
        raw.append((record.get_value(), record.get_time()))


# %%
raw[0:5]


# %%
print()
print("=== influxdb query into dataframe ===")
print()
df=pd.DataFrame(raw, columns=['y','ds'], index=None)
df['ds'] = df['ds'].values.astype('<M8[D]')
df.head()

# %% [markdown]
# We fit the model by instantiating a new `Prophet` object.  Any settings to the forecasting procedure are passed into the constructor.  Then you call its `fit` method and pass in the historical dataframe. Fitting should take 1-5 seconds.

# %%
#m = Prophet()
#m.fit(df)
m = Prophet(weekly_seasonality=True, yearly_seasonality=True,changepoint_prior_scale=0.0001).fit(df)

# %% [markdown]
# Predictions are then made on a dataframe with a column `ds` containing the dates for which a prediction is to be made. You can get a suitable dataframe that extends into the future a specified number of days using the helper method `Prophet.make_future_dataframe`. By default it will also include the dates from the history, so we will see the model fit as well. 

# %%
future = m.make_future_dataframe(periods=365*24, freq="H")
future.tail()

# %% [markdown]
# The `predict` method will assign each row in `future` a predicted value which it names `yhat`.  If you pass in historical dates, it will provide an in-sample fit. The `forecast` object here is a new dataframe that includes a column `yhat` with the forecast, as well as columns for components and uncertainty intervals.

# %%
forecast = m.predict(future)
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()


# %%
forecast['measurement'] = dst_measurement_name
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper','measurement']].head()

# %% [markdown]
# You can plot the forecast by calling the `Prophet.plot` method and passing in your forecast dataframe.

# %%
from fbprophet.plot import add_changepoints_to_plot
fig1 = m.plot(forecast)
a = add_changepoints_to_plot(fig1.gca(),m,forecast)


# %%
fig2 = m.plot_components(forecast)


# %%
cp = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper','measurement']].copy()
lines = [str(cp["measurement"][d]) 
         + ",type=forecast" 
         + " " 
         + "yhat=" + str(cp["yhat"][d]) + ","
         + "yhat_lower=" + str(cp["yhat_lower"][d]) + ","
         + "yhat_upper=" + str(cp["yhat_upper"][d])
         + " " + str(int(time.mktime(cp['ds'][d].timetuple()))) + "000000000" for d in range(len(cp))]


# %%
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS

_write_client = client.write_api(write_options=WriteOptions(batch_size=1000, 
                                                            flush_interval=10000,
                                                            jitter_interval=2000,
                                                            retry_interval=5000))

_write_client.write(bucket, org, lines)

lines[0:10]

# %% [markdown]
# To close client:

# %%
_write_client.__del__()
client.__del__()


