import urllib, http.client
import time
import json
# ці модулі необхідні для генерації підпису API
import hmac, hashlib
# ввести ключі API, які надала біржа
API_KEY = 'YOUR API KEY'
# зверніть увагу, що, додана 'b' перед строкою
API_SECRET = ‘b'YOUR API SECRET'
# Вказуємо валютну пару
CURRENCY_1 = 'BTC' 
CURRENCY_2 = 'USD'
CURRENCY_1_MIN_QUANTITY = 0.001 # мінімальна сума ставки - береться із https://api.exmo.com/v1/pair_settings/
ORDER_LIFE_TIME = 3 # час, через який відміняється невикористаний ордер на покупку CURRENCY_1
STOCK_FEE = 0.002 # Комісія, яку бере біржа (0.002 = 0.2%)
AVG_PRICE_PERIOD = 15 # За який період брати середню ціну (хвилини)
CAN_SPEND = 5 # Скільки тратити CURRENCY_2 кожен раз при покупці CURRENCY_1
PROFIT_MARKUP = 0.001 # Необхідний профіт з кожної угоди (0.001 = 0.1%)
DEBUG = True # True – виводити інформацію про налагодження, False – нічого не виводити
STOCK_TIME_OFFSET = 0 # Синхронізація часу біржі з поточним часом
# базові налаштування
API_URL = 'api.exmo.com'
API_VERSION = 'v1'
# Створюємо клас виключень
class ScriptError(Exception):
    pass
class ScriptQuitCondition(Exception):
    pass
CURRENT_PAIR = CURRENCY_1 + '_' + CURRENCY_2
# всі звернення до API проходять через дану функцію
def call_api(api_method, http_method="POST", **kwargs):
    payload = {'nonce': int(round(time.time()*1000))}
    if kwargs:
        payload.update(kwargs)
    payload =  urllib.parse.urlencode(payload)
    H = hmac.new(key=API_SECRET, digestmod=hashlib.sha512)
    H.update(payload.encode('utf-8'))
    sign = H.hexdigest()
    headers = {"Content-type": "application/x-www-form-urlencoded",
           "Key":API_KEY,
           "Sign":sign}
    conn = http.client.HTTPSConnection(API_URL, timeout=60)
    conn.request(http_method, "/"+API_VERSION + "/" + api_method, payload, headers)
    response = conn.getresponse().read()
    conn.close()
    try:
        obj = json.loads(response.decode('utf-8'))
        if 'error' in obj and obj['error']:
            raise ScriptError(obj['error'])
        return obj
    except json.decoder.JSONDecodeError:
        raise ScriptError('Помилка аналізу повернених даних, отримана строка', response)
# Реалізація алгоритму
def main_flow():
    try:
        # Отримуємо список активних ордерів
        try:
            opened_orders = call_api('user_open_orders')[CURRENCY_1 + '_' + CURRENCY_2]
        except KeyError:
            if DEBUG:
                print('Відкритих ордерів намає’)
            opened_orders = []
        sell_orders = []
        # Чи є невикористані ордери на продаж  CURRENCY_1?
        for order in opened_orders:
            if order['type'] == 'sell':
                # Чи є невикористані ордери на продаж CURRENCY_1, вихід
                raise ScriptQuitCondition('Вихід, чекаємо аж до виповнення / закриття всіх ордерів на продаж (один ордер може бути розбитий біржею на кілька і виконуватися частинами)')
            else:
                # Запам’ятовуємо ордера на покупку CURRENCY_1
                sell_orders.append(order)
        # Перевіряємо, чи є відкриті ордера на покупку CURRENCY_1
        if sell_orders: # відкриті ордера є
            for order in sell_orders:
                # Перевіряємо, чи є частково виконані
                if DEBUG:
                    print('Перевіряємо, що відбувається з відкладеним ордером ', order['order_id'])
                try:
                    order_history = call_api('order_trades', order_id=order['order_id'])
                    # за ордером вже є часткове виконання, вихід                   
	  raise ScriptQuitCondition ('Вихід, продовжуємо сподіватися докупити валюту за тим курсом, за яким вже купили частину ')
                except ScriptError as e:
                    if 'Error 50304' in str(e):
                        if DEBUG:
                            print('Частково виконаних ордерів немає ')
                            time_passed = time.time() + STOCK_TIME_OFFSET*60*60 - int(order['created'])
                        if time_passed > ORDER_LIFE_TIME * 60:
                            # Ордер вже давно висить, нікому не потрібний, скасовуємо
                            call_api('order_cancel', order_id=order['order_id'])
                            raise ScriptQuitCondition('Скасовуємо ордер -за ' + str(ORDER_LIFE_TIME) + ' хвилин не вдалося купити '+ str(CURRENCY_1))
                        else:
                          raise ScriptQuitCondition('Вихід, продовжуємо сподіватися купити валюту за вказаною раніше курсу, з часу створення ордера пройшло% s секунд'%str(time_passed))
                    else:
                        raise ScriptQuitCondition(str(e))
        else: # Відкритих ордерів немає
            balances = call_api('user_info')['balances']
            if float(balances[CURRENCY_1]) >= CURRENCY_1_MIN_QUANTITY: 
# Чи є в наявності CURRENCY_1, яку можна продати?
#Вираховуємо курс для продажу.
 #Нам треба продати всю валюту, яку купили, на суму, за яку купили + трохи #навару і мінус комісія біржі
#При цьому важливий момент, що валюти у нас менше, ніж купили - біржі пішла #комісія 
 0.00134345 1.5045
                wanna_get = CAN_SPEND + CAN_SPEND * (STOCK_FEE+PROFIT_MARKUP)  # скільки хочемо отримати за наше кількість
                print('sell', balances[CURRENCY_1], wanna_get, (wanna_get/float(balances[CURRENCY_1])))
                new_order = call_api(
                    'order_create',
                    pair=CURRENT_PAIR,
                    quantity = balances[CURRENCY_1],
                    price=wanna_get/float(balances[CURRENCY_1]),
                    type='sell'
                print(new_order)
                if DEBUG:
                    print('Створено ордер на продаж ', CURRENCY_1, new_order['order_id'])
            else:
                # CURRENCY_1 немає, треба докупити
                 # Чи достатньо грошей на балансі у валюті CURRENCY_2 (Баланс >= CAN_SPEND)
                if float(balances[CURRENCY_2]) >= CAN_SPEND:
                    # Дізнатися середню ціну за AVG_PRICE_PERIOD, по якій продають CURRENCY_1
#Exmo не надає такого методу в API, але надає інші, до яких можна спробувати прив'язатися.
#У них є метод required_total, який дозволяє підрахувати курс, але,
#по-перше, схоже він бере поточну ринкову ціну (а мені потрібна в динаміці), а
#по-друге алгоритм розрахунку прихований і може змінитися в будь-який момент.
#Зараз я бачу два шляхи - або дивитися поточні відкриті ордера, або останні зроблені угоди.
#Обидва варіанти мені не дуже подобаються, але завершення угоди покажуть реальні ціни за якими продавали / купували,
#а відкриті ордера покажуть ціни, за якими тільки збираються продати / купити - тобто завищені і занижені.
#Так що беремо інформацію з завершених угод.                    """
                    deals = call_api('trades', pair=CURRENT_PAIR)
                    prices = []
                    for deal in deals[CURRENT_PAIR]:
                        time_passed = time.time() + STOCK_TIME_OFFSET*60*60 - int(deal['date'])
                        if time_passed < AVG_PRICE_PERIOD*60:
                            prices.append(float(deal['price']))
                    try:        
                        avg_price = sum(prices)/len(prices)
#Порахувати, скільки валюти CURRENCY_1 можна купити.
#На суму CAN_SPEND за мінусом STOCK_FEE, і з урахуванням PROFIT_MARKUP
# (= Нижче середньої ціни ринку, з урахуванням комісії і бажаного профіту)
# купити більше, тому що біржа потім забере шматок
                        my_need_price = avg_price - avg_price * (STOCK_FEE+PROFIT_MARKUP) 
                        my_amount = CAN_SPEND/my_need_price
                        print('buy', my_amount, my_need_price)
                        # Чи допускається купівля такого кол-ва валюти (тобто не порушується мінімальна сума угоди)
                        if my_amount >= CURRENCY_1_MIN_QUANTITY:
                            new_order = call_api(
                                'order_create',
                                pair=CURRENT_PAIR,
                                quantity = my_amount,
                                price=my_need_price,
                                type='buy'
                            print(new_order)
                            if DEBUG:
                                print('Создан ордер на покупку', new_order['order_id'])
                        else: # ми можемо купити занадто мало на нашу суму
                            raise ScriptQuitCondition('Вихід, не вистачає грошей на створення ордера')
                    except ZeroDivisionError:
                        print('Неможливо обчислити середню ціну', prices)
                else:
                    raise ScriptQuitCondition('Вихід, не вистачає грошей')
    except ScriptError as e:
        print(e)
    except ScriptQuitCondition as e:
        if DEBUG:
            print(e)
        pass
    except Exception as e:
        print("!!!!",e)
while(True):
    main_flow()
    time.sleep(1)