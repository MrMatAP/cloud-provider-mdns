import sys
import argparse
import asyncio

import kubernetes_asyncio as kubernetes

from cloud_provider_mdns.watchers import HTTPRouteWatcher, IngressWatcher
from cloud_provider_mdns.registries import RecordRegistry
from cloud_provider_mdns.nameservers import MulticastNameserver, UnicastNameserver


async def main() -> int:
    parser = argparse.ArgumentParser(prog='cloud_provider_mdns')
    parser.add_argument('--ip',
                        dest='ip',
                        type=str,
                        required=False,
                        default='127.0.0.1',
                        help='IP address of the unicast resolver to update')
    parser.add_argument('--tsig-key',
                        dest='tsig_key',
                        type=str,
                        required=False,
                        help='TSIG key name')
    parser.add_argument('--tsig-secret',
                        dest='tsig_secret',
                        type=str,
                        required=False,
                        help='TSIG secret')
    args = parser.parse_args(sys.argv[1:])
    await kubernetes.config.load_kube_config()
    try:
        record_registry = RecordRegistry()
        mcast_ns = MulticastNameserver(record_registry)
        ucast_ns = UnicastNameserver(record_registry,
                                     ip=args.ip,
                                     key=args.tsig_key,
                                     secret=args.tsig_secret)
        http_route_watcher = HTTPRouteWatcher(record_registry)
        #ingress_watcher = IngressWatcher(record_registry)
        async with asyncio.TaskGroup() as tg:
            mcast_task = tg.create_task(mcast_ns.run())
            ucast_task = tg.create_task(ucast_ns.run())
            http_route_watcher_task = tg.create_task(http_route_watcher.run())
            #ingress_watcher_task = tg.create_task(ingress_watcher.run())
    except asyncio.CancelledError:
        print('Shut down')
        return 0


def run() -> int:
    sys.exit(asyncio.run(main()))


if __name__ == '__main__':
    run()
