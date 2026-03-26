from pymavlink import mavutil
import time
import os

# --- CONFIGURATION ---
TARGET_ALTITUDE = 100
GROUND_ALTITUDE = 50 # ASML height at start location

# 1. CONNECTION
master = mavutil.mavlink_connection('udpin:0.0.0.0:14550')

# Drone State Dictionary
state = {
    "alt": 0.0, "speed": 0.0, "heading": 0,
    "lat": 0.0, "lon": 0.0, "battery": 0,
    "mode": "UNKNOWN", "armed": False,
    "ekf_ok": False, "status_text": "Initializing..."
}

def update_telemetry():
    """ Updates drone state from MAVLink messages (Non-blocking) """
    msg = master.recv_match(blocking=False)
    if not msg: return

    msg_type = msg.get_type()
    # https://mavlink.io/en/messages/common.html#VFR_HUD
    if msg_type == 'VFR_HUD':
        state['alt'] = msg.alt - GROUND_ALTITUDE
        state['speed'] = msg.groundspeed
        state['heading'] = msg.heading
    # https://mavlink.io/en/messages/common.html#GLOBAL_POSITION_INT
    elif msg_type == 'GLOBAL_POSITION_INT':
        state['lat'] = msg.lat / 1e7
        state['lon'] = msg.lon / 1e7
    #https://mavlink.io/en/messages/common.html#SYS_STATUSs
    elif msg_type == 'SYS_STATUS':
        state['battery'] = msg.battery_remaining
    # https://mavlink.io/en/messages/ardupilotmega.html#EKF_STATUS_REPORT
    elif msg_type == 'EKF_STATUS_REPORT':
        # Check if EKF flags are healthy (velocity, pos_horiz, pos_vert)
        # https://mavlink.io/en/messages/ardupilotmega.html#EKF_STATUS_FLAGS
        state['ekf_ok'] = bool(msg.flags & 0x01 and msg.flags & 0x02 and msg.flags & 0x04)
    # https://mavlink.io/en/messages/common.html#HEARTBEATs
    elif msg_type == 'HEARTBEAT':
        modes = {v: k for k, v in master.mode_mapping().items()}
        state['mode'] = modes.get(msg.custom_mode, "UNKNOWN")
        # https://mavlink.io/en/messages/common.html#MAV_MODE_FLAG
        state['armed'] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    elif msg_type == 'STATUSTEXT':
        state['status_text'] = msg.text

def draw_dashboard():
    """ Renders the Mission Control Dashboard in Terminal """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("========================================")
    print("       DRONE MISSION CONTROL DASHBOARD   ")
    print("========================================")
    print(f" MODE:    {state['mode']:10} | ARMED: {str(state['armed']):5}")
    print(f" EKF OK:  {str(state['ekf_ok']):10} | BATT:  {state['battery']}%")
    print(f" STATUS:  {state['status_text']}")
    print("----------------------------------------")
    print(f" LAT:     {state['lat']:.6f} | LON:   {state['lon']:.6f}")
    print(f" ALT:     {state['alt']:6.2f} m | SPEED: {state['speed']:.2f} m/s")
    print(f" HEADING: {state['heading']:3}°")
    print("========================================\n")

# --- MISSION LOGIC ---

print("Waiting for initial heartbeat...")
master.wait_heartbeat()

mission_step = "WAIT_EKF"

while True:
    update_telemetry()
    draw_dashboard()

    # Machine State Logic
    if mission_step == "WAIT_EKF":
        if state['ekf_ok'] and state['lat'] != 0:
            state['status_text'] = "EKF Ready. Changing to GUIDED..."
            mission_step = "SET_MODE"
        else:
            state['status_text'] = "Waiting for EKF/GPS alignment..."

    elif mission_step == "SET_MODE":
        if state['mode'] != "GUIDED":
            mode_id = master.mode_mapping()['GUIDED']
            master.mav.set_mode_send(master.target_system, 1, mode_id)
        else:
            mission_step = "ARMING"

    elif mission_step == "ARMING":
        if not state['armed']:
            state['status_text'] = "Sending ARM command..."
            master.mav.command_long_send(master.target_system, master.target_component,
                                         mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
        else:
            mission_step = "TAKEOFF"

    elif mission_step == "TAKEOFF":
        state['status_text'] = f"Taking off to {TARGET_ALTITUDE}m..."
        master.mav.command_long_send(master.target_system, master.target_component,
                                     mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, TARGET_ALTITUDE)
        mission_step = "MONITOR_FLIGHT"

    elif mission_step == "MONITOR_FLIGHT":
        if state['alt'] >= (TARGET_ALTITUDE - 0.5):
            state['status_text'] = "Target altitude reached. Mission Success."

    time.sleep(0.1) # Loop rate (10Hz)