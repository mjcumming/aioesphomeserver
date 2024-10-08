import asyncio
import random
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, ClimateEntity, ListEntitiesClimateResponse, ClimateStateResponse
from aioesphomeapi.api_pb2 import ClimateMode, ClimateFanMode, ClimateSwingMode, ClimateAction, ClimatePreset

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class FullFeatureClimateEntity(ClimateEntity):
    """
    A full-featured climate control entity that handles temperature settings, fan modes, swing modes,
    presets, humidity, and interacts with external requests.

    Attributes:
        device (Device): The device instance this entity is associated with.
        mode (ClimateMode): The current mode of the climate entity.
        target_temperature (float): The desired target temperature.
        target_temperature_low (float): The desired low target temperature (for two-point control).
        target_temperature_high (float): The desired high target temperature (for two-point control).
        current_temperature (float): The current temperature reading.
        fan_mode (ClimateFanMode): The current fan mode.
        swing_mode (ClimateSwingMode): The current swing mode.
        action (ClimateAction): The current action being performed.
        preset (ClimatePreset): The current preset being used.
        current_humidity (float): The current humidity reading.
        target_humidity (float): The desired target humidity.
    """

    DOMAIN = "climate"

    def __init__(self, device, name, object_id, supported_modes, visual_min_temperature, visual_max_temperature, visual_target_temperature_step, **kwargs):
        """
        Initialize a FullFeatureClimateEntity instance.

        Args:
            device (Device): The device instance this entity is associated with.
            name (str): The name of the climate entity.
            object_id (str): The object ID of the climate entity.
            supported_modes (list[int]): The list of supported climate modes.
            visual_min_temperature (float): The minimum temperature displayed to the user.
            visual_max_temperature (float): The maximum temperature displayed to the user.
            visual_target_temperature_step (float): The step value for adjusting the target temperature.
            **kwargs: Arbitrary keyword arguments.
        """
        # Filter out kwargs that are not required by the base class
        base_kwargs = {k: v for k, v in kwargs.items() if k in [
            'unique_id', 'icon', 'entity_category'
        ]}

        super().__init__(
            name=name,
            object_id=object_id,
            supported_modes=supported_modes,
            visual_min_temperature=visual_min_temperature,
            visual_max_temperature=visual_max_temperature,
            visual_target_temperature_step=visual_target_temperature_step,
            **base_kwargs
        )
        self.device = device
        self.supported_modes = supported_modes
        self.visual_min_temperature = visual_min_temperature
        self.visual_max_temperature = visual_max_temperature
        self.visual_target_temperature_step = visual_target_temperature_step
        self.supports_two_point_target_temperature = kwargs.get('supports_two_point_target_temperature', False)
        self.supports_fan_mode = kwargs.get('supports_fan_mode', True)
        self.supports_swing_mode = kwargs.get('supports_swing_mode', True)
        self.supports_action = kwargs.get('supports_action', True)
        self.supports_current_temperature = kwargs.get('supports_current_temperature', True)
        self.supports_current_humidity = kwargs.get('supports_current_humidity', False)
        self.supports_target_humidity = kwargs.get('supports_target_humidity', False)
        self.supports_preset = kwargs.get('supports_preset', True)
        self.visual_min_humidity = kwargs.get('visual_min_humidity', 0.0)
        self.visual_max_humidity = kwargs.get('visual_max_humidity', 100.0)

        self.mode = ClimateMode.CLIMATE_MODE_OFF
        self.target_temperature = self.visual_min_temperature
        self.target_temperature_low = self.visual_min_temperature if self.supports_two_point_target_temperature else None
        self.target_temperature_high = self.visual_max_temperature if self.supports_two_point_target_temperature else None
        self.current_temperature = self.visual_min_temperature
        self.fan_mode = ClimateFanMode.CLIMATE_FAN_OFF
        self.swing_mode = ClimateSwingMode.CLIMATE_SWING_OFF
        self.action = ClimateAction.CLIMATE_ACTION_OFF
        self.preset = ClimatePreset.CLIMATE_PRESET_NONE
        self.current_humidity = 0
        self.target_humidity = 0

        logging.debug('Initialized FullFeatureClimateEntity with mode %s, min_temp %s, max_temp %s', self.mode, self.visual_min_temperature, self.visual_max_temperature)

    async def build_list_entities_response(self) -> ListEntitiesClimateResponse:
        """
        Build and return the response for listing this climate entity.

        Returns:
            ListEntitiesClimateResponse: The response containing climate entity details.
        """
        return ListEntitiesClimateResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supported_modes=self.supported_modes,
            visual_min_temperature=self.visual_min_temperature,
            visual_max_temperature=self.visual_max_temperature,
            visual_target_temperature_step=self.visual_target_temperature_step,
            supports_current_temperature=self.supports_current_temperature,
            supports_two_point_target_temperature=self.supports_two_point_target_temperature,
            supports_action=self.supports_action,
            supported_fan_modes=[
                ClimateFanMode.CLIMATE_FAN_ON,
                ClimateFanMode.CLIMATE_FAN_OFF,
                ClimateFanMode.CLIMATE_FAN_AUTO,
                ClimateFanMode.CLIMATE_FAN_LOW,
                ClimateFanMode.CLIMATE_FAN_MEDIUM,
                ClimateFanMode.CLIMATE_FAN_HIGH
            ] if self.supports_fan_mode else [],
            supported_swing_modes=[
                ClimateSwingMode.CLIMATE_SWING_OFF,
                ClimateSwingMode.CLIMATE_SWING_BOTH,
                ClimateSwingMode.CLIMATE_SWING_VERTICAL,
                ClimateSwingMode.CLIMATE_SWING_HORIZONTAL
            ] if self.supports_swing_mode else [],
            supported_presets=[
                ClimatePreset.CLIMATE_PRESET_NONE,
                ClimatePreset.CLIMATE_PRESET_HOME,
                ClimatePreset.CLIMATE_PRESET_AWAY,
                ClimatePreset.CLIMATE_PRESET_BOOST,
                ClimatePreset.CLIMATE_PRESET_COMFORT,
                ClimatePreset.CLIMATE_PRESET_ECO,
                ClimatePreset.CLIMATE_PRESET_SLEEP,
                ClimatePreset.CLIMATE_PRESET_ACTIVITY
            ] if self.supports_preset else [],
            supports_current_humidity=self.supports_current_humidity,
            supports_target_humidity=self.supports_target_humidity,
            visual_min_humidity=self.visual_min_humidity,
            visual_max_humidity=self.visual_max_humidity
        )

    async def build_state_response(self) -> ClimateStateResponse:
        """
        Build and return the state response for this climate entity.

        Returns:
            ClimateStateResponse: The response containing the climate's current state.
        """
        return ClimateStateResponse(
            key=self.key,
            mode=self.mode,
            current_temperature=self.current_temperature if self.supports_current_temperature else None,
            target_temperature=self.target_temperature,
            target_temperature_low=self.target_temperature_low,
            target_temperature_high=self.target_temperature_high,
            current_humidity=self.current_humidity if self.supports_current_humidity else None,
            target_humidity=self.target_humidity if self.supports_target_humidity else None,
            fan_mode=self.fan_mode,
            swing_mode=self.swing_mode,
            action=self.action,
            preset=self.preset
        )

    async def random_temperature(self):
        """
        Randomly change the target temperature within the visual limits.
        """
        while True:
            target_temperature = random.uniform(self.visual_min_temperature, self.visual_max_temperature)
            if self.supports_two_point_target_temperature:
                target_temperature_low = random.uniform(self.visual_min_temperature, target_temperature)
                target_temperature_high = random.uniform(target_temperature, self.visual_max_temperature)
                await self.set_state_from_query(target_temperature_low=target_temperature_low, target_temperature_high=target_temperature_high)
            else:
                await self.set_state_from_query(target_temperature=target_temperature)
            logging.debug('Set target temperature to %s', target_temperature)
            await asyncio.sleep(5)

    async def random_mode(self):
        """
        Randomly change the climate mode within the supported modes.
        """
        while True:
            mode = random.choice(self.supported_modes)
            await self.set_state_from_query(mode=mode)
            logging.debug('Set mode to %s', mode)
            await asyncio.sleep(5)

    async def random_values(self):
        """
        Randomly change multiple attributes of the climate entity, including temperature, mode,
        fan mode, swing mode, action, and preset.
        """
        while True:
            target_temperature = random.uniform(self.visual_min_temperature, self.visual_max_temperature)
            mode = random.choice(self.supported_modes)
            current_temperature = random.uniform(self.visual_min_temperature, self.visual_max_temperature)
            fan_mode = random.choice([ClimateFanMode.CLIMATE_FAN_ON, ClimateFanMode.CLIMATE_FAN_AUTO, ClimateFanMode.CLIMATE_FAN_LOW, ClimateFanMode.CLIMATE_FAN_MEDIUM, ClimateFanMode.CLIMATE_FAN_HIGH]) if self.supports_fan_mode else None
            swing_mode = random.choice([ClimateSwingMode.CLIMATE_SWING_OFF, ClimateSwingMode.CLIMATE_SWING_BOTH, ClimateSwingMode.CLIMATE_SWING_VERTICAL, ClimateSwingMode.CLIMATE_SWING_HORIZONTAL]) if self.supports_swing_mode else None
            action = random.choice([ClimateAction.CLIMATE_ACTION_OFF, ClimateAction.CLIMATE_ACTION_COOLING, ClimateAction.CLIMATE_ACTION_HEATING, ClimateAction.CLIMATE_ACTION_IDLE]) if self.supports_action else None
            preset = random.choice([ClimatePreset.CLIMATE_PRESET_NONE, ClimatePreset.CLIMATE_PRESET_HOME, ClimatePreset.CLIMATE_PRESET_AWAY, ClimatePreset.CLIMATE_PRESET_BOOST, ClimatePreset.CLIMATE_PRESET_COMFORT, ClimatePreset.CLIMATE_PRESET_ECO, ClimatePreset.CLIMATE_PRESET_SLEEP, ClimatePreset.CLIMATE_PRESET_ACTIVITY]) if self.supports_preset else None
            if self.supports_two_point_target_temperature:
                target_temperature_low = random.uniform(self.visual_min_temperature, target_temperature)
                target_temperature_high = random.uniform(target_temperature, self.visual_max_temperature)
                await self.set_state_from_query(target_temperature_low=target_temperature_low, target_temperature_high=target_temperature_high, mode=mode, current_temperature=current_temperature, fan_mode=fan_mode, swing_mode=swing_mode, action=action, preset=preset)
            else:
                await self.set_state_from_query(target_temperature=target_temperature, mode=mode, current_temperature=current_temperature, fan_mode=fan_mode, swing_mode=swing_mode, action=action, preset=preset)
            logging.debug('Set random values: target_temperature=%s, mode=%s, fan_mode=%s, swing_mode=%s, action=%s, preset=%s', target_temperature, mode, fan_mode, swing_mode, action, preset)
            await asyncio.sleep(5)

    async def notify_state_change(self):
        """
        Notify the system of a state change to ensure all attributes are updated in OpenHAB.
        """
        state = {
            "mode": self.mode,
            "target_temperature": self.target_temperature,
            "target_temperature_low": self.target_temperature_low,
            "target_temperature_high": self.target_temperature_high,
            "current_temperature": self.current_temperature,
            "fan_mode": self.fan_mode,
            "swing_mode": self.swing_mode,
            "action": self.action,
            "preset": self.preset,
            "current_humidity": self.current_humidity,
            "target_humidity": self.target_humidity
        }
        logging.debug('State change notified with: %s', state)
        # Notify the OpenHAB or relevant system by publishing the updated state
        await self.device.publish(self, 'state_update', state)
        # Additionally, call the update callback to ensure the state is pushed to the system
        if self.device.update_callback:
            await self.device.update_callback(self, state)

    async def set_state_from_command(self, command):
        """
        Set the climate entity state from a command request.

        Args:
            command (ClimateCommandRequest): The command request containing new state values.
        """
        changed = False

        if hasattr(command, 'has_mode') and command.has_mode:
            self.mode = command.mode
            changed = True
        if hasattr(command, 'has_target_temperature') and command.has_target_temperature:
            self.target_temperature = command.target_temperature
            changed = True
        if hasattr(command, 'has_target_temperature_low') and command.has_target_temperature_low:
            self.target_temperature_low = command.target_temperature_low
            changed = True
        if hasattr(command, 'has_target_temperature_high') and command.has_target_temperature_high:
            self.target_temperature_high = command.target_temperature_high
            changed = True
        if hasattr(command, 'has_current_temperature') and command.has_current_temperature:
            self.current_temperature = command.current_temperature
            changed = True
        if hasattr(command, 'has_fan_mode') and command.has_fan_mode:
            self.fan_mode = command.fan_mode
            changed = True
        if hasattr(command, 'has_swing_mode') and command.has_swing_mode:
            self.swing_mode = command.swing_mode
            changed = True
        if hasattr(command, 'has_action') and command.has_action:
            self.action = command.action
            changed = True
        if hasattr(command, 'has_preset') and command.has_preset:
            self.preset = command.preset
            changed = True
        if hasattr(command, 'has_target_humidity') and command.has_target_humidity:
            self.target_humidity = command.target_humidity
            changed = True

        if changed:
            await self.notify_state_change()

async def main():
    """
    Main function to create the climate entity, add it to the device, and start running the device.
    """
    device = Device(name="Full Feature Climate", mac_address="02:00:00:00:98:02")
    climate_entity = FullFeatureClimateEntity(
        device=device,
        name="Full Feature Climate",
        object_id="full_feature_climate",
        supported_modes=[
            ClimateMode.CLIMATE_MODE_OFF,
            ClimateMode.CLIMATE_MODE_HEAT_COOL,
            ClimateMode.CLIMATE_MODE_COOL,
            ClimateMode.CLIMATE_MODE_HEAT,
            ClimateMode.CLIMATE_MODE_FAN_ONLY,
            ClimateMode.CLIMATE_MODE_DRY,
            ClimateMode.CLIMATE_MODE_AUTO
        ],
        visual_min_temperature=16.0,
        visual_max_temperature=30.0,
        visual_target_temperature_step=0.5,
        supports_two_point_target_temperature=True,
        supports_fan_mode=True,
        supports_swing_mode=True,
        supports_action=True,
        supports_preset=True,
        supports_current_humidity=True,
        supports_target_humidity=True
    )
    device.add_entity(climate_entity)

    # Set initial state values after creation
    climate_entity.mode = ClimateMode.CLIMATE_MODE_OFF
    climate_entity.target_temperature = 16.0
    climate_entity.target_temperature_low = 18.0
    climate_entity.target_temperature_high = 24.0
    climate_entity.current_temperature = 16.0
    climate_entity.fan_mode = ClimateFanMode.CLIMATE_FAN_OFF
    climate_entity.swing_mode = ClimateSwingMode.CLIMATE_SWING_OFF
    climate_entity.action = ClimateAction.CLIMATE_ACTION_OFF
    climate_entity.preset = ClimatePreset.CLIMATE_PRESET_NONE
    climate_entity.current_humidity = 50.0
    climate_entity.target_humidity = 45.0

    logging.debug('Starting device...')
    await device.run(api_port=6053, web_port=8080)
    await asyncio.gather(
        climate_entity.random_temperature(),
        climate_entity.random_mode(),
        climate_entity.random_values()
    )

if __name__ == "__main__":
    asyncio.run(main())