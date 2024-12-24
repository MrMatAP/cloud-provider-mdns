import sys
import asyncio

import kubernetes_asyncio as kubernetes # type: ignore

from cloud_provider_mdns.watchers import HTTPRouteWatcher
from cloud_provider_mdns.registries import GatewayRegistry, RecordRegistry
from cloud_provider_mdns.nameservers import ZeroConfNameserver


async def main() -> int:
  await kubernetes.config.load_kube_config()
  api = kubernetes.client.CustomObjectsApi()
  try:
    gtw_registry = GatewayRegistry(api)
    record_registry = RecordRegistry()
    zcn = ZeroConfNameserver(record_registry)
    http_route_watcher = HTTPRouteWatcher(api, record_registry, gtw_registry)
    async with asyncio.TaskGroup() as tg:
      #watch_gtw_task = tg.create_task(watch_gtw())
      zcn_task = tg.create_task(zcn.run())
      http_route_watcher_task = tg.create_task(http_route_watcher.run())
  except asyncio.CancelledError:
    print('Shut down')
  return 0

def run() -> int:
  sys.exit(asyncio.run(main()))

if __name__ == '__main__':
    run()
