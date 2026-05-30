"""
ESP32S3 NMEA2000 Rudder Simulator - MicroPython version
Симулятор руля NMEA2000 на ESP32-S3 (MicroPython)

Считывает угол поворота с потенциометра (GPIO5) и отправляет
PGN 127245 (Rudder) в сеть NMEA2000.

Аппаратная конфигурация:
  POT (крутилка)      -> GPIO5
  TWAI TX (CAN H)     -> GPIO17
  TWAI RX (CAN L)     -> GPIO16

Основано на Arduino-версии: src/ESP32S3_NMEA2000_device_simulator.ino
"""
# pylint: disable=no-member

import machine
import struct
import math
import time


# ===== Конфигурация пинов =====
PIN_POT = 5               # Потенциометр (вход АЦП)
PIN_LED_STATUS = 15        # Светодиод статуса работы
PIN_LED_ACTIVE = 3         # Светодиод активности (при отправке)
PIN_CAN_TX = 17            # CAN TX (TWAI)
PIN_CAN_RX = 16            # CAN RX (TWAI)


# ===== Параметры NMEA2000 =====
N2K_SOURCE_ADDR = 22       # Адрес этого устройства в сети N2K
N2K_PGN_RUDDER = 127245    # PGN для данных руля
N2K_PRIORITY = 2           # Приоритет (2 — типично для руля)
CAN_BAUDRATE = 250000      # NMEA2000 использует 250 кбит/с
SEND_INTERVAL_MS = 200     # Период отправки PGN (мс)

# ===== Параметры руля =====
RUDDER_INSTANCE = 0              # Номер экземпляра руля
DIR_ORDER_NO_ORDER = 0           # N2kRDO_NoDirectionOrder (без команды)


# ================================================================
# ИНИЦИАЛИЗАЦИЯ ПЕРИФЕРИИ
# ================================================================

# ---- Светодиоды ----
led_status = machine.Pin(PIN_LED_STATUS, machine.Pin.OUT)
led_active = machine.Pin(PIN_LED_ACTIVE, machine.Pin.OUT)
led_status.off()
led_active.off()

# ---- АЦП (потенциометр) ----
#   ESP32-S3: 12 бит, 0-4095, диапазон 0-3.3 В
adc = machine.ADC(machine.Pin(PIN_POT))
adc.atten(machine.ADC.ATTN_11DB)       # 0..3.3 В
adc.width(machine.ADC.WIDTH_12BIT)     # 12 бит

# ---- CAN-шина (TWAI) ----
#   machine.CAN использует встроенный контроллер TWAI ESP32-S3.
#   Параметр extframe=True для 29-битных идентификаторов NMEA2000.
try:
    can = machine.CAN(0,
                      tx=PIN_CAN_TX,
                      rx=PIN_CAN_RX,
                      mode=machine.CAN.NORMAL,
                      baud=CAN_BAUDRATE,
                      extframe=True)
    print("CAN: TWAI инициализирован (250 кбит/с)")
except AttributeError:
    # Альтернатива: некоторые прошивки используют встроенный модуль esp32_can
    try:
        import esp32_can
        can = esp32_can.CAN(0,
                            tx=PIN_CAN_TX,
                            rx=PIN_CAN_RX,
                            mode=esp32_can.CAN.NORMAL,
                            baud=CAN_BAUDRATE,
                            extframe=True)
        print("CAN: esp32_can инициализирован (250 кбит/с)")
    except ImportError:
        print("ВНИМАНИЕ: не удалось найти модуль CAN. Работа без CAN.")
        can = None
except Exception as e:
    print(f"ОШИБКА инициализации CAN: {e}")
    can = None


# ================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ================================================================

def pgn_to_can_id(pgn, priority=N2K_PRIORITY, source=N2K_SOURCE_ADDR, dp=1):
    """
    Преобразует PGN в 29-битный CAN ID для NMEA2000.

    Структура NMEA2000 CAN ID (29 бит, extended frame):

        Bit 28-26  Priority       (3 бита)
        Bit 25     Reserved       (0)
        Bit 24     Data Page (DP)
        Bit 23-16  PDU Format PF  (8 бит)
        Bit 15-8   PDU Specific PS(8 бит)
        Bit 7-0    Source Address (8 бит)

    Для PGN 127245 = 0x1F10D:
      DP = 1, PF = 0xF1 = 241, PS = 0x0D = 13
      PGN = (1<<16) | (241<<8) | 13 = 127245 ✓
    """
    pf = (pgn >> 8) & 0xFF
    ps = pgn & 0xFF
    can_id = (priority << 26) | (dp << 24) | (pf << 16) | (ps << 8) | source
    return can_id


def read_rudder_angle():
    """
    Читает напряжение с потенциометра и преобразует в угол руля.

    Маппинг:
       0 АЦП  -> -40° (лево на борт)
    2047 АЦП  ->   0° (прямо)
    4095 АЦП  -> +40° (право на борт)

    Возвращает угол в радианах (требование NMEA2000).
    """
    pot = adc.read()

    # Линейное преобразование: 0..4095 -> -40..+40 градусов
    angle_deg = (pot / 4095.0) * 80.0 - 40.0
    angle_rad = math.radians(angle_deg)

    # Вспышка светодиода активности
    led_active.on()
    time.sleep_ms(5)
    led_active.off()

    return angle_rad


def encode_rudder(position_rad,
                  instance=RUDDER_INSTANCE,
                  direction_order=DIR_ORDER_NO_ORDER):
    """
    Кодирует PGN 127245 (Rudder) в массив байтов для отправки по CAN.

    Формат сообщения (6 байт, помещается в один CAN-фрейм):

      Byte 0     Rudder Instance          (uint8)
      Byte 1     Direction Order          (uint8, N2kRackDetectionOrder)
      Bytes 2-5  Position                 (IEEE 754 single float, радианы)

    Angle Order опущен (unavailable / N2kDoubleNA),
    так как это симулятор без управления рулём.
    """
    data = bytearray(6)
    data[0] = instance & 0xFF
    data[1] = direction_order & 0xFF
    struct.pack_into('<f', data, 2, position_rad)   # little-endian float32
    return data


def send_rudder():
    """Собирает и отправляет PGN 127245 (Rudder) в шину NMEA2000."""
    if can is None:
        return  # CAN не инициализирован — ничего не делаем

    angle_rad = read_rudder_angle()
    can_id = pgn_to_can_id(N2K_PGN_RUDDER)
    data = encode_rudder(angle_rad)

    try:
        can.send(data, id=can_id, timeout=0)
    except Exception as e:
        print(f"Ошибка отправки CAN: {e}")


# ================================================================
# ОСНОВНОЙ ЦИКЛ
# ================================================================

led_status.on()   # Индикация работы устройства

print("\n==============================================")
print("  ESP32-S3 NMEA2000 Rudder Simulator")
print("  MicroPython версия")
print("==============================================")
print(f"  PGN:      {N2K_PGN_RUDDER} (Rudder)")
print(f"  CAN:      TX=GPIO{PIN_CAN_TX}, RX=GPIO{PIN_CAN_RX}")
print(f"  POT:      GPIO{PIN_POT}")
print(f"  LED:      STATUS=GPIO{PIN_LED_STATUS}, ACTIVE=GPIO{PIN_LED_ACTIVE}")
print(f"  Период:   {SEND_INTERVAL_MS} мс")
print(f"  Адрес:    {N2K_SOURCE_ADDR}")
print("==============================================\n")


last_send = time.ticks_ms()
last_diag = time.ticks_ms()

while True:
    now = time.ticks_ms()

    # --- Отправка PGN 127245 с заданным периодом ---
    if time.ticks_diff(now, last_send) >= SEND_INTERVAL_MS:
        last_send = now
        send_rudder()

    # --- Диагностика АЦП (раз в 500 мс) ---
    if time.ticks_diff(now, last_diag) >= 500:
        last_diag = now
        raw = adc.read()
        angle_deg = (raw / 4095.0) * 80.0 - 40.0
        print(f"ADC[GPIO{PIN_POT}] raw={raw:4d} (0-4095)  "
              f"угол={angle_deg:+6.1f}°  "
              f"рад={math.radians(angle_deg):+.4f}")

    # Небольшая задержка для снижения нагрузки на CPU
    time.sleep_ms(10)
