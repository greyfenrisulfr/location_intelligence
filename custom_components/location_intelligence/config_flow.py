"""Config flow for Location Intelligence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_EXCLUDED_PERSON_ENTITIES, DEFAULT_ENTRY_NAME, DOMAIN

if TYPE_CHECKING:
    import voluptuous as vol


def _person_selector_config(options: list[selector.SelectOptionDict]) -> selector.SelectSelector:
    """Build the selector used for excluded person entities."""

    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )



class LocationIntelligenceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Create the single config entry."""

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=DEFAULT_ENTRY_NAME, data={})

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LocationIntelligenceOptionsFlow:
        """Return the options flow for this handler."""

        return LocationIntelligenceOptionsFlow(config_entry)


class LocationIntelligenceOptionsFlow(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage excluded person entity options."""

        import voluptuous as vol

        if user_input is not None:
            selected = sorted(str(entity_id) for entity_id in user_input.get(CONF_EXCLUDED_PERSON_ENTITIES, []))
            return self.async_create_entry(
                title="",
                data={CONF_EXCLUDED_PERSON_ENTITIES: selected},
            )

        current_value = list(self._config_entry.options.get(CONF_EXCLUDED_PERSON_ENTITIES, []))
        person_options = []
        for entity_id in sorted(self.hass.states.async_entity_ids("person")):
            state = self.hass.states.get(entity_id)
            label = state.name if state is not None and state.name else entity_id
            person_options.append(selector.SelectOptionDict(value=entity_id, label=label))

        data_schema: vol.Schema = vol.Schema(
            {
                vol.Optional(
                    CONF_EXCLUDED_PERSON_ENTITIES,
                    default=current_value,
                ): _person_selector_config(person_options)
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
