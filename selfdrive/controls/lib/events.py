from enum import IntEnum
from typing import Dict, Union, Callable, Any

from cereal import log, car
import cereal.messaging as messaging
from common.realtime import DT_CTRL
from selfdrive.config import Conversions as CV
from selfdrive.locationd.calibrationd import MIN_SPEED_FILTER

AlertSize = log.ControlsState.AlertSize
AlertStatus = log.ControlsState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
EventName = car.CarEvent.EventName


# Alert priorities
class Priority(IntEnum):
  LOWEST = 0
  LOWER = 1
  LOW = 2
  MID = 3
  HIGH = 4
  HIGHEST = 5


# Event types
class ET:
  ENABLE = 'enable'
  PRE_ENABLE = 'preEnable'
  NO_ENTRY = 'noEntry'
  WARNING = 'warning'
  USER_DISABLE = 'userDisable'
  SOFT_DISABLE = 'softDisable'
  IMMEDIATE_DISABLE = 'immediateDisable'
  PERMANENT = 'permanent'


# get event name from enum
EVENT_NAME = {v: k for k, v in EventName.schema.enumerants.items()}


class Events:
  def __init__(self):
    self.events = []
    self.static_events = []
    self.events_prev = dict.fromkeys(EVENTS.keys(), 0)

  @property
  def names(self):
    return self.events

  def __len__(self):
    return len(self.events)

  def add(self, event_name, static=False):
    if static:
      self.static_events.append(event_name)
    self.events.append(event_name)

  def clear(self):
    self.events_prev = {k: (v + 1 if k in self.events else 0) for k, v in self.events_prev.items()}
    self.events = self.static_events.copy()

  def any(self, event_type):
    for e in self.events:
      if event_type in EVENTS.get(e, {}).keys():
        return True
    return False

  def create_alerts(self, event_types, callback_args=None):
    if callback_args is None:
      callback_args = []

    ret = []
    for e in self.events:
      types = EVENTS[e].keys()
      for et in event_types:
        if et in types:
          alert = EVENTS[e][et]
          if not isinstance(alert, Alert):
            alert = alert(*callback_args)

          if DT_CTRL * (self.events_prev[e] + 1) >= alert.creation_delay:
            alert.alert_type = f"{EVENT_NAME[e]}/{et}"
            alert.event_type = et
            ret.append(alert)
    return ret

  def add_from_msg(self, events):
    for e in events:
      self.events.append(e.name.raw)

  def to_msg(self):
    ret = []
    for event_name in self.events:
      event = car.CarEvent.new_message()
      event.name = event_name
      for event_type in EVENTS.get(event_name, {}).keys():
        setattr(event, event_type, True)
      ret.append(event)
    return ret

# 메세지 한글화 : 로웰 ( https://github.com/crwusiz/openpilot )

class Alert:
  def __init__(self,
               alert_text_1: str,
               alert_text_2: str,
               alert_status: log.ControlsState.AlertStatus,
               alert_size: log.ControlsState.AlertSize,
               alert_priority: Priority,
               visual_alert: car.CarControl.HUDControl.VisualAlert,
               audible_alert: car.CarControl.HUDControl.AudibleAlert,
               duration_sound: float,
               duration_hud_alert: float,
               duration_text: float,
               alert_rate: float = 0.,
               creation_delay: float = 0.):

    self.alert_text_1 = alert_text_1
    self.alert_text_2 = alert_text_2
    self.alert_status = alert_status
    self.alert_size = alert_size
    self.alert_priority = alert_priority
    self.visual_alert = visual_alert
    self.audible_alert = audible_alert

    self.duration_sound = duration_sound
    self.duration_hud_alert = duration_hud_alert
    self.duration_text = duration_text

    self.alert_rate = alert_rate
    self.creation_delay = creation_delay

    self.start_time = 0.
    self.alert_type = ""
    self.event_type = None

  def __str__(self) -> str:
    return f"{self.alert_text_1}/{self.alert_text_2} {self.alert_priority} {self.visual_alert} {self.audible_alert}"

  def __gt__(self, alert2) -> bool:
    return self.alert_priority > alert2.alert_priority


class NoEntryAlert(Alert):
  def __init__(self, alert_text_2, audible_alert=AudibleAlert.chimeError, duration_sound=.4,
               visual_alert=VisualAlert.none, duration_hud_alert=2.):
    super().__init__("Unable to use open pilot", alert_text_2, AlertStatus.normal,
                     AlertSize.mid, Priority.LOW, visual_alert,
                     audible_alert, duration_sound, duration_hud_alert, 3.)


class SoftDisableAlert(Alert):
  def __init__(self, alert_text_2):
    super().__init__("Take control immediately", alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.MID, VisualAlert.steerRequired,
                     AudibleAlert.chimeWarningRepeat, .1, 2., 2.),


class ImmediateDisableAlert(Alert):
  def __init__(self, alert_text_2, alert_text_1="Take control immediately"):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.HIGHEST, VisualAlert.steerRequired,
                     AudibleAlert.chimeWarningRepeat, 2.2, 3., 4.),


class EngagementAlert(Alert):
  def __init__(self, audible_alert=True):
    super().__init__("", "",
                     AlertStatus.normal, AlertSize.none,
                     Priority.MID, VisualAlert.none,
                     audible_alert, .2, 0., 0.),


class NormalPermanentAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str, duration_text: float = 0.2):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.normal, AlertSize.mid if len(alert_text_2) else AlertSize.small,
                     Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., duration_text),


# ********** alert callback functions **********
def below_steer_speed_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  speed = int(round(CP.minSteerSpeed * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)))
  unit = "㎞/h" if metric else "mph"
  return Alert(
    "TAKE CONTROL",
    "Steer Unavailable Below %d %s" % (speed+5, unit),
    AlertStatus.userPrompt, AlertSize.mid,
    Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimeDing, .1, .1, .1)


def calibration_incomplete_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  speed = int(MIN_SPEED_FILTER * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH))
  unit = "㎞/h" if metric else "mph"
  return Alert(
    "Calibration in progress : %d%%" % sm['liveCalibration'].calPerc,
    "Drive above %d %s " % (speed, unit),
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2)


def no_gps_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  gps_integrated = sm['pandaState'].pandaType in [log.PandaState.PandaType.uno, log.PandaState.PandaType.dos]
  return Alert(
    "GPS poor reception",
    "GPS Check the connection and antenna" if gps_integrated else "GPS check the antenna",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=300.)


def wrong_car_mode_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  text = "Cruise inactive"
  if CP.carName == "honda":
    text = "main switch OFF"
  return NoEntryAlert(text, duration_hud_alert=0.)


def startup_fuzzy_fingerprint_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  return Alert(
    "WARNING: Exactly matching vehicle model not found",
    f"closest match: {CP.carFingerprint.title()[:40]}",
    AlertStatus.userPrompt, AlertSize.mid,
    Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 15.)


def joystick_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  axes = sm['testJoystick'].axes
  gb, steer = list(axes)[:2] if len(axes) else (0., 0.)
  return Alert(
    "joystick mode",
    f"Gas: {round(gb * 100.)}%, Steer: {round(steer * 100.)}%",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .1)

def auto_lane_change_alert(CP, sm, metric):
  alc_timer = sm['lateralPlan'].autoLaneChangeTimer
  return Alert(
    "Lane change starts in %d seconds" % alc_timer,
    "Check for vehicle in the other lane",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOW, VisualAlert.none, AudibleAlert.chimeDingRepeat, .1, .1, .1, alert_rate=0.75)

EVENTS: Dict[int, Dict[str, Union[Alert, Callable[[Any, messaging.SubMaster, bool], Alert]]]] = {
  # ********** events with no alerts **********

  # ********** events only containing alerts displayed in all states **********

  EventName.joystickDebug: {
    ET.WARNING: joystick_alert,
    ET.PERMANENT: Alert(
      "joystick mode",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 0.1),
  },

  EventName.controlsInitializing: {
    ET.NO_ENTRY: NoEntryAlert("Process is initializing"),
  },

  EventName.startup: {
    ET.PERMANENT: Alert(
      "Enjoy openpilot, have a safe ride!",
      "Always keep hands on wheel and eyes on road",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.chimeEngage2, 1., 0., 10.),
  },

  EventName.startupMaster: {
    ET.PERMANENT: Alert(
      "Enjoy openpilot, have a safe ride!",
      "Always keep hands on wheel and eyes on road",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.chimeEngage2, 1., 0., 10.),
  },

  # Car is recognized, but marked as dashcam only
  EventName.startupNoControl: {
    ET.PERMANENT: Alert(
      "Dash cam mode",
      "Always keep hands on wheel and eyes on road",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.chimeDisengage2, 1., 0., 15.),
  },

  # Car is not recognized
  EventName.startupNoCar: {
    ET.PERMANENT: Alert(
      "Dash cam mode : incompatible vehicle",
      "Always keep hands on wheel and eyes on road",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.chimeDisengage2, 1., 0., 15.),
  },

  # openpilot uses the version strings from various ECUs to detect the correct car model.
  # Usually all ECUs are recognized and an exact match to a car model can be made. Sometimes
  # one or two ECUs have unrecognized versions, but the others are present in the database.
  # If openpilot is confident about the match to a car model, it fingerprints anyway.
  # In this case an alert is thrown since there is a small chance the wrong car was detected
  # and the user should pay extra attention.
  # This alert can be prevented by adding all ECU firmware version to openpilot:
  # https://github.com/commaai/openpilot/wiki/Fingerprinting
  EventName.startupFuzzyFingerprint: {
    ET.PERMANENT: startup_fuzzy_fingerprint_alert,
  },

  EventName.startupNoFw: {
    ET.PERMANENT: Alert(
      "Vehicle not recognized",
      "Check the connection status",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 15.),
  },

  EventName.dashcamMode: {
    ET.PERMANENT: Alert(
      "Dash cam mode",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.invalidLkasSetting: {
    ET.PERMANENT: Alert(
      "Vehicle LKAS button status check",
      "Activated after vehicle LKAS button OFF",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  # Some features or cars are marked as community features. If openpilot
  # detects the use of a community feature it switches to dashcam mode
  # until these features are allowed using a toggle in settings.
  EventName.communityFeatureDisallowed: {
    # LOW priority to overcome Cruise Error
    ET.PERMANENT: Alert(
      "Community feature detected",
      "Please enable community features in developer settings",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  # openpilot doesn't recognize the car. This switches openpilot into a
  # read-only mode. This can be solved by adding your fingerprint.
  # See https://github.com/commaai/openpilot/wiki/Fingerprinting for more information
  EventName.carUnrecognized: {
    ET.PERMANENT: Alert(
      "Dash cam mode",
      "Vehicle not recognized",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.stockAeb: {
    ET.PERMANENT: Alert(
      "Brake!",
      "Collision risk",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 1., 2., 2.),
    ET.NO_ENTRY: NoEntryAlert("AEB: Collision risk"),
  },

  EventName.stockFcw: {
    ET.PERMANENT: Alert(
      "Brake!",
      "Collision risk",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 1., 2., 2.),
    ET.NO_ENTRY: NoEntryAlert("FCW: Collision risk"),
  },

  EventName.fcw: {
    ET.PERMANENT: Alert(
      "Brake!",
      "Collision risk",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.chimeWarningRepeat, 1., 2., 2.),
  },

  EventName.ldw: {
    ET.PERMANENT: Alert(
      "Take control",
      "Lane departure detected",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.ldw, AudibleAlert.chimePrompt, .1, 2., 3.),
  },

  # ********** events only containing alerts that display while engaged **********

  EventName.gasPressed: {
    ET.PRE_ENABLE: Alert(
      "openpilot will not brake while gas pressed",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .0, .0, .1, creation_delay=1.),
  },

  # openpilot tries to learn certain parameters about your car by observing
  # how the car behaves to steering inputs from both human and openpilot driving.
  # This includes:
  # - steer ratio: gear ratio of the steering rack. Steering angle divided by tire angle
  # - tire stiffness: how much grip your tires have
  # - angle offset: most steering angle sensors are offset and measure a non zero angle when driving straight
  # This alert is thrown when any of these values exceed a sanity check. This can be caused by
  # bad alignment or bad sensor data. If this happens consistently consider creating an issue on GitHub
  EventName.vehicleModelInvalid: {
    ET.NO_ENTRY: NoEntryAlert("Vehicle parameter identification error"),
    ET.SOFT_DISABLE: SoftDisableAlert("Vehicle parameter identification error"),
    ET.WARNING: Alert(
      "Vehicle parameter identification error",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.steerRequired, AudibleAlert.none, .0, .0, .1),
  },

  EventName.steerTempUnavailableSilent: {
    ET.WARNING: Alert(
      "Steering control temporarily unavailable",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimePrompt, 1., 1., 1.),
  },

  EventName.preDriverDistracted: {
    ET.WARNING: Alert(
      "KEEP EYES ON ROAD: Driver Distracted",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.chimeDing, .1, .1, .1),
  },

  EventName.promptDriverDistracted: {
    ET.WARNING: Alert(
      "KEEP EYES ON ROAD",
      "Driver Distracted",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimeDistracted, 3., .1, .1),
  },

  EventName.driverDistracted: {
    ET.WARNING: Alert(
      "DISENGAGE IMMEDIATELY",
      "Driver Distracted",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarningRepeat, .1, .1, .1),
  },

  EventName.preDriverUnresponsive: {
    ET.WARNING: Alert(
      "TOUCH STEERING WHEEL: No Face Detected",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeDing, .1, .1, .1, alert_rate=0.75),
  },

  EventName.promptDriverUnresponsive: {
    ET.WARNING: Alert(
      "TOUCH STEERING WHEEL",
      "Driver Unresponsive",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimeWarning2Repeat, .1, .1, .1),
  },

  EventName.driverUnresponsive: {
    ET.WARNING: Alert(
      "DISENGAGE IMMEDIATELY",
      "Driver Unresponsive",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarningRepeat, .1, .1, .1),
  },

  EventName.manualRestart: {
    ET.WARNING: Alert(
      "Take control",
      "Reactivate manually",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.resumeRequired: {
    ET.WARNING: Alert(
      "STOPPED",
      "Press Resume to Move",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.belowSteerSpeed: {
    ET.WARNING: below_steer_speed_alert,
  },

  EventName.preLaneChangeLeft: {
    ET.WARNING: Alert(
      "Steer Left to Start Lane Change",
      "Monitor Other Vehicles",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.preLaneChangeRight: {
    ET.WARNING: Alert(
      "Steer Right to Start Lane Change",
      "Monitor Other Vehicles",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.laneChangeBlocked: {
    ET.WARNING: Alert(
      "Car Detected in Blindspot",
      "Monitor Other Vehicles",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.chimeDingRepeat, .1, .1, .1),
  },

  EventName.laneChange: {
    ET.WARNING: Alert(
      "Changing Lane",
      "Monitor Other Vehicles",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1),
  },

  EventName.steerSaturated: {
    ET.WARNING: Alert(
      "TAKE CONTROL",
      "Turn Exceeds Steering Limit",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimePrompt, 1., 1., 1.),
  },

  # Thrown when the fan is driven at >50% but is not rotating
  EventName.fanMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("FAN malfunction", "Check the device"),
  },

  # Camera is not outputting frames at a constant framerate
  EventName.cameraMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("Camera malfunction", "Check the device"),
  },

  # Unused
  EventName.gpsMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("GPS Malfunction", "Check the device"),
  },

  # When the GPS position and localizer diverge the localizer is reset to the
  # current GPS position. This alert is thrown when the localizer is reset
  # more often than expected.
  EventName.localizerMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("Localizer Malfunction", "Check the device"),
  },

  EventName.turningIndicatorOn: {
    ET.WARNING: Alert(
      "Take control while",
      "turn indicator is on",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.none, .0, .1, .2),
  },

  EventName.lkasButtonOff: {
    ET.WARNING: Alert(
      "TAKE CONTROL",
      "Steer Disabled by LKAS button",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.none, 0., .1, .2),
  },

  EventName.autoLaneChange: {
    ET.WARNING: auto_lane_change_alert,
  },

  # ********** events that affect controls state transitions **********

  EventName.pcmEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.chimeEngage),
  },

  EventName.buttonEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.chimeEngage),
  },

  EventName.pcmDisable: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
  },

  EventName.buttonCancel: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
  },

  EventName.brakeHold: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("brake detected"),
  },

  EventName.parkBrake: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("Parking brake"),
  },

  EventName.pedalPressed: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("brake detected",
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.wrongCarMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: wrong_car_mode_alert,
  },

  EventName.wrongCruiseMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("Activate Adaptive Cruise"),
  },

  EventName.steerTempUnavailable: {
    ET.WARNING: Alert(
      "Take control",
      "Steering temporarily unavailable",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert("Steering temporarily unavailable",
                              duration_hud_alert=0.),
  },

  EventName.outOfSpace: {
    ET.PERMANENT: Alert(
      "Insufficient storage space",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert("Insufficient storage space",
                              duration_hud_alert=0.),
  },

  EventName.belowEngageSpeed: {
    ET.NO_ENTRY: NoEntryAlert("Below engage speed"),
  },

  EventName.sensorDataInvalid: {
    ET.PERMANENT: Alert(
      "Device sensor error",
      "Check your device",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("Device sensor error"),
  },

  EventName.noGps: {
    ET.PERMANENT: no_gps_alert,
  },

  EventName.soundsUnavailable: {
    ET.PERMANENT: NormalPermanentAlert("speaker not detected", "Check your device"),
    ET.NO_ENTRY: NoEntryAlert("speaker not detected"),
  },

  EventName.tooDistracted: {
    ET.NO_ENTRY: NoEntryAlert("Interference level too high"),
  },

  EventName.overheat: {
    ET.PERMANENT: Alert(
      "Device overheated",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.SOFT_DISABLE: SoftDisableAlert("Device overheated"),
    ET.NO_ENTRY: NoEntryAlert("Device overheated"),
  },

  EventName.wrongGear: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("Change gear to [D]",
                              audible_alert=AudibleAlert.chimeGeard, duration_sound=3.),
  },

  # This alert is thrown when the calibration angles are outside of the acceptable range.
  # For example if the device is pointed too much to the left or the right.
  # Usually this can only be solved by removing the mount from the windshield completely,
  # and attaching while making sure the device is pointed straight forward and is level.
  # See https://comma.ai/setup for more information
  EventName.calibrationInvalid: {
    ET.PERMANENT: NormalPermanentAlert("Calibration error", "Re-calibrate after repositioning the device."),
    ET.SOFT_DISABLE: SoftDisableAlert("Calibration error: Re-calibrate after changing the device location"),
    ET.NO_ENTRY: NoEntryAlert("Calibration error: Re-calibrate after changing the device location"),
  },

  EventName.calibrationIncomplete: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: SoftDisableAlert("Calibration in progress"),
    ET.NO_ENTRY: NoEntryAlert("Calibration in progress"),
  },

  EventName.doorOpen: {
    ET.PERMANENT: Alert(
      "Door open",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=0.5),
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("Door open"),
  },

  EventName.seatbeltNotLatched: {
    ET.PERMANENT: Alert(
      "Check seat belt",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=0.5),
    ET.SOFT_DISABLE: SoftDisableAlert("Please fasten your seat belt"),
    ET.NO_ENTRY: NoEntryAlert("Please fasten your seat belt",
                              audible_alert=AudibleAlert.chimeSeatbelt, duration_sound=3.),
  },

  EventName.espDisabled: {
    ET.SOFT_DISABLE: SoftDisableAlert("ESP off"),
    ET.NO_ENTRY: NoEntryAlert("ESP off"),
  },

  EventName.lowBattery: {
    ET.SOFT_DISABLE: SoftDisableAlert("Battery low"),
    ET.NO_ENTRY: NoEntryAlert("Battery low"),
  },

  # Different openpilot services communicate between each other at a certain
  # interval. If communication does not follow the regular schedule this alert
  # is thrown. This can mean a service crashed, did not broadcast a message for
  # ten times the regular interval, or the average interval is more than 10% too high.
  EventName.commIssue: {
    ET.SOFT_DISABLE: SoftDisableAlert("Device process error"),
    ET.NO_ENTRY: NoEntryAlert("Device process error",
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  # Thrown when manager detects a service exited unexpectedly while driving
  EventName.processNotRunning: {
    ET.NO_ENTRY: NoEntryAlert("System Malfunction: Reboot the device",
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.radarFault: {
    ET.SOFT_DISABLE: SoftDisableAlert("Radar error : restart your vehicle"),
    ET.NO_ENTRY: NoEntryAlert("Radar error : restart your vehicle"),
  },

  # Every frame from the camera should be processed by the model. If modeld
  # is not processing frames fast enough they have to be dropped. This alert is
  # thrown when over 20% of frames are dropped.
  EventName.modeldLagging: {
    ET.SOFT_DISABLE: SoftDisableAlert("Driving model lagging"),
    ET.NO_ENTRY: NoEntryAlert("Driving model lagging"),
  },

  # Besides predicting the path, lane lines and lead car data the model also
  # predicts the current velocity and rotation speed of the car. If the model is
  # very uncertain about the current velocity while the car is moving, this
  # usually means the model has trouble understanding the scene. This is used
  # as a heuristic to warn the driver.
  EventName.posenetInvalid: {
    ET.SOFT_DISABLE: SoftDisableAlert("Lane recognition condition is poor."),
    ET.NO_ENTRY: NoEntryAlert("Lane recognition condition is poor."),
  },

  # When the localizer detects an acceleration of more than 40 m/s^2 (~4G) we
  # alert the driver the device might have fallen from the windshield.
  EventName.deviceFalling: {
    ET.SOFT_DISABLE: SoftDisableAlert("Device fell off mount"),
    ET.NO_ENTRY: NoEntryAlert("Device fell off mount"),
  },

  EventName.lowMemory: {
    ET.SOFT_DISABLE: SoftDisableAlert("Insufficient memory: restart the device"),
    ET.PERMANENT: NormalPermanentAlert("Insufficient memory", "Please restart your device"),
    ET.NO_ENTRY: NoEntryAlert("Insufficient memory: restart the device",
                               audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.accFaulted: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise error"),
    ET.PERMANENT: NormalPermanentAlert("Cruise error", ""),
    ET.NO_ENTRY: NoEntryAlert("Cruise error"),
  },

  EventName.controlsMismatch: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Control mismatch"),
  },

  EventName.roadCameraError: {
    ET.PERMANENT: NormalPermanentAlert("Driving camera error", "",
                                       duration_text=10.),
  },

  EventName.driverCameraError: {
    ET.PERMANENT: NormalPermanentAlert("Driver camera error", "",
                                       duration_text=10.),
  },

  EventName.wideRoadCameraError: {
    ET.PERMANENT: NormalPermanentAlert("Wide driving camera error", "",
                                       duration_text=10.),
  },

  # Sometimes the USB stack on the device can get into a bad state
  # causing the connection to the panda to be lost
  EventName.usbError: {
    ET.SOFT_DISABLE: SoftDisableAlert("USB Error: Reboot your device"),
    ET.PERMANENT: NormalPermanentAlert("USB Error: Reboot your device", ""),
    ET.NO_ENTRY: NoEntryAlert("USB Error: Reboot your device"),
  },

  # This alert can be thrown for the following reasons:
  # - No CAN data received at all
  # - CAN data is received, but some message are not received at the right frequency
  # If you're not writing a new car port, this is usually cause by faulty wiring
  EventName.canError: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("CAN error : Check your device"),
    ET.PERMANENT: Alert(
      "CAN error : Check your device",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("CAN error : Check your device"),
  },

  EventName.steerUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("LKAS error : restart your vehicle"),
    ET.PERMANENT: Alert(
      "LKAS error : restart your vehicle",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert("LKAS error : restart your vehicle"),
  },

  EventName.brakeUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise error : restart your vehicle"),
    ET.PERMANENT: Alert(
      "Cruise error : restart your vehicle",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert("Cruise error : restart your vehicle"),
  },

  EventName.reverseGear: {
    ET.PERMANENT: Alert(
      "Gear in [R]",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=0.5),
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("Gear in [R]"),
  },

  # On cars that use stock ACC the car can decide to cancel ACC for various reasons.
  # When this happens we can no long control the car so the user needs to be warned immediately.
  EventName.cruiseDisabled: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise off"),
  },

  # For planning the trajectory Model Predictive Control (MPC) is used. This is
  # an optimization algorithm that is not guaranteed to find a feasible solution.
  # If no solution is found or the solution has a very high cost this alert is thrown.
  EventName.plannerError: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Planner solution error"),
    ET.NO_ENTRY: NoEntryAlert("Planner solution error"),
  },

  # When the relay in the harness box opens the CAN bus between the LKAS camera
  # and the rest of the car is separated. When messages from the LKAS camera
  # are received on the car side this usually means the relay hasn't opened correctly
  # and this alert is thrown.
  EventName.relayMalfunction: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Harness malfunction"),
    ET.PERMANENT: NormalPermanentAlert("Harness malfunction", "Check the device"),
    ET.NO_ENTRY: NoEntryAlert("Harness malfunction"),
  },

  EventName.noTarget: {
    ET.IMMEDIATE_DISABLE: Alert(
      "Unable to use open pilot",
      "There is no vehicle in front",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.chimeDisengage, .4, 2., 3.),
    ET.NO_ENTRY: NoEntryAlert("There is no vehicle in front"),
  },

  EventName.speedTooLow: {
    ET.IMMEDIATE_DISABLE: Alert(
      "Unable to use open pilot",
      "Speed too low",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.chimeDisengage, .4, 2., 3.),
  },

  # When the car is driving faster than most cars in the training data the model outputs can be unpredictable
  EventName.speedTooHigh: {
    ET.WARNING: Alert(
      "Speed is too high",
      "please slow down",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarning2Repeat, 2.2, 3., 4.),
    ET.NO_ENTRY: Alert(
      "Speed is too high",
      "Slow down",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.chimeError, .4, 2., 3.),
  },

  EventName.lowSpeedLockout: {
    ET.PERMANENT: Alert(
      "Cruise error : restart your vehicle",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert("Cruise error : restart your vehicle"),
  },

}
