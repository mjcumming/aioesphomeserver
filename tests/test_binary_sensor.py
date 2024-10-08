import asyncio
import json
import logging
import sys
import os
from aiohttp import web
from aiohttp.test_utils import TestServer, TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device
from aioesphomeserver.binary_sensor import BinarySensorEntity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBinarySensor:
    def __init__(self, device_name, api_port, web_port):
        self.device = Device(
            name=device_name,
            mac_address=f"AC:BC:32:89:0E:{api_port:02x}",
            model="Test Binary Sensor Device",
            project_name="aioesphomeserver",
            project_version="1.0.0"
        )
        self.api_port = api_port
        self.web_port = web_port

        self.binary_sensor = BinarySensorEntity(name="Test Binary Sensor", device_class="motion")
        self.device.add_entity(self.binary_sensor)

    async def run_tests(self):
        logger.info("Starting Binary Sensor tests...")

        # Test initial state
        state = await self.binary_sensor.get_state()
        assert state is False, f"Initial state should be False, got {state}"
        logger.info("Initial state test passed")

        # Test set_state
        await self.binary_sensor.set_state(True)
        state = await self.binary_sensor.get_state()
        assert state is True, f"State should be True after set_state(True), got {state}"
        logger.info("set_state test passed")

        # Test build_list_entities_response
        response = await self.binary_sensor.build_list_entities_response()
        assert response.name == "Test Binary Sensor", f"Expected name 'Test Binary Sensor', got {response.name}"
        assert response.device_class == "motion", f"Expected device_class 'motion', got {response.device_class}"
        logger.info("build_list_entities_response test passed")

        # Test build_state_response
        state_response = await self.binary_sensor.build_state_response()
        assert state_response.state is True, f"Expected state True, got {state_response.state}"
        logger.info("build_state_response test passed")

        # Test state_json
        json_state = await self.binary_sensor.state_json()
        state_dict = json.loads(json_state)
        assert state_dict['state'] == "ON", f"Expected state 'ON', got {state_dict['state']}"
        assert state_dict['value'] is True, f"Expected value True, got {state_dict['value']}"
        logger.info("state_json test passed")

        # Test can_handle method
        can_handle = await self.binary_sensor.can_handle(1, {"test": "message"})
        assert can_handle is False, f"can_handle should return False, got {can_handle}"
        logger.info("can_handle test passed")

        # Test handle method
        test_message = {"test": "message"}
        await self.binary_sensor.handle(1, test_message)
        logger.info("handle test passed")

        # Test route_get_state
        app = web.Application()
        await self.binary_sensor.add_routes(app.router)
        
        async with TestClient(TestServer(app)) as client:
            resp = await client.get(f"/binary_sensor/{self.binary_sensor.object_id}")
            assert resp.status == 200, f"Expected status 200, got {resp.status}"
            
            resp_json = await resp.json()
            assert resp_json['state'] == "ON", f"Expected state 'ON', got {resp_json['state']}"
        logger.info("route_get_state test passed")

        logger.info("All Binary Sensor tests passed!")

    async def simulate_motion(self):
        while True:
            await asyncio.sleep(5)  # Simulate motion every 5 seconds
            new_state = not await self.binary_sensor.get_state()
            await self.binary_sensor.set_state(new_state)
            logger.info(f"Binary Sensor state changed to: {'ON' if new_state else 'OFF'}")

    async def run(self):
        await self.run_tests()
        simulation_task = asyncio.create_task(self.simulate_motion())
        device_task = asyncio.create_task(self.device.run(self.api_port, self.web_port))

        try:
            await asyncio.gather(device_task, simulation_task)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled. Shutting down...")
        finally:
            await self.device.unregister_zeroconf()

async def main():
    test = TestBinarySensor("Test Binary Sensor Device", 6053, 8081)
    await test.run()

if __name__ == "__main__":
    logger.info("Starting Binary Sensor test")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)