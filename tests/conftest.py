"""Shared test fixtures for DroneMobile integration tests."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest


def make_vehicle_data(engine_on=False, ignition_on=False):
    """Create a mock vehicle data dict matching the coordinator's expected shape."""
    return {
        "id": "vehicle_123",
        "vehicle_name": "Test Car",
        "device_key": "dev_key_abc",
        "remote_start_status": False,
        "panic_status": False,
        "last_known_state": {
            "controller": {
                "engine_on": engine_on,
                "ignition_on": ignition_on,
            },
            "controller_model": "DM-500",
        },
    }


@pytest.fixture
def mock_vehicle():
    """Mock the drone_mobile Vehicle object with start/stop methods."""
    vehicle = MagicMock()
    vehicle.start = MagicMock(return_value={
        "command_success": True,
        "command_sent": "remote_start",
        "controller": {"engine_on": True, "ignition_on": True},
    })
    vehicle.stop = MagicMock(return_value={
        "command_success": True,
        "command_sent": "remote_stop",
        "controller": {"engine_on": False, "ignition_on": False},
    })
    return vehicle


@pytest.fixture
def mock_coordinator(mock_vehicle):
    """Create a mock coordinator that mimics DroneMobileDataUpdateCoordinator."""
    coordinator = MagicMock()
    coordinator.data = make_vehicle_data(engine_on=False, ignition_on=False)
    coordinator.vehicle = mock_vehicle
    coordinator.hass = MagicMock()
    # Make async_add_executor_job run the function directly
    coordinator.hass.async_add_executor_job = AsyncMock(
        side_effect=lambda func, *args: func(*args)
    )
    coordinator.update_data_from_response = MagicMock()
    return coordinator
