"""A sample inline mapper app."""

from __future__ import annotations

from typing import TYPE_CHECKING

import singer_sdk.typing as th
from singer_sdk import _singerlib as singer
from singer_sdk.helpers._util import utc_now
from singer_sdk.mapper import PluginMapper
from singer_sdk.mapper_base import InlineMapper

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import PurePath


class StreamTransform(InlineMapper):
    """A map transformer which implements the Stream Maps capability."""

    name = "meltano-map-transformer"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "stream_maps",
            th.ObjectType(
                additional_properties=th.CustomType(
                    {
                        "type": ["object", "string", "null"],
                        "properties": {
                            "__filter__": {"type": ["string", "null"]},
                            "__source__": {"type": ["string", "null"]},
                            "__alias__": {"type": ["string", "null"]},
                            "__else__": {
                                "type": ["string", "null"],
                                "enum": [None, "__NULL__"],
                            },
                            "__key_properties__": {
                                "type": ["array", "null"],
                                "items": {"type": "string"},
                            },
                        },
                        "additionalProperties": {"type": ["string", "null"]},
                    },
                ),
            ),
            required=True,
            description="Stream maps",
        ),
        th.Property(
            "flattening_enabled",
            th.BooleanType(),
            description=(
                "'True' to enable schema flattening and automatically expand nested "
                "properties."
            ),
        ),
        th.Property(
            "flattening_max_depth",
            th.IntegerType(),
            description="The max depth to flatten schemas.",
        ),
    ).to_dict()

    def __init__(
        self,
        *,
        config: dict | PurePath | str | list[PurePath | str] | None = None,
        parse_env_config: bool = False,
        validate_config: bool = True,
    ) -> None:
        """Create a new inline mapper.

        Args:
            config: Mapper configuration. Can be a dictionary, a single path to a
                configuration file, or a list of paths to multiple configuration
                files.
            parse_env_config: Whether to look for configuration values in environment
                variables.
            validate_config: True to require validation of config settings.
        """
        super().__init__(
            config=config,
            parse_env_config=parse_env_config,
            validate_config=validate_config,
        )

        self.mapper = PluginMapper(plugin_config=dict(self.config), logger=self.logger)

    def map_schema_message(
        self,
        message_dict: dict,
    ) -> Generator[singer.Message, None, None]:
        """Map a schema message according to config.

        Args:
            message_dict: A SCHEMA message JSON dictionary.

        Yields:
            Transformed schema messages.
        """
        self._assert_line_requires(message_dict, requires={"stream", "schema"})

        stream_id: str = message_dict["stream"]
        self.mapper.register_raw_stream_schema(
            stream_id,
            message_dict["schema"],
            message_dict.get("key_properties", []),
        )
        for stream_map in self.mapper.stream_maps[stream_id]:
            yield singer.SchemaMessage(
                stream_map.stream_alias,
                stream_map.transformed_schema,
                stream_map.transformed_key_properties,
                message_dict.get("bookmark_keys", []),
            )

    def map_record_message(
        self,
        message_dict: dict,
    ) -> Generator[singer.Message, None, None]:
        """Map a record message according to config.

        Args:
            message_dict: A RECORD message JSON dictionary.

        Yields:
            Transformed record messages.
        """
        self._assert_line_requires(message_dict, requires={"stream", "record"})

        stream_id: str = message_dict["stream"]
        for stream_map in self.mapper.stream_maps[stream_id]:
            mapped_record = stream_map.transform(message_dict["record"])
            if mapped_record is not None:
                yield singer.RecordMessage(
                    stream=stream_map.stream_alias,
                    record=mapped_record,
                    version=message_dict.get("version"),
                    time_extracted=utc_now(),
                )

    def map_state_message(self, message_dict: dict) -> list[singer.Message]:
        """Do nothing to the message.

        Args:
            message_dict: A STATE message JSON dictionary.

        Returns:
            The same state message
        """
        return [singer.StateMessage(value=message_dict["value"])]

    def map_activate_version_message(
        self,
        message_dict: dict,
    ) -> Generator[singer.Message, None, None]:
        """Duplicate the message or alias the stream name as defined in configuration.

        Args:
            message_dict: An ACTIVATE_VERSION message JSON dictionary.

        Yields:
            An ACTIVATE_VERSION for each duplicated or aliased stream.
        """
        self._assert_line_requires(message_dict, requires={"stream", "version"})

        stream_id: str = message_dict["stream"]
        for stream_map in self.mapper.stream_maps[stream_id]:
            yield singer.ActivateVersionMessage(
                stream=stream_map.stream_alias,
                version=message_dict["version"],
            )
