import sys
import asyncio

import kubernetes_asyncio as kubernetes
from cloud_provider_local.watchers import HTTPRouteWatcher
from cloud_provider_local.nameservers import ZeroConfNameserver

async def main() -> int:
  await kubernetes.config.load_kube_config()
  api = kubernetes.client.CustomObjectsApi()
  try:
    q = asyncio.Queue()
    zcn = ZeroConfNameserver(q)
    http_route_watcher = HTTPRouteWatcher(api, q)
    async with asyncio.TaskGroup() as tg:
      #watch_gtw_task = tg.create_task(watch_gtw())
      zcn_task = tg.create_task(zcn.run())
      http_route_watcher_task = tg.create_task(http_route_watcher.run())
  except asyncio.CancelledError:
    print('Shutting down...')
  return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
