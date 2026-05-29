# Руководство по заливке прошивки на ESP32-S3

## Обзор
Это руководство описывает процесс компиляции и заливки прошивки на плату ESP32-S3 DevKitC-1 для проекта NMEA2000 Device Simulator.

## Подготовка оборудования

### 1. Подключение устройства
- Подключите плату ESP32-S3 DevKitC-1 к компьютеру через USB-C кабель
- Убедитесь, что драйверы USB установлены (для Windows может потребоваться установка драйверов CP210x или CH340)

### 2. Определение COM-порта
- **Linux/Mac**: устройство будет доступно как `/dev/ttyUSB0` или `/dev/ttyACM0`
- **Windows**: устройство будет доступно как `COM3`, `COM4` и т.д.

Проверить подключенные устройства:
```bash
# Linux/Mac
ls /dev/ttyUSB* /dev/ttyACM*

# Windows (в командной строке)
mode
```

## Команды PlatformIO

### 1. Компиляция проекта
```bash
pio run
```
Эта команда только компилирует проект без заливки на устройство.

### 2. Заливка прошивки на устройство
```bash
pio run --target upload
```
Или сокращенная версия:
```bash
pio run -t upload
```

Эта команда:
1. Скомпилирует проект (если нужно)
2. Определит подключенное устройство
3. Загрузит прошивку на устройство

### 3. Мониторинг последовательного порта
```bash
pio device monitor
```
Параметры монитора:
- Скорость: 115200 бод (по умолчанию)
- Для выхода: `Ctrl+]` или `Ctrl+C`

### 4. Очистка проекта
```bash
pio run --target clean
```
Удаляет все скомпилированные файлы.

### 5. Полная пересборка
```bash
pio run --target clean && pio run
```

## Расположение скомпилированных файлов

Скомпилированные файлы находятся в директории `.pio/build/esp32s3/`:

### Основные файлы:
1. **`firmware.bin`** (318 KB) - основная прошивка
   - Путь: `.pio/build/esp32s3/firmware.bin`
   - Используется для загрузки на устройство

2. **`bootloader.bin`** (15 KB) - загрузчик
   - Путь: `.pio/build/esp32s3/bootloader.bin`

3. **`partitions.bin`** (3 KB) - таблица разделов
   - Путь: `.pio/build/esp32s3/partitions.bin`

4. **`firmware.elf`** - ELF файл с отладочной информацией
   - Путь: `.pio/build/esp32s3/firmware.elf`

## Ручная загрузка через esptool.py

Если PlatformIO не работает, можно использовать esptool.py напрямую:

### 1. Установка esptool
```bash
pip install esptool
```

### 2. Стирание флеш-памяти
```bash
esptool.py --chip esp32s3 --port /dev/ttyACM0 erase_flash
```

### 3. Загрузка прошивки
```bash
esptool.py --chip esp32s3 --port /dev/ttyACM0 \
  --baud 460800 \
  write_flash \
  -z 0x10000 .pio/build/esp32s3/firmware.bin
```

### 4. Загрузка с разделами
```bash
esptool.py --chip esp32s3 --port /dev/ttyACM0 \
  --baud 460800 \
  write_flash \
  0x1000 .pio/build/esp32s3/bootloader.bin \
  0x8000 .pio/build/esp32s3/partitions.bin \
  0x10000 .pio/build/esp32s3/firmware.bin
```

## Решение проблем

### 1. Ошибка "Port not found"
- Проверьте подключение USB кабеля
- Убедитесь, что драйверы установлены
- Попробуйте другой USB порт

### 2. Ошибка "Failed to connect"
- Нажмите кнопку BOOT на плате во время подключения
- Нажмите кнопку EN (Reset) для перезагрузки

### 3. Ошибка разрешений (Linux)
```bash
# Добавить пользователя в группу dialout
sudo usermod -a -G dialout $USER

# Или установите udev правила PlatformIO
curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/master/scripts/99-platformio-udev.rules | sudo tee /etc/udev/rules.d/99-platformio-udev.rules
sudo service udev restart
```

### 4. Устройство не определяется
```bash
# Проверить доступные устройства
pio device list

# Посмотреть логи USB
dmesg | tail -20
```

## Проверка работы

После успешной загрузки:
1. Откройте монитор последовательного порта:
   ```bash
   pio device monitor
   ```
2. Должны появиться сообщения:
   ```
   ESP32 S3 NMEA2000 Device simulator. Temperature and humidity
   skpang.co.uk 10/2025
   ```
3. Светодиоды на плате должны мигать в соответствии с программой

## Автоматизация

Для автоматической загрузки при изменении кода можно использовать:
```bash
# Следить за изменениями и автоматически заливать
pio run --target upload --environment esp32s3 --watch
```

## Дополнительные ресурсы

- [Документация PlatformIO](https://docs.platformio.org/)
- [Документация ESP32-S3](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/)
- [Исходный код проекта (оригинал)](https://github.com/skpang/ESP32S3_NMEA2000_device_simulator)
- [Репозиторий ra4hgn/vodoplav](https://github.com/ra4hgn/vodoplav) — проект в подпапке `esp32s3_nmea2000/`

---
*Последнее обновление: 08.04.2026*