import sys
import argparse
import asyncio

import kubernetes_asyncio as kubernetes     # type: ignore[import-untyped]

from cloud_provider_mdns.registry import Registry
from cloud_provider_mdns.watchers import HTTPRouteWatcher, GatewayWatcher
from cloud_provider_mdns.nameservers import MulticastNameserver, UnicastNameserver


async def main() -> int:
    parser = argparse.ArgumentParser(prog='cloud_provider_mdns')
    parser.add_argument('--ip',
                        dest='ip',
                        type=str,
                        required=False,
                        default='127.0.0.1',
                        help='IP address of the unicast resolver to update')
    parser.add_argument('--domain',
                        dest='domain',
                        type=str,
                        required=False,
                        default='kube-eng.k8s',
                        help='Domain for unicast DNS updates')
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

    registry = Registry()
    mcast_ns = MulticastNameserver(registry=registry)
    ucast_ns = UnicastNameserver(registry=registry,
                                 ip=args.ip,
                                 domain=args.domain,
                                 key=args.tsig_key,
                                 secret=args.tsig_secret)
    try:
        gw_watcher = GatewayWatcher(registry)
        route_watcher = HTTPRouteWatcher(registry)
        async with asyncio.TaskGroup() as tg:
            gw_watcher_task = tg.create_task(gw_watcher.run())
            route_watcher_task = tg.create_task(route_watcher.run())
        return 0
    except asyncio.CancelledError:
        print('Shut down')
        return 0
    except KeyboardInterrupt:
        print('Keyboard interrupt, shutting down')
        return 0
    finally:
        await mcast_ns.shutdown()
        await ucast_ns.shutdown()



def run() -> int:
    sys.exit(asyncio.run(main()))


if __name__ == '__main__':
    run()
