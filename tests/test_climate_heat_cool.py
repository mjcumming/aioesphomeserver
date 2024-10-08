import asyncio
import random
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, ClimateEntity
from aioesphomeapi.api_pb2 import (
    ClimateMode, ClimateAction, ListEntitiesClimateResponse, ClimateStateResponse, ClimateCommandRequest
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class BasicHeatCoolClimateEntity(ClimateEntity):
    DOMAIN = "climate"

    def __init__(
        self,
        device,
        name,
        object_id,
        min_temperature,
        max_temperature,
        temperature_step,
    ):
        super().__init__(
            name=name,
            object_id=object_id,
            supported_modes=[
                ClimateMode.CLIMATE_MODE_OFF,
                ClimateMode.CLIMATE_MODE_HEAT_COOL,
                ClimateMode.CLIMATE_MODE_COOL,
                ClimateMode.CLIMATE_MODE_HEAT,
            ],
            visual_min_temperature=min_temperature,
            visual_max_temperature=max_temperature,
            visual_target_temperature_step=temperature_step,
        )
        self.device = device
        self.mode = ClimateMode.CLIMATE_MODE_OFF
        self.current_temperature = (min_temperature + max_temperature) / 2
        self.target_temperature_low = min_temperature
        self.target_temperature_high = max_temperature
        self.action = ClimateAction.CLIMATE_ACTION_OFF

    async def build_list_entities_response(self) -> ListEntitiesClimateResponse:
        return ListEntitiesClimateResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supported_modes=self.supported_modes,
            visual_min_temperature=self.visual_min_temperature,
            visual_max_temperature=self.visual_max_temperature,
            visual_target_temperature_step=self.visual_target_temperature_step,
            supports_current_temperature=True,
            supports_two_point_target_temperature=True,
            supports_action=True,
        )

    async def build_state_response(self) -> ClimateStateResponse:
        return ClimateStateResponse(
            key=self.key,
            mode=self.mode,
            current_temperature=self.current_temperature,
            target_temperature_low=self.target_temperature_low,
            target_temperature_high=self.target_temperature_high,
            action=self.action,
        )

    async def set_state_from_command(self, command: ClimateCommandRequest):
        logging.info(f"Received command for {self.name} (key: {self.key}):")
        changed = False

        if command.has_mode:
            old_mode = self.mode
            self.mode = command.mode
            changed = True
            logging.info(f"  Mode changed: {ClimateMode.Name(old_mode)} -> {ClimateMode.Name(self.mode)}")

        if command.has_target_temperature_low:
            old_temp = self.target_temperature_low
            self.target_temperature_low = command.target_temperature_low
            changed = True
            logging.info(f"  Target temperature low changed: {old_temp:.1f}°C -> {self.target_temperature_low:.1f}°C")

        if command.has_target_temperature_high:
            old_temp = self.target_temperature_high
            self.target_temperature_high = command.target_temperature_high
            changed = True
            logging.info(f"  Target temperature high changed: {old_temp:.1f}°C -> {self.target_temperature_high:.1f}°C")

        if changed:
            self.update_action()
            await self.notify_state_change()
        else:
            logging.info("  No changes made")

    def update_action(self):
        old_action = self.action
        if self.mode == ClimateMode.CLIMATE_MODE_OFF:
            self.action = ClimateAction.CLIMATE_ACTION_OFF
        elif self.mode == ClimateMode.CLIMATE_MODE_HEAT:
            if self.current_temperature < self.target_temperature_low:
                self.action = ClimateAction.CLIMATE_ACTION_HEATING
            else:
                self.action = ClimateAction.CLIMATE_ACTION_IDLE
        elif self.mode == ClimateMode.CLIMATE_MODE_COOL:
            if self.current_temperature > self.target_temperature_high:
                self.action = ClimateAction.CLIMATE_ACTION_COOLING
            else:
                self.action = ClimateAction.CLIMATE_ACTION_IDLE
        elif self.mode == ClimateMode.CLIMATE_MODE_HEAT_COOL:
            if self.current_temperature < self.target_temperature_low:
                self.action = ClimateAction.CLIMATE_ACTION_HEATING
            elif self.current_temperature > self.target_temperature_high:
                self.action = ClimateAction.CLIMATE_ACTION_COOLING
            else:
                self.action = ClimateAction.CLIMATE_ACTION_IDLE
        else:
            logging.warning(f"{self.name}: Unexpected mode {ClimateMode.Name(self.mode)}, setting action to OFF")
            self.action = ClimateAction.CLIMATE_ACTION_OFF
        
        if old_action != self.action:
            logging.info(f"{self.name}: Action changed from {ClimateAction.Name(old_action)} to {ClimateAction.Name(self.action)}")
        else:
            logging.info(f"{self.name}: Action remained {ClimateAction.Name(self.action)}")

    async def random_temperature_change(self):
        while True:
            await asyncio.sleep(5)
            old_temp = self.current_temperature
            
            # Simulate temperature change based on current action
            if self.action == ClimateAction.CLIMATE_ACTION_HEATING:
                self.current_temperature += random.uniform(0.1, 0.5)
            elif self.action == ClimateAction.CLIMATE_ACTION_COOLING:
                self.current_temperature -= random.uniform(0.1, 0.5)
            else:
                self.current_temperature += random.uniform(-0.3, 0.3)
            
            self.current_temperature = max(self.visual_min_temperature, min(self.current_temperature, self.visual_max_temperature))
            logging.info(f"Temperature changed for {self.name}: {old_temp:.1f}°C -> {self.current_temperature:.1f}°C")
            
            self.update_action()
            await self.notify_state_change()

    async def notify_state_change(self):
        logging.info(f"State change for {self.name}:")
        logging.info(f"  Mode: {ClimateMode.Name(self.mode)}")
        logging.info(f"  Current Temperature: {self.current_temperature:.1f}°C")
        logging.info(f"  Target Temperature Low: {self.target_temperature_low:.1f}°C")
        logging.info(f"  Target Temperature High: {self.target_temperature_high:.1f}°C")
        logging.info(f"  Action: {ClimateAction.Name(self.action)}")
        await super().notify_state_change()

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Basic Heat/Cool Climate",
        project_name="aioesphomeserver",
        project_version="1.0.0",
    )

    climate_entity = BasicHeatCoolClimateEntity(
        device=device,
        name="Test_Basic Heat/Cool Climate",
        object_id="test_basic_heat_cool_climate",
        min_temperature=16.0,
        max_temperature=32.0,
        temperature_step=0.5,
    )
    device.add_entity(climate_entity)

    # Run the random temperature change simulation
    asyncio.create_task(climate_entity.random_temperature_change())

    try:
        # Run the device
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    name, api_port, web_port = "Basic Heat/Cool Climate Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())