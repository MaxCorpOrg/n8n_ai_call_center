# VPS SIP Bridge: Mango -> Asterisk -> ElevenLabs

Минимальный рабочий контур для полноценного голосового AI через ElevenLabs, когда Mango не дает создать trunk на IP ElevenLabs.

## 1) Что нужно заранее

- VPS с Ubuntu 22.04+ и белым статическим IP.
- Root/sudo доступ на VPS.
- В ElevenLabs уже создан агент (у вас: `agent_8801kgybyekned2a8yae6rp8hk3q`).

## 2) Файлы

- `.env.example` — пример переменных.
- `bootstrap_ubuntu.sh` — автоматическая установка и настройка Asterisk.
- `templates/pjsip.conf.template` — SIP параметры.
- `templates/extensions.conf.template` — маршрутизация вызова.

## 3) Быстрый запуск на VPS

Скопируйте папку `sip-bridge/asterisk` на VPS и выполните:

```bash
cd /root/asterisk
cp .env.example .env
```

Заполните `.env`:

- `PUBLIC_IP` — IP VPS.
- `MANGO_IP` — SIP source IP Mango (если неизвестен, временно `81.88.86.55`, потом уточнить у поддержки).
- `TARGET_NUMBER_E164` — целевой номер для ElevenLabs в quick mode (например `+79923298897`).
- `BRIDGE_EXT` — extension для quick mode (по умолчанию `100`).

Запуск:

```bash
sudo bash bootstrap_ubuntu.sh .env
```

## 4) Что ставить в Mango

### Настройка trunk

- `IP-адрес`: `PUBLIC_IP` вашего VPS.
- `Порт`: `5060`.
- `Команды DTMF`: `Не обрабатывать на стороне ВАТС`.
- `Режим DTMF`: `RFC2833`.
- `Голосовые кодеки`: только `G.711A`.
- `Режим работы`: `UDP`.

### Маршрутизация

Вариант A (быстрый):

- В `Преобразование` отправляйте на extension `100` (или ваш `BRIDGE_EXT`).
- Asterisk на VPS переведет на `TARGET_NUMBER_E164`.

Вариант B (динамический):

- Передавайте из Mango целевой номер (только цифры или `+E164`).
- Asterisk отправит его как SIP user в ElevenLabs.

## 5) Проверка

```bash
asterisk -rvvv
pjsip set logger on
```

Сделайте тестовый звонок на номер в Mango и смотрите INVITE/ответы.

## 6) Дальше после стабильного SIP

1. Импортируйте номер/SIP trunk в ElevenLabs.
2. Получите `agent_phone_number_id`.
3. В n8n workflow `VOICE_INBOUND_AGENT (draft)` укажите этот `agent_phone_number_id` в `Eleven | Config`.
4. Запускайте исходящие через:
   - `POST https://www.n-8-n.site/webhook/eleven/outbound-call`
