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


class BasicHeatingClimateEntity(ClimateEntity):
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
            supported_modes=[ClimateMode.CLIMATE_MODE_OFF, ClimateMode.CLIMATE_MODE_HEAT],
            visual_min_temperature=min_temperature,
            visual_max_temperature=max_temperature,
            visual_target_temperature_step=temperature_step,
        )
        self.device = device
        self.mode = ClimateMode.CLIMATE_MODE_OFF
        self.current_temperature = min_temperature
        self.target_temperature = min_temperature
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
            supports_two_point_target_temperature=False,
            supports_action=True,
        )

    async def build_state_response(self) -> ClimateStateResponse:
        return ClimateStateResponse(
            key=self.key,
            mode=self.mode,
            current_temperature=self.current_temperature,
            target_temperature=self.target_temperature,
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

        if command.has_target_temperature:
            old_temp = self.target_temperature
            self.target_temperature = command.target_temperature
            changed = True
            logging.info(f"  Target temperature changed: {old_temp:.1f}°C -> {self.target_temperature:.1f}°C")

        if changed:
            self.update_action()
            await self.notify_state_change()
        else:
            logging.info("  No changes made")

    def update_action(self):
        old_action = self.action
        if self.mode == ClimateMode.CLIMATE_MODE_OFF:
            self.action = ClimateAction.CLIMATE_ACTION_OFF
            logging.info(f"{self.name}: Mode is OFF, setting action to OFF")
        elif self.mode == ClimateMode.CLIMATE_MODE_HEAT:
            if self.current_temperature < self.target_temperature:
                self.action = ClimateAction.CLIMATE_ACTION_HEATING
                logging.info(f"{self.name}: Mode is HEAT, Current temp ({self.current_temperature:.1f}°C) < Target temp ({self.target_temperature:.1f}°C), setting action to HEATING")
            else:
                self.action = ClimateAction.CLIMATE_ACTION_IDLE
                logging.info(f"{self.name}: Mode is HEAT, Current temp ({self.current_temperature:.1f}°C) >= Target temp ({self.target_temperature:.1f}°C), setting action to IDLE")
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
            
            # Simulate temperature change based on heating action
            if self.action == ClimateAction.CLIMATE_ACTION_HEATING:
                self.current_temperature += random.uniform(0.1, 0.5)
            else:
                self.current_temperature += random.uniform(-0.3, 0.1)
            
            self.current_temperature = max(self.visual_min_temperature, min(self.current_temperature, self.visual_max_temperature))
            logging.info(f"Temperature changed for {self.name}: {old_temp:.1f}°C -> {self.current_temperature:.1f}°C")
            
            # Update action based on new temperature, but only if in HEAT mode
            if self.mode == ClimateMode.CLIMATE_MODE_HEAT:
                self.update_action()
            
            await self.notify_state_change()

    async def notify_state_change(self):
        logging.info(f"State change for {self.name}:")
        logging.info(f"  Mode: {ClimateMode.Name(self.mode)}")
        logging.info(f"  Current Temperature: {self.current_temperature:.1f}°C")
        logging.info(f"  Target Temperature: {self.target_temperature:.1f}°C")
        logging.info(f"  Action: {ClimateAction.Name(self.action)}")
        await super().notify_state_change()

        
async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Basic Heating Climate",
        project_name="aioesphomeserver",
        project_version="1.0.0",
    )

    climate_entity = BasicHeatingClimateEntity(
        device=device,
        name="Test Basic Heating Climate",
        object_id="test_basic_heating_climate",
        min_temperature=10.0,
        max_temperature=30.0,
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
    name, api_port, web_port = "Test Basic Heating Climate Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())