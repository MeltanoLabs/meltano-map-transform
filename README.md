# `meltano-map-transformer`

A map transformer which implements the [`Stream Maps` capability](https://sdk.meltano.com/en/latest/stream_maps.html) from Meltano's tap and target SDK: https://sdk.meltano.com/

This mapper plugin is fully compliant with the Singer Spec and can be placed in between any Singer tap and target.

## Capabilities

* `stream-maps`

## Settings

| Setting     | Required | Default | Description |
|:------------|:--------:|:-------:|:------------|
| stream_maps | True     | None    | Stream maps |

A full list of supported settings and capabilities is available by running: `meltano-map-transformer --about`
