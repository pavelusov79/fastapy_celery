import datetime
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import insert, select, create_engine

from celery import Celery
from app.models import UserTrackedGoods, Goods
from config import *


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

celery = Celery('tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}')


@celery.task(name='parse_to_db')
def get_data(grade, user_id, parse_till, interval):
    while datetime.datetime.now() < parse_till:
        print('start parsing...')
        url = f'https://www.wildberries.ru/catalog/{grade}/detail.aspx'
        options = Options()
        user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'
        options.add_argument('--headless')
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--no-sandbox")
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            name = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//h1'))).text.strip()
            try:
                brand_name = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
                    By.XPATH, '//a[contains(@class, "product-page__header-brand")]'))).text
            except Exception:
                brand_name = 'No name'
            try:
                el = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//ins[contains(@class, "price-block__final-price")]')))
                price = int(el.get_attribute('innerHTML').strip().replace('&nbsp;', '').replace('₽', ''))
            except Exception:
                price = 0
            print('success data = ', name, brand_name, price)
            try:
                with engine.connect() as session:
                    query = select(Goods).where(Goods.fk_user == user_id, Goods.grade == grade)
                    res = session.execute(query)
                    res = res.scalars().one()
                    # print('res = ', res)
                    stmt = insert(UserTrackedGoods).values(fk_goods=res, fk_user=user_id, price=price,
                                                           brand_name=brand_name,  date_field=datetime.datetime.now())
                    session.execute(stmt)
                    session.commit()
                    session.close()
            except Exception as er:
                return {'status': 'error to db', 'details': er}
            driver.quit()
            time.sleep(interval)
        except Exception as e:
            driver.quit()
            return {'status': 'error', 'details': e}
