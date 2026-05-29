# Решение проблемы с распознаванием платы `esp32s3-devkitc-1` в PlatformIO

## Проблема
PlatformIO выдает ошибку: `UnknownBoard: Unknown board ID 'esp32s3-devkitc-1'`

## Причина
Неправильное название платы в файле `platformio.ini`. Правильное название содержит дефисы.

## Пошаговое решение

### Шаг 1: Исправить файл `platformio.ini`
Откройте файл `platformio.ini` и замените строку:
```ini
board = esp32s3-devkitc-1
```
на:
```ini
board = esp32-s3-devkitc-1
```

Полный исправленный файл:
```ini
[env:esp32s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
lib_deps = 
    ttlappalainen/NMEA2000@^4.22.0
    offspring/NMEA2000_esp32@add-esp32s3
    sparkfun/SparkFun BME280@^2.0.9
```

### Шаг 2: Обновить PlatformIO (рекомендуется)
```bash
pio upgrade
```

### Шаг 3: Проверить установку платформы espressif32
```bash
pio platform list
```
Если платформа не установлена:
```bash
pio platform install espressif32
```

### Шаг 4: Проверить распознавание платы
```bash
pio boards esp32-s3-devkitc-1
```

### Шаг 5: Установить библиотеки
```bash
pio pkg install
```
или
```bash
pio run
```

## Если библиотеки все еще не устанавливаются

### Вариант A: Установить через PlatformIO Home в VS Code
1. Откройте PlatformIO Home (иконка на левой панели)
2. Перейдите в "Libraries"
3. Установите библиотеки:
   - `NMEA2000` от ttlappalainen
   - `NMEA2000_esp32` от offspring
   - `SparkFun BME280` от sparkfun

### Вариант B: Использовать прямые ссылки в platformio.ini
```ini
lib_deps = 
    https://github.com/ttlappalainen/NMEA2000.git#4.22.0
    https://github.com/offspring/NMEA2000_esp32.git#add-esp32s3
    https://github.com/sparkfun/SparkFun_BME280.git#2.0.9
```

### Вариант C: Установить библиотеки локально
```bash
# Создать папку для библиотек
mkdir -p lib

# Перейти в папку lib
cd lib

# Клонировать библиотеки
git clone https://github.com/ttlappalainen/NMEA2000.git
git clone https://github.com/offspring/NMEA2000_esp32.git
git clone https://github.com/sparkfun/SparkFun_BME280.git

# Вернуться в корень проекта
cd ..
```

Изменить `platformio.ini`:
```ini
lib_deps = 
    lib/NMEA2000
    lib/NMEA2000_esp32
    lib/SparkFun_BME280
```

## Проверка решения

### Проверка 1: Компиляция проекта
```bash
pio run
```
Если компиляция успешна - проблема решена.

### Проверка 2: Просмотр установленных библиотек
```bash
pio pkg list
```

### Проверка 3: Просмотр структуры проекта
```bash
tree .pio -d
```

## Частые ошибки и решения

### Ошибка 1: "Could not find library"
**Решение:** Убедитесь, что библиотеки установлены в `.pio/libdeps/esp32s3/`

### Ошибка 2: "GitHub rate limit exceeded"
**Решение:** Используйте локальную установку библиотек (Вариант C)

### Ошибка 3: "Branch add-esp32s3 not found"
**Решение:** Используйте основную ветку:
```ini
offspring/NMEA2000_esp32
```

## Краткий чеклист
- [ ] Исправить `board = esp32-s3-devkitc-1` в platformio.ini
- [ ] Обновить PlatformIO: `pio upgrade`
- [ ] Установить библиотеки: `pio pkg install`
- [ ] Проверить компиляцию: `pio run`

После этих шагов PlatformIO должен распознать плату и установить все необходимые библиотеки автоматически.