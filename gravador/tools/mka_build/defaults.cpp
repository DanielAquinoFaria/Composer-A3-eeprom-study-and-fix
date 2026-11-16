#include <stdint.h>
#include <stddef.h>
#include "src/lib/macros.h"
#include "Boards.h"
#include "Configuration_Basic.h"
#include "Configuration_Core.h"
#include "Configuration_Temperature.h"
#include "Configuration_Feature.h"
#include "src/lib/conditionals_pre.h"
#include "src/lib/pins.h"
#include "src/lib/conditionals_post.h"
#include "src/core/heater/sensor/thermistor.h"
typedef enum { IS_HOTEND = 0, IS_BED = 1, IS_CHAMBER = 2, IS_COOLER = 3 } Heater_type;
struct ToolSwitchPos
	{
		float X,Y,Speed;
		bool SwitchMove;
	};

static_assert(sizeof(Heater_type)==1, "ARM enum width");
static_assert(sizeof(ToolSwitchPos)==16 && offsetof(ToolSwitchPos,SwitchMove)==12, "tool path ABI");
static_assert(sizeof(float)==4 && sizeof(bool)==1, "scalar ABI");
static_assert(HEATER_COUNT==4 && FAN_COUNT==4 && DRIVER_EXTRUDERS==3 && HOTENDS==2 && SD_COUNT==2, "A3 feature set");
#if HEATER_USES_AD595
#error Unsupported AD595 layout
#endif
constexpr float steps[] = DEFAULT_AXIS_STEPS_PER_UNIT;
constexpr float feedrate[] = DEFAULT_MAX_FEEDRATE;
constexpr uint32_t max_accel[] = DEFAULT_MAX_ACCELERATION;
constexpr uint32_t retract_accel[] = DEFAULT_RETRACT_ACCELERATION;
constexpr float ejerk[] = DEFAULT_EJERK;
constexpr float offset_X[] = HOTEND_OFFSET_X;
constexpr float offset_Y[] = HOTEND_OFFSET_Y;
constexpr float offset_Z[] = HOTEND_OFFSET_Z;
constexpr float Kp[] = DEFAULT_Kp;
constexpr float Ki[] = DEFAULT_Ki;
constexpr float Kd[] = DEFAULT_Kd;
constexpr float Kc[] = DEFAULT_Kc;
constexpr int8_t fan_pins[] = FANS_CHANNELS;
constexpr int8_t auto_fan[] = AUTO_FAN;
constexpr float load[] = PAUSE_PARK_LOAD_LENGTH;
constexpr float unload[] = PAUSE_PARK_UNLOAD_LENGTH;
constexpr ToolSwitchPos path0[] = CHANGE_T0;
constexpr ToolSwitchPos path1[] = CHANGE_T1;
struct __attribute__((packed)) Defaults {
  float steps_E;
  float steps_U;
  float steps_V;
  float home_X;
  float home_Y;
  float home_Z;
  float hotend_0_X;
  float hotend_1_X;
  float hotend_0_Y;
  float hotend_1_Y;
  float hotend_0_Z;
  float hotend_1_Z;
  float switch_offset_X;
  float switch_offset_Y;
  uint16_t preheat_hotend;
  uint16_t preheat_bed;
  uint8_t lcd_brightness;
  float heater_0_Kp;
  float heater_0_Ki;
  float heater_0_Kd;
  float heater_1_Kp;
  float heater_1_Ki;
  float heater_1_Kd;
  float heater_2_Kp;
  float heater_2_Ki;
  float heater_2_Kd;
  float heater_3_Kp;
  float heater_3_Ki;
  float heater_3_Kd;
  bool dir_X;
  bool dir_Y;
  bool dir_Z;
  bool dir_E;
  bool dir_U;
  bool dir_V;
  float steps_X;
  float steps_Y;
  float steps_Z;
  float feedrate_X;
  float feedrate_Y;
  float feedrate_Z;
  float feedrate_E;
  float feedrate_U;
  float feedrate_V;
  uint32_t max_accel_X;
  uint32_t max_accel_Y;
  uint32_t max_accel_Z;
  uint32_t max_accel_E;
  uint32_t max_accel_U;
  uint32_t max_accel_V;
  float acceleration;
  float retract_accel_E;
  float retract_accel_U;
  float retract_accel_V;
  float travel_acceleration;
  float min_feedrate;
  float min_travel_feedrate;
  uint32_t min_segment_us;
  float jerk_X;
  float jerk_Y;
  float jerk_Z;
  float jerk_E;
  float jerk_U;
  float jerk_V;
  uint16_t endstop_logic;
  uint16_t endstop_pullup;
  uint8_t heater_0_type;
  int8_t heater_0_pin;
  uint8_t heater_0_id;
  uint8_t heater_0_pid_min;
  uint8_t heater_0_pid_max_drive;
  uint8_t heater_0_pid_max;
  int16_t heater_0_min_temp;
  int16_t heater_0_max_temp;
  float heater_0_Kc;
  uint8_t heater_0_flags;
  int8_t heater_0_sensor_pin;
  int16_t heater_0_sensor_type;
  int16_t heater_0_adc_low;
  int16_t heater_0_adc_high;
  float heater_0_r25;
  float heater_0_beta;
  float heater_0_pullup;
  float heater_0_shC;
  uint8_t heater_1_type;
  int8_t heater_1_pin;
  uint8_t heater_1_id;
  uint8_t heater_1_pid_min;
  uint8_t heater_1_pid_max_drive;
  uint8_t heater_1_pid_max;
  int16_t heater_1_min_temp;
  int16_t heater_1_max_temp;
  float heater_1_Kc;
  uint8_t heater_1_flags;
  int8_t heater_1_sensor_pin;
  int16_t heater_1_sensor_type;
  int16_t heater_1_adc_low;
  int16_t heater_1_adc_high;
  float heater_1_r25;
  float heater_1_beta;
  float heater_1_pullup;
  float heater_1_shC;
  uint8_t heater_2_type;
  int8_t heater_2_pin;
  uint8_t heater_2_id;
  uint8_t heater_2_pid_min;
  uint8_t heater_2_pid_max_drive;
  uint8_t heater_2_pid_max;
  int16_t heater_2_min_temp;
  int16_t heater_2_max_temp;
  float heater_2_Kc;
  uint8_t heater_2_flags;
  int8_t heater_2_sensor_pin;
  int16_t heater_2_sensor_type;
  int16_t heater_2_adc_low;
  int16_t heater_2_adc_high;
  float heater_2_r25;
  float heater_2_beta;
  float heater_2_pullup;
  float heater_2_shC;
  uint8_t heater_3_type;
  int8_t heater_3_pin;
  uint8_t heater_3_id;
  uint8_t heater_3_pid_min;
  uint8_t heater_3_pid_max_drive;
  uint8_t heater_3_pid_max;
  int16_t heater_3_min_temp;
  int16_t heater_3_max_temp;
  float heater_3_Kc;
  uint8_t heater_3_flags;
  int8_t heater_3_sensor_pin;
  int16_t heater_3_sensor_type;
  int16_t heater_3_adc_low;
  int16_t heater_3_adc_high;
  float heater_3_r25;
  float heater_3_beta;
  float heater_3_pullup;
  float heater_3_shC;
  int8_t fan_0_pin;
  uint16_t fan_0_freq;
  uint8_t fan_0_min;
  int8_t fan_0_auto;
  uint8_t fan_0_flags;
  int8_t fan_1_pin;
  uint16_t fan_1_freq;
  uint8_t fan_1_min;
  int8_t fan_1_auto;
  uint8_t fan_1_flags;
  int8_t fan_2_pin;
  uint16_t fan_2_freq;
  uint8_t fan_2_min;
  int8_t fan_2_auto;
  uint8_t fan_2_flags;
  int8_t fan_3_pin;
  uint16_t fan_3_freq;
  uint8_t fan_3_min;
  int8_t fan_3_auto;
  uint8_t fan_3_flags;
  float linear_advance;
  float load_0;
  float load_1;
  float load_2;
  float unload_0;
  float unload_1;
  float unload_2;
  float pause_retract;
  float pause_retract_feed;
  float pause_load_feed;
  float pause_unload_feed;
  float pause_extrude_feed;
  uint8_t cut_servo;
  uint8_t cut_active;
  uint8_t cut_neutral;
  float path_0_0_X;
  float path_0_0_Y;
  float path_0_0_Speed;
  bool path_0_0_SwitchMove;
  uint8_t path_0_0_padding[3];
  float path_0_1_X;
  float path_0_1_Y;
  float path_0_1_Speed;
  bool path_0_1_SwitchMove;
  uint8_t path_0_1_padding[3];
  float path_0_2_X;
  float path_0_2_Y;
  float path_0_2_Speed;
  bool path_0_2_SwitchMove;
  uint8_t path_0_2_padding[3];
  float path_0_3_X;
  float path_0_3_Y;
  float path_0_3_Speed;
  bool path_0_3_SwitchMove;
  uint8_t path_0_3_padding[3];
  float path_0_4_X;
  float path_0_4_Y;
  float path_0_4_Speed;
  bool path_0_4_SwitchMove;
  uint8_t path_0_4_padding[3];
  float path_0_5_X;
  float path_0_5_Y;
  float path_0_5_Speed;
  bool path_0_5_SwitchMove;
  uint8_t path_0_5_padding[3];
  float path_0_6_X;
  float path_0_6_Y;
  float path_0_6_Speed;
  bool path_0_6_SwitchMove;
  uint8_t path_0_6_padding[3];
  float path_0_7_X;
  float path_0_7_Y;
  float path_0_7_Speed;
  bool path_0_7_SwitchMove;
  uint8_t path_0_7_padding[3];
  float path_0_8_X;
  float path_0_8_Y;
  float path_0_8_Speed;
  bool path_0_8_SwitchMove;
  uint8_t path_0_8_padding[3];
  float path_0_9_X;
  float path_0_9_Y;
  float path_0_9_Speed;
  bool path_0_9_SwitchMove;
  uint8_t path_0_9_padding[3];
  float path_0_10_X;
  float path_0_10_Y;
  float path_0_10_Speed;
  bool path_0_10_SwitchMove;
  uint8_t path_0_10_padding[3];
  float path_0_11_X;
  float path_0_11_Y;
  float path_0_11_Speed;
  bool path_0_11_SwitchMove;
  uint8_t path_0_11_padding[3];
  float path_1_0_X;
  float path_1_0_Y;
  float path_1_0_Speed;
  bool path_1_0_SwitchMove;
  uint8_t path_1_0_padding[3];
  float path_1_1_X;
  float path_1_1_Y;
  float path_1_1_Speed;
  bool path_1_1_SwitchMove;
  uint8_t path_1_1_padding[3];
  float path_1_2_X;
  float path_1_2_Y;
  float path_1_2_Speed;
  bool path_1_2_SwitchMove;
  uint8_t path_1_2_padding[3];
  float path_1_3_X;
  float path_1_3_Y;
  float path_1_3_Speed;
  bool path_1_3_SwitchMove;
  uint8_t path_1_3_padding[3];
  float path_1_4_X;
  float path_1_4_Y;
  float path_1_4_Speed;
  bool path_1_4_SwitchMove;
  uint8_t path_1_4_padding[3];
  float path_1_5_X;
  float path_1_5_Y;
  float path_1_5_Speed;
  bool path_1_5_SwitchMove;
  uint8_t path_1_5_padding[3];
  float path_1_6_X;
  float path_1_6_Y;
  float path_1_6_Speed;
  bool path_1_6_SwitchMove;
  uint8_t path_1_6_padding[3];
  float path_1_7_X;
  float path_1_7_Y;
  float path_1_7_Speed;
  bool path_1_7_SwitchMove;
  uint8_t path_1_7_padding[3];
  float path_1_8_X;
  float path_1_8_Y;
  float path_1_8_Speed;
  bool path_1_8_SwitchMove;
  uint8_t path_1_8_padding[3];
  float path_1_9_X;
  float path_1_9_Y;
  float path_1_9_Speed;
  bool path_1_9_SwitchMove;
  uint8_t path_1_9_padding[3];
  float path_1_10_X;
  float path_1_10_Y;
  float path_1_10_Speed;
  bool path_1_10_SwitchMove;
  uint8_t path_1_10_padding[3];
  float path_1_11_X;
  float path_1_11_Y;
  float path_1_11_Speed;
  bool path_1_11_SwitchMove;
  uint8_t path_1_11_padding[3];
  int8_t sd_0_pin;
  int8_t sd_0_detect;
  uint8_t sd_0_divisor;
  int8_t sd_1_pin;
  int8_t sd_1_detect;
  uint8_t sd_1_divisor;
};
static_assert(sizeof(Defaults)==852, "USER and SYSTEM payload sizes");
extern const Defaults defaults __attribute__((section(".eeprom_defaults"),used)) = {
  steps[3],
  steps[4],
  steps[5],
  0,
  0,
  0,
  offset_X[0],
  offset_X[1],
  offset_Y[0],
  offset_Y[1],
  offset_Z[0],
  offset_Z[1],
  0,
  0,
  PREHEAT_1_TEMP_HOTEND,
  PREHEAT_1_TEMP_BED,
  90,
  Kp[0],
  Ki[0],
  Kd[0],
  Kp[1],
  Ki[1],
  Kd[1],
  DEFAULT_bedKp,
  DEFAULT_bedKi,
  DEFAULT_bedKd,
  DEFAULT_chamberKp,
  DEFAULT_chamberKi,
  DEFAULT_chamberKd,
  INVERT_X_DIR,
  INVERT_Y_DIR,
  INVERT_Z_DIR,
  INVERT_E0_DIR,
  INVERT_E1_DIR,
  INVERT_E2_DIR,
  steps[0],
  steps[1],
  steps[2],
  feedrate[0],
  feedrate[1],
  feedrate[2],
  feedrate[3],
  feedrate[4],
  feedrate[5],
  max_accel[0],
  max_accel[1],
  max_accel[2],
  max_accel[3],
  max_accel[4],
  max_accel[5],
  DEFAULT_ACCELERATION,
  retract_accel[0],
  retract_accel[1],
  retract_accel[2],
  DEFAULT_TRAVEL_ACCELERATION,
  DEFAULT_MINIMUMFEEDRATE,
  DEFAULT_MINTRAVELFEEDRATE,
  DEFAULT_MINSEGMENTTIME,
  DEFAULT_XJERK,
  DEFAULT_YJERK,
  DEFAULT_ZJERK,
  ejerk[0],
  ejerk[1],
  ejerk[2],
  ((uint16_t)(X_MIN_ENDSTOP_LOGIC) << 0) | ((uint16_t)(Y_MIN_ENDSTOP_LOGIC) << 1) | ((uint16_t)(Z_MIN_ENDSTOP_LOGIC) << 2) | ((uint16_t)(Z_PROBE_ENDSTOP_LOGIC) << 3) | ((uint16_t)(X_MAX_ENDSTOP_LOGIC) << 4) | ((uint16_t)(Y_MAX_ENDSTOP_LOGIC) << 5) | ((uint16_t)(Z_MAX_ENDSTOP_LOGIC) << 6) | ((uint16_t)(X2_MIN_ENDSTOP_LOGIC) << 7) | ((uint16_t)(X2_MAX_ENDSTOP_LOGIC) << 8) | ((uint16_t)(Y2_MIN_ENDSTOP_LOGIC) << 9) | ((uint16_t)(Y2_MAX_ENDSTOP_LOGIC) << 10) | ((uint16_t)(Z2_MIN_ENDSTOP_LOGIC) << 11) | ((uint16_t)(Z2_MAX_ENDSTOP_LOGIC) << 12) | ((uint16_t)(FIL_RUNOUT_LOGIC) << 13) | ((uint16_t)(DOOR_OPEN_LOGIC) << 14) | ((uint16_t)(POWER_CHECK_LOGIC) << 15),
  ((uint16_t)(ENDSTOPPULLUP_XMIN) << 0) | ((uint16_t)(ENDSTOPPULLUP_YMIN) << 1) | ((uint16_t)(ENDSTOPPULLUP_ZMIN) << 2) | ((uint16_t)(ENDSTOPPULLUP_ZPROBE) << 3) | ((uint16_t)(ENDSTOPPULLUP_XMAX) << 4) | ((uint16_t)(ENDSTOPPULLUP_YMAX) << 5) | ((uint16_t)(ENDSTOPPULLUP_ZMAX) << 6) | ((uint16_t)(ENDSTOPPULLUP_X2MIN) << 7) | ((uint16_t)(ENDSTOPPULLUP_X2MAX) << 8) | ((uint16_t)(ENDSTOPPULLUP_Y2MIN) << 9) | ((uint16_t)(ENDSTOPPULLUP_Y2MAX) << 10) | ((uint16_t)(ENDSTOPPULLUP_Z2MIN) << 11) | ((uint16_t)(ENDSTOPPULLUP_Z2MAX) << 12) | ((uint16_t)(PULLUP_FIL_RUNOUT) << 13) | ((uint16_t)(PULLUP_DOOR_OPEN) << 14) | ((uint16_t)(PULLUP_POWER_CHECK) << 15),
  0,
  HEATER_0_PIN,
  0,
  PID_DRIVE_MIN,
  PID_DRIVE_MAX,
  PID_MAX,
  HEATER_0_MINTEMP,
  HEATER_0_MAXTEMP,
  Kc[0],
  (PIDTEMP ? 1 : 0) | 2 | (INVERTED_HEATER_PINS ? 4 : 0),
  TEMP_0_PIN,
  TEMP_SENSOR_0,
  0,
  0,
  HOT0_R25,
  HOT0_BETA,
  THERMISTOR_SERIES_RS,
  0,
  0,
  HEATER_1_PIN,
  1,
  PID_DRIVE_MIN,
  PID_DRIVE_MAX,
  PID_MAX,
  HEATER_1_MINTEMP,
  HEATER_1_MAXTEMP,
  Kc[1],
  (PIDTEMP ? 1 : 0) | 2 | (INVERTED_HEATER_PINS ? 4 : 0),
  TEMP_1_PIN,
  TEMP_SENSOR_1,
  0,
  0,
  HOT1_R25,
  HOT1_BETA,
  THERMISTOR_SERIES_RS,
  0,
  1,
  HEATER_BED_PIN,
  2,
  BED_PID_DRIVE_MIN,
  BED_PID_DRIVE_MAX,
  BED_PID_MAX,
  BED_MINTEMP,
  BED_MAXTEMP,
  0,
  (PIDTEMPBED ? 1 : 0) | 2 | (INVERTED_BED_PIN ? 4 : 0),
  TEMP_BED_PIN,
  TEMP_SENSOR_BED,
  0,
  0,
  BED_R25,
  BED_BETA,
  THERMISTOR_SERIES_RS,
  0,
  2,
  HEATER_CHAMBER_PIN,
  3,
  CHAMBER_PID_DRIVE_MIN,
  CHAMBER_PID_DRIVE_MAX,
  CHAMBER_PID_MAX,
  CHAMBER_MINTEMP,
  CHAMBER_MAXTEMP,
  0,
  (PIDTEMPCHAMBER ? 1 : 0) | 2 | (INVERTED_CHAMBER_PIN ? 4 : 0),
  TEMP_CHAMBER_PIN,
  TEMP_SENSOR_CHAMBER,
  0,
  0,
  CHAMBER_R25,
  CHAMBER_BETA,
  THERMISTOR_SERIES_RS,
  0,
  fan_pins[0],
  250,
  FAN_MIN_PWM,
  auto_fan[0],
  FAN_INVERTED ? 1 : 0,
  fan_pins[1],
  250,
  FAN_MIN_PWM,
  auto_fan[1],
  FAN_INVERTED ? 1 : 0,
  fan_pins[2],
  250,
  FAN_MIN_PWM,
  auto_fan[2],
  FAN_INVERTED ? 1 : 0,
  fan_pins[3],
  250,
  FAN_MIN_PWM,
  auto_fan[3],
  FAN_INVERTED ? 1 : 0,
  LIN_ADVANCE_K,
  load[0],
  load[1],
  load[2],
  unload[0],
  unload[1],
  unload[2],
  PAUSE_PARK_RETRACT_LENGTH,
  PAUSE_PARK_RETRACT_FEEDRATE,
  PAUSE_PARK_LOAD_FEEDRATE,
  PAUSE_PARK_UNLOAD_FEEDRATE,
  PAUSE_PARK_EXTRUDE_FEEDRATE,
  CUT_SERVO_ID,
  CUT_ACTIVE_ANGLE,
  CUT_NEUTRAL_ANGLE,
  path0[0].X,
  path0[0].Y,
  path0[0].Speed,
  path0[0].SwitchMove,
  {0,0,0},
  path0[1].X,
  path0[1].Y,
  path0[1].Speed,
  path0[1].SwitchMove,
  {0,0,0},
  path0[2].X,
  path0[2].Y,
  path0[2].Speed,
  path0[2].SwitchMove,
  {0,0,0},
  path0[3].X,
  path0[3].Y,
  path0[3].Speed,
  path0[3].SwitchMove,
  {0,0,0},
  path0[4].X,
  path0[4].Y,
  path0[4].Speed,
  path0[4].SwitchMove,
  {0,0,0},
  path0[5].X,
  path0[5].Y,
  path0[5].Speed,
  path0[5].SwitchMove,
  {0,0,0},
  path0[6].X,
  path0[6].Y,
  path0[6].Speed,
  path0[6].SwitchMove,
  {0,0,0},
  path0[7].X,
  path0[7].Y,
  path0[7].Speed,
  path0[7].SwitchMove,
  {0,0,0},
  path0[8].X,
  path0[8].Y,
  path0[8].Speed,
  path0[8].SwitchMove,
  {0,0,0},
  path0[9].X,
  path0[9].Y,
  path0[9].Speed,
  path0[9].SwitchMove,
  {0,0,0},
  path0[10].X,
  path0[10].Y,
  path0[10].Speed,
  path0[10].SwitchMove,
  {0,0,0},
  path0[11].X,
  path0[11].Y,
  path0[11].Speed,
  path0[11].SwitchMove,
  {0,0,0},
  path1[0].X,
  path1[0].Y,
  path1[0].Speed,
  path1[0].SwitchMove,
  {0,0,0},
  path1[1].X,
  path1[1].Y,
  path1[1].Speed,
  path1[1].SwitchMove,
  {0,0,0},
  path1[2].X,
  path1[2].Y,
  path1[2].Speed,
  path1[2].SwitchMove,
  {0,0,0},
  path1[3].X,
  path1[3].Y,
  path1[3].Speed,
  path1[3].SwitchMove,
  {0,0,0},
  path1[4].X,
  path1[4].Y,
  path1[4].Speed,
  path1[4].SwitchMove,
  {0,0,0},
  path1[5].X,
  path1[5].Y,
  path1[5].Speed,
  path1[5].SwitchMove,
  {0,0,0},
  path1[6].X,
  path1[6].Y,
  path1[6].Speed,
  path1[6].SwitchMove,
  {0,0,0},
  path1[7].X,
  path1[7].Y,
  path1[7].Speed,
  path1[7].SwitchMove,
  {0,0,0},
  path1[8].X,
  path1[8].Y,
  path1[8].Speed,
  path1[8].SwitchMove,
  {0,0,0},
  path1[9].X,
  path1[9].Y,
  path1[9].Speed,
  path1[9].SwitchMove,
  {0,0,0},
  path1[10].X,
  path1[10].Y,
  path1[10].Speed,
  path1[10].SwitchMove,
  {0,0,0},
  path1[11].X,
  path1[11].Y,
  path1[11].Speed,
  path1[11].SwitchMove,
  {0,0,0},
  SD0_SS_PIN,
  SD_DETECT_PIN,
  SD0_SPEED_DIVISOR,
  SD1_SS_PIN,
  SD_DETECT_PIN,
  SD1_SPEED_DIVISOR
};
