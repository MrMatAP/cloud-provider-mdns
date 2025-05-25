import sys
import pathlib
import asyncio

import pydantic
import pydantic_settings

import kubernetes_asyncio as kubernetes     # type: ignore[import-untyped]
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from cloud_provider_mdns import console
from cloud_provider_mdns.registry import Registry
from cloud_provider_mdns.watchers import HTTPRouteWatcher, GatewayWatcher, IngressWatcher
from cloud_provider_mdns.nameservers import MulticastNameserver, UnicastNameserver


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(cli_parse_args=True,
                                                        cli_prog_name='cloud-provider-mdns',
                                                        cli_kebab_case=True,
                                                        cli_enforce_required=True,
                                                        env_prefix='CLOUD_PROVIDER_MDNS_')
    multicast_enable: pydantic_settings.CliImplicitFlag[bool] = pydantic.Field(default=False,
                                                                               description='Enable multicast DNS updates')
    unicast_enable: pydantic_settings.CliImplicitFlag[bool] = pydantic.Field(default=False,
                                                                             description='Enable unicast DNS updates')
    unicast_ip: str = pydantic.Field(default='127.0.0.1',
                                     description='IP address of the unicast DNS server to update')
    unicast_domain: str = pydantic.Field(default='k8s',
                                         description='Register only names ending in this domain within unicast DNS')
    unicast_key_name: str = pydantic.Field(default='',
                                           description='The TSIG key name')
    unicast_key_secret: str = pydantic.Field(default='',
                                             description='The TSIG key secret')

    @classmethod
    def settings_customise_sources(cls, settings_cls: type[BaseSettings],
                                   init_settings: PydanticBaseSettingsSource,
                                   env_settings: PydanticBaseSettingsSource,
                                   dotenv_settings: PydanticBaseSettingsSource,
                                   file_secret_settings: PydanticBaseSettingsSource) -> tuple[
        PydanticBaseSettingsSource, ...]:
        return (init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
                pydantic_settings.JsonConfigSettingsSource(settings_cls,
                                                           json_file=pathlib.Path('~/etc/cloud-provider-mdns.json').expanduser().resolve(),
                                                           json_file_encoding='utf-8'))


async def main() -> int:
    settings = Settings()
    await kubernetes.config.load_kube_config()

    registry = Registry()
    if settings.multicast_enable:
        mcast_ns = MulticastNameserver(registry=registry)
    else:
        mcast_ns = None
    if settings.unicast_enable:
        ucast_ns = UnicastNameserver(registry=registry,
                                     ip=settings.unicast_ip,
                                     domain=settings.unicast_domain,
                                     key=settings.unicast_key_name,
                                     secret=settings.unicast_key_secret)
    else:
        ucast_ns = None
    if mcast_ns is None and ucast_ns is None:
        console.print('[bold yellow]No nameservers are enabled. It will only show discovery[/bold yellow]')
    try:
        gw_watcher = GatewayWatcher(registry)
        route_watcher = HTTPRouteWatcher(registry)
        ingress_watcher = IngressWatcher(registry)
        async with asyncio.TaskGroup() as tg:
            gw_watcher_task = tg.create_task(gw_watcher.run())
            route_watcher_task = tg.create_task(route_watcher.run())
            ingress_watcher_task = tg.create_task(ingress_watcher.run())
        return 0
    except asyncio.CancelledError:
        print('Shut down')
        return 0
    except KeyboardInterrupt:
        print('Keyboard interrupt, shutting down')
        return 0
    finally:
        if mcast_ns is not None:
            await mcast_ns.shutdown()
        if ucast_ns is not None:
            await ucast_ns.shutdown()



def run() -> int:
    sys.exit(asyncio.run(main()))


if __name__ == '__main__':
    run()
