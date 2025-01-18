import sys
import asyncio

import kubernetes_asyncio as kubernetes

from cloud_provider_mdns.watchers import HTTPRouteWatcher, IngressWatcher
from cloud_provider_mdns.registries import RecordRegistry
from cloud_provider_mdns.nameservers import ZeroConfNameserver


async def main() -> int:
  await kubernetes.config.load_kube_config()
  try:
    record_registry = RecordRegistry()
    zcn = ZeroConfNameserver(record_registry)
    http_route_watcher = HTTPRouteWatcher(record_registry)
    ingress_watcher = IngressWatcher(record_registry)
    async with asyncio.TaskGroup() as tg:
      zcn_task = tg.create_task(zcn.run())
      http_route_watcher_task = tg.create_task(http_route_watcher.run())
      ingress_watcher_task = tg.create_task(ingress_watcher.run())
  except asyncio.CancelledError:
    print('Shut down')
  return 0

def run() -> int:
  sys.exit(asyncio.run(main()))

if __name__ == '__main__':
    run()
