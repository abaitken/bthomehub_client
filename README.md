# Home Hub Client

A Python client that can interact with BT Home Hub routers.

At present, only device listing and some status information has been implemented.

## Usage

```python
import bthomeclient

client = bthomeclient.BtHomeClient()

client.authenticate()

print(client.get_devices())

values = client.get_values()
print(values)

print('Downstream = ' + str(values["Device/DSL/Channels/Channel[@uid='1']/DownstreamCurrRate"]))
print('Upstream = ' + str(values["Device/DSL/Channels/Channel[@uid='1']/UpstreamCurrRate"]))

```