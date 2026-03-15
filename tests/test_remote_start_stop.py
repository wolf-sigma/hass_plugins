"""Tests for DroneMobile remote start and stop via the Switch entity."""

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Add the custom_components path so we can import the integration
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "drone_mobile_home_assistant"),
)

from conftest import make_vehicle_data


# ---------------------------------------------------------------------------
# Helpers — we test the Switch class in isolation by mocking HA dependencies
# ---------------------------------------------------------------------------

def _make_switch(coordinator, switch_type="remoteStart"):
    """Instantiate a Switch without going through HA setup."""
    # Patch the parent class __init__ to avoid HA internals
    with patch(
        "custom_components.drone_mobile.switch.DroneMobileEntity.__init__",
        return_value=None,
    ):
        from custom_components.drone_mobile.switch import Switch

        sw = Switch(coordinator, switch_type, {})
        # Manually wire up what the parent __init__ would have done
        sw.coordinator = coordinator
        sw.coordinator_context = object()
        sw.async_write_ha_state = MagicMock()
        return sw


# ---------------------------------------------------------------------------
# Remote Start tests
# ---------------------------------------------------------------------------

class TestRemoteStart:
    """Tests for turning on the remoteStart switch (starting the car)."""

    @pytest.mark.asyncio
    async def test_start_calls_vehicle_start(self, mock_coordinator):
        """Starting the car should call vehicle.start with the device key."""
        # Engine is off → is_on returns False
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_on()

        mock_coordinator.vehicle.start.assert_called_once_with("dev_key_abc")

    @pytest.mark.asyncio
    async def test_start_updates_coordinator_data(self, mock_coordinator):
        """After starting, the coordinator should process the response."""
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_on()

        mock_coordinator.update_data_from_response.assert_called_once()
        # Verify the response from vehicle.start was passed through
        args = mock_coordinator.update_data_from_response.call_args[0]
        response = args[1]
        assert response["command_success"] is True
        assert response["controller"]["engine_on"] is True

    @pytest.mark.asyncio
    async def test_start_writes_ha_state(self, mock_coordinator):
        """Starting should trigger a HA state update."""
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_on()

        sw.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_skipped_when_already_on(self, mock_coordinator):
        """If the engine is already running, start should be a no-op."""
        mock_coordinator.data = make_vehicle_data(engine_on=True)
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_on()

        mock_coordinator.vehicle.start.assert_not_called()


# ---------------------------------------------------------------------------
# Remote Stop tests
# ---------------------------------------------------------------------------

class TestRemoteStop:
    """Tests for turning off the remoteStart switch (stopping the car)."""

    @pytest.mark.asyncio
    async def test_stop_calls_vehicle_stop(self, mock_coordinator):
        """Stopping the car should call vehicle.stop with the device key."""
        # Engine is on → is_on returns True
        mock_coordinator.data = make_vehicle_data(engine_on=True)
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_off()

        mock_coordinator.vehicle.stop.assert_called_once_with("dev_key_abc")

    @pytest.mark.asyncio
    async def test_stop_updates_coordinator_data(self, mock_coordinator):
        """After stopping, the coordinator should process the response."""
        mock_coordinator.data = make_vehicle_data(engine_on=True)
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_off()

        mock_coordinator.update_data_from_response.assert_called_once()
        args = mock_coordinator.update_data_from_response.call_args[0]
        response = args[1]
        assert response["command_success"] is True
        assert response["controller"]["engine_on"] is False

    @pytest.mark.asyncio
    async def test_stop_writes_ha_state(self, mock_coordinator):
        """Stopping should trigger a HA state update."""
        mock_coordinator.data = make_vehicle_data(engine_on=True)
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_off()

        sw.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_skipped_when_already_off(self, mock_coordinator):
        """If the engine is already off, stop should be a no-op."""
        mock_coordinator.data = make_vehicle_data(engine_on=False)
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_turn_off()

        mock_coordinator.vehicle.stop.assert_not_called()


# ---------------------------------------------------------------------------
# Toggle tests
# ---------------------------------------------------------------------------

class TestRemoteToggle:
    """Tests for toggling the remoteStart switch."""

    @pytest.mark.asyncio
    async def test_toggle_starts_when_off(self, mock_coordinator):
        """Toggle should start the car when it's off."""
        mock_coordinator.data = make_vehicle_data(engine_on=False)
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_toggle()

        mock_coordinator.vehicle.start.assert_called_once_with("dev_key_abc")
        mock_coordinator.vehicle.stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_toggle_stops_when_on(self, mock_coordinator):
        """Toggle should stop the car when it's running."""
        mock_coordinator.data = make_vehicle_data(engine_on=True)
        sw = _make_switch(mock_coordinator, "remoteStart")

        await sw.async_toggle()

        mock_coordinator.vehicle.stop.assert_called_once_with("dev_key_abc")
        mock_coordinator.vehicle.start.assert_not_called()


# ---------------------------------------------------------------------------
# is_on property tests
# ---------------------------------------------------------------------------

class TestIsOnProperty:
    """Tests for the is_on state detection."""

    def test_is_on_true_when_engine_on(self, mock_coordinator):
        mock_coordinator.data = make_vehicle_data(engine_on=True)
        sw = _make_switch(mock_coordinator, "remoteStart")
        assert sw.is_on is True

    def test_is_on_true_when_ignition_on(self, mock_coordinator):
        mock_coordinator.data = make_vehicle_data(engine_on=False, ignition_on=True)
        sw = _make_switch(mock_coordinator, "remoteStart")
        assert sw.is_on is True

    def test_is_on_false_when_both_off(self, mock_coordinator):
        mock_coordinator.data = make_vehicle_data(engine_on=False, ignition_on=False)
        sw = _make_switch(mock_coordinator, "remoteStart")
        assert sw.is_on is False

    def test_is_on_none_when_data_missing(self, mock_coordinator):
        mock_coordinator.data = None
        sw = _make_switch(mock_coordinator, "remoteStart")
        assert sw.is_on is None
