import json
import os
import random
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import geckodriver_autoinstaller
import chromedriver_autoinstaller
import pyperclip
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

import logging_config as log
from utils.date_utils import DateUtils
from utils.exception_utils import ExceptionUtils
from lxml.html import fromstring


class ScrapUtils:
    """
    크롤링 관련 유틸
    """

    NUMBER_FORMAT = re.compile(r'[\d]+[.,\d]+|[\d]*[.][\d]+|[\d]+')

    def __init__(self, driver_url=None, mobile_device=None, driver_type=None, user_data_dir=None, execute_path=None):
        self.logger = log.get_logger(self.__class__.__name__)
        self.driver_url = driver_url
        self.proc = None
        self.driver = self.load_driver(driver_url, mobile_device, driver_type, user_data_dir=user_data_dir,
                                       execute_path=execute_path)


    def load_driver(self, driver_url, mobile_device=None, driver_type="chrome", time_to_wait=20, user_data_dir=None,
                    execute_path=None):
        if driver_type == 'firefox':
            return self.load_firefox_driver(driver_url, time_to_wait)

        options = webdriver.ChromeOptions()
        if driver_type == "chrome_local":
            if user_data_dir is None:
                user_data_dir = 'C:\chrometemp\scraper'
            if execute_path is None or not Path(execute_path).exists():
                execute_path = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
                if not Path(execute_path).exists():
                    execute_path = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            if not Path(execute_path).exists():
                raise Exception("로컬 환경의 크롬실행파일이 설정하신 경로에 없습니다. 크롬파일 경로를 확인해주세요.")

            self.proc = subprocess.Popen(
                fr'{execute_path} --remote-debugging-port=9222 --user-data-dir="{user_data_dir}"')
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        else:
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

        options.add_argument("disable-gpu")

        if mobile_device:
            mobile_emulation = {"deviceName": mobile_device}
            options.add_experimental_option("mobileEmulation", mobile_emulation)
        if driver_url is None:
            if getattr(sys, 'frozen', False):
                driver_path = chromedriver_autoinstaller.install(cwd=True)
                driver = webdriver.Chrome(driver_path, options=options)
            else:
                chromedriver_autoinstaller.install()
                driver = webdriver.Chrome(options=options)
        else:
            driver = webdriver.Chrome(driver_url, options=options)
        driver.maximize_window()
        driver.set_page_load_timeout(time_to_wait)
        time.sleep(1)
        return driver

    @staticmethod
    def load_firefox_driver(driver_url, time_to_wait):
        options = webdriver.FirefoxOptions()
        options.add_argument("disable-gpu")

        if driver_url is None:
            if getattr(sys, 'frozen', False):
                driver_path = geckodriver_autoinstaller.install(cwd=True)
                driver = webdriver.Firefox(executable_path=driver_path, options=options)
            else:
                geckodriver_autoinstaller.install()
                driver = webdriver.Firefox(options=options)
        else:
            driver = webdriver.Firefox(executable_path=driver_url, options=options)
        driver.maximize_window()
        driver.set_page_load_timeout(time_to_wait)
        return driver

    def reload_driver(self, sleep_random_sec=0):
        self.quit()
        if sleep_random_sec > 0:
            self.sleep_random(sleep_random_sec, display=False)
        self.driver = self.load_driver(self.driver_url)

    def go(self, url, timeout=None):
        try:
            if timeout is not None:
                self.driver.set_page_load_timeout(timeout)
            self.driver.get(url)
        except Exception as e:
            self.logger.debug(ExceptionUtils.get_error_message(e))

    def wait(self, value, timeout=20, by=By.CSS_SELECTOR, parent=None):
        if parent is None:
            try:
                WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
            except Exception as e:
                self.logger.debug(ExceptionUtils.get_error_message(e))
        else:
            for _ in range(timeout):
                try:
                    if parent.find_element(by, value):
                        break
                    else:
                        time.sleep(1)
                except Exception as e:
                    self.logger.debug(ExceptionUtils.get_error_message(e))
                    time.sleep(1)

    def text(self, value=None, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        try:
            content = self.html(value, by, parent, waitable, timeout)
            return self.html2Text(content)
        except Exception as e:
            self.logger.debug(e)
            return ''

    def html(self, value=None, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        try:
            content = element.get_attribute('innerHTML')
            return content
        except Exception as e:
            self.logger.debug(e)
            return ''

    @staticmethod
    def html2Text(html):
        text = fromstring(html).text_content().strip()
        return text.strip()

    def integer(self, value, attr_name=None, by=By.CSS_SELECTOR,  parent=None, waitable=True, timeout=10):
        if attr_name is not None:
            content = self.attr(value, attr_name, by, parent, waitable, timeout)
        else:
            content = self.text(value, by, parent, waitable, timeout)
        if content is None or len(content) == 0:
            return None
        else:
            num = self.get_number(content)
            try:
                return int(num)
            except Exception as e:
                self.logger.debug(e)
                return None

    def float(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        content = self.text(value, by, parent, waitable, timeout)
        if len(content) == 0:
            return None
        else:
            num = self.get_number(content)
            try:
                return float(num)
            except Exception as e:
                self.logger.debug(e)
                return None

    def get_number(self, text):
        if text is None:
            return None
        value = self.NUMBER_FORMAT.search(text)
        if value is None:
            return None
        else:
            num = value.group()
            num = num.replace(",", "")
            return num

    def attr(self, value, attr_name, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        try:
            return element.get_attribute(attr_name)
        except Exception as e:
            self.logger.debug(e)
            return None

    def tag_name(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        try:
            return element.tag_name
        except Exception as e:
            self.logger.debug(e)
            return None

    def click(self, value=None, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        try:
            element.click()
        except Exception as e:
            self.logger.debug(e)
        time.sleep(1)

    def is_enabled(self, value=None, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        try:
            return element.is_enabled()
        except Exception as e:
            self.logger.debug(e)
        return False

    def enter(self, value, enter_value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        element.clear()
        element.send_keys(enter_value)

    def send_enter(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        element.send_keys(Keys.RETURN)

    def enter_clipboard(self, value, enter_value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        element.clear()
        element.click()
        pyperclip.copy(enter_value)
        element.send_keys(Keys.CONTROL, 'v')
        time.sleep(1)

    def exists(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        if self.size(value, by, parent, waitable, timeout) > 0:
            return True
        else:
            return False

    def elements(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        if parent is None:
            parent = self.driver
        if waitable:
            self.wait(value, timeout, by, parent)
        try:
            return parent.find_elements(by, value)
        except Exception as e:
            self.logger.debug(e)
            return []

    def element(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        if not isinstance(value, str):
            return value
        if parent is None:
            parent = self.driver
        if waitable:
            self.wait(value, timeout, by, parent)
        try:
            return parent.find_element(by, value)
        except Exception as e:
            self.logger.debug(e)
            return None

    def size(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        return len(self.elements(value, by, parent, waitable, timeout))

    def move_to_element(self, value, by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        element = self.element(value, by, parent, waitable, timeout)
        action = ActionChains(self.driver)
        action.move_to_element(element).perform()
        time.sleep(1)

    def current_url(self):
        return self.driver.current_url

    def execute_script(self, script):
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            self.logger.debug(e)
            return None

    def post_json(self, url, params):
        params_json = json.dumps(params)
        js = f'''var xhr = new XMLHttpRequest();
        xhr.open('POST', '{url}', false);
        xhr.setRequestHeader('Content-type', 'application/json');
        xhr.send('{params_json}');
        return xhr.response;'''
        return self.execute_script(js)

    def quit(self):
        try:
            if self.proc:
                self.proc.kill()
            self.driver.quit()
        except Exception as e:
            self.logger.debug(ExceptionUtils.get_error_message(e))

    # def __del__(self):
    #     self.quit()

    @staticmethod
    def random_sec(sec):
        """
        sec 초를 기준으로 랜덤한 시간을 구한다.
        :param sec:
        :return:
        """
        return random.randint(1, int(sec * 2000)) / 1000

    @staticmethod
    def bool_random(n=10):
        """
        True 일 확률을 1/n 번 나오게 한다.
        :param n: 몇 번 시도할 것인지
        :return:
        """
        v = random.randint(1, n)
        if v == n:
            return True
        return False

    def sleep_random(self, sec=10, display=True):
        """
        sec를 기준으로 랜덤한 시간만큼 멈춘다.
        :param sec:
        :param display:
        :return:
        """
        if sec > 0:
            random_sec = self.random_sec(sec)
            if random_sec > 60 * 5:
                self.quit()
                self.logger.info(f"Delay time: {DateUtils.seconds_to_hhmmss(random_sec)}")
                self.sleep_timer(random_sec, display=display)
                self.reload_driver()
            else:
                self.sleep_timer(random_sec, display=display)

    @staticmethod
    def sleep_timer(sec, renewal_sec=5, display=True):
        """
        기다리는 시간을 프로그래스바로 보여준다.
        :param sec: 기다릴 시간
        :param renewal_sec: 갱신 주기
        :param display:
        :return:
        """
        if display and sec > renewal_sec:
            start = time.time()
            with tqdm(total=int(sec), desc="sleeping...") as bar:
                while True:
                    taken_time = time.time() - start
                    if taken_time > sec:
                        bar.refresh()
                        break
                    if bar.n + 1 < taken_time:
                        bar.update(int(taken_time) - bar.n)
                    if taken_time + renewal_sec < sec:
                        time.sleep(renewal_sec)
        else:
            time.sleep(sec)

    def scroll_down(self, height=None):
        if height is None:
            height = "document.body.scrollHeight || document.documentElement.scrollHeight"
        self.execute_script(f"window.scrollTo(0, {height});")
        time.sleep(1)

    def scroll_up(self, height=None):
        if height is None:
            height = "-document.body.scrollHeight || -document.documentElement.scrollHeight"
        self.execute_script(f"window.scrollTo(0, {-height});")
        time.sleep(1)

    def scroll_to_end(self, value, by=By.CSS_SELECTOR, parent=None):
        bf_elements_size = 0
        for _ in range(10000):
            elements = self.elements(value, by, parent, waitable=False)
            if bf_elements_size == len(elements):
                break
            else:
                bf_elements_size = len(elements)
            last_element = elements[len(elements) - 1]
            self.move_to_element(last_element)

    def switch_to_frame(self, frame_selector):
        if self.exists(frame_selector):
            self.driver.switch_to.frame(self.element(frame_selector))

    def switch_to_default_content(self):
        self.driver.switch_to.default_content()

    def switch_tab(self, index):
        tab = self.driver.window_handles[index]
        self.driver.switch_to.window(tab)
        time.sleep(1)

    def close_popup(self, start_idx=1):
        tabs = self.driver.window_handles
        for i, tab in reversed(list(enumerate(tabs))):
            if i < start_idx:
                break
            self.driver.switch_to.window(tab)
            self.driver.close()
            time.sleep(1)

    def close_alert(self, timeout=5):
        for i in range(timeout):
            if EC.alert_is_present():
                self.driver.switch_to.alert.accept()
                break
            else:
                time.sleep(1)

    def title(self):
        return self.driver.title

    def page_source(self):
        return self.driver.page_source

    def enable_download_headless(self, download_dir):
        if isinstance(download_dir, str):
            download_dir = Path(download_dir)
        if not download_dir.exists():
            download_dir.mkdir(exist_ok=True, parents=True)
        self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': str(download_dir)}}
        self.driver.execute("send_command", params)

    def tries(self, fn_act, n=20, sleep_sec=0.5, raise_err=False, fn_err=None, **kwargs):
        for i in range(n):
            try:
                return fn_act(**kwargs)
            except Exception as e:
                self.logger.debug(f"{i + 1}th try. {e}")
                time.sleep(sleep_sec)
                if fn_err:
                    fn_err()
                if i == n - 1:
                    self.logger.error(f"{fn_act} Function : {i + 1}th try. {e}")
                    if raise_err:
                        raise e

    def has_class(self, value, cls="active", by=By.CSS_SELECTOR, parent=None, waitable=True, timeout=10):
        classes = self.attr(value, 'class', by, parent, waitable, timeout)
        return cls in classes.split()

    def get_current_url(self):
        return self.driver.current_url

    def value(self, css_selector, waitable=True):
        return self.attr(css_selector, "value", waitable=waitable)
