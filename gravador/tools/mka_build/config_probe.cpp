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
typedef int8_t pin_t;
typedef enum { IS_HOTEND = 0, IS_BED = 1, IS_CHAMBER = 2, IS_COOLER = 3 } Heater_type;
struct ToolSwitchPos { float X, Y, Speed; bool SwitchMove; };
extern const unsigned char abi[] = {sizeof(Heater_type), sizeof(ToolSwitchPos), HEATER_COUNT, FAN_COUNT, DRIVER_EXTRUDERS, HOTENDS, SD_COUNT};
