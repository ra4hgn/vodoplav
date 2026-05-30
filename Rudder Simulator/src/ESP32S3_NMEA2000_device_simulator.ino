/*

ESP32S3 NMEA2000 Rudder Simulator - Симулятор руля NMEA2000 на ESP32-S3

Считывает угол поворота с потенциометра (GPIO4) и отправляет
PGN 127245 (Rudder) в сеть NMEA2000.

Аппаратная конфигурация:
  POT (крутилка)      -> GPIO4
  TWAI TX (CAN H)     -> GPIO17
  TWAI RX (CAN L)     -> GPIO16

*/

#define ESP32_CAN_TX_PIN GPIO_NUM_17  // Пин TX для CAN интерфейса (TWAI)
#define ESP32_CAN_RX_PIN GPIO_NUM_16  // Пин RX для CAN интерфейса (TWAI)
#define USE_N2K_CAN 7  // Принудительное использование библиотеки CAN для ESP32

#include "NMEA2000_CAN.h"  // Автоматически выбирает подходящую CAN библиотеку и создает объект NMEA2000
#include "N2kMessages.h"   // Заголовочный файл для сообщений NMEA2000

// Пин потенциометра (симуляция угла поворота руля)
#define POT_POTENTIOMETER  4

// Список PGN сообщений, которые устройство будет передавать
const unsigned long TransmitMessages[] PROGMEM = {127245L, 0};

// Планировщик для сообщения Rudder (период 200 мс)
tN2kSyncScheduler RudderScheduler(false, 200, 0);

// *****************************************************************************
void OnN2kOpen() {
  RudderScheduler.UpdateNextTime();
}

// *****************************************************************************
// Чтение угла поворота руля с потенциометра
// МАППИНГ: потенциометр 0-4095 -> угол -40..+40 градусов (лево/право на борт)
double ReadRudderAngle() {
  int pot = analogRead(POT_POTENTIOMETER);
  
  // Преобразование: 0 -> -40°, 2047 -> 0°, 4095 -> +40°
  double angleDeg = map(pot, 0, 4095, -40, 40);
  double angleRad = DegToRad(angleDeg);  // Конвертация в радианы для NMEA2000

  //Serial.printf("Rudder: pot=%d  deg=%.1f  rad=%.3f\n", pot, angleDeg, angleRad);

  return angleRad;
}

// *****************************************************************************
void setup() {
  Serial.begin(115200);
  
  // Настройка ADC для ESP32-S3
  analogReadResolution(12);  // 12 бит (0-4095)
  analogSetPinAttenuation(POT_POTENTIOMETER, ADC_11db);  // Диапазон 0-3.3В для конкретного пина

  //Serial.println("ESP32 S3 NMEA2000 Rudder Simulator");
  //Serial.println("PGN 127245 - Rudder position");

  // Установка информации о продукте
  NMEA2000.SetProductInformation("00000001", // Серийный номер
                                 100,        // Код продукта
                                 "Rudder Simulator",  // Модель
                                 "1.0.0.0",  // Версия ПО
                                 "1.0.0.0"   // Версия модели
                                 );
  
  // Установка информации об устройстве
  NMEA2000.SetDeviceInformation(112233, // Уникальный номер
                                160,    // Функция устройства = Steering Control
                                75,     // Класс устройства = Interface
                                2040    // Произвольный код
                               );

  NMEA2000.SetForwardStream(&Serial);
  NMEA2000.SetMode(tNMEA2000::N2km_NodeOnly, 22);
  NMEA2000.EnableForward(false);
  NMEA2000.ExtendTransmitMessages(TransmitMessages);
  NMEA2000.SetOnOpen(OnN2kOpen);
  NMEA2000.Open();
}

// *****************************************************************************
// Хранилище для последнего отправленного N2K сообщения (для диагностики)
static uint32_t lastN2kPGN = 0;
static uint8_t lastN2kData[8];
static uint8_t lastN2kDataLen = 0;

void loop() {
  if (RudderScheduler.IsTime()) {
    RudderScheduler.UpdateNextTime();
    
    tN2kMsg N2kMsg;
    double rudderAngle = ReadRudderAngle();  // Получаем угол в радианах
    
    // Отправка PGN 127245 (Rudder)
    // Параметры: угол в радианах, instance=0, без команды направления
    SetN2kRudder(N2kMsg, rudderAngle, 0, N2kRDO_NoDirectionOrder, N2kDoubleNA);
    NMEA2000.SendMsg(N2kMsg);

    // Сохраняем отправленное сообщение для вывода в диагностику
    lastN2kPGN = N2kMsg.PGN;
    lastN2kDataLen = N2kMsg.DataLen;
    uint8_t copyLen = N2kMsg.DataLen < 8 ? N2kMsg.DataLen : 8;
    memcpy(lastN2kData, N2kMsg.Data, copyLen);
  }
  
  NMEA2000.ParseMessages();
  
  // Диагностика: вывод последнего отправленного N2K сообщения каждые 500 мс
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    Serial.printf("N2K: PGN=%lu Len=%u [", lastN2kPGN, lastN2kDataLen);
    for (uint8_t i = 0; i < lastN2kDataLen; i++) {
      Serial.printf("%02X ", lastN2kData[i]);
    }
    Serial.println("]");
  }
}
