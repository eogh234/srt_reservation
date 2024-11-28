# -*- coding: utf-8 -*-
import time
import requests
from random import randint
from datetime import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, WebDriverException, NoSuchElementException, UnexpectedAlertPresentException, TimeoutException, NoAlertPresentException

from exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from validation import station_list

class KTX:
    def __init__(self, dpt_stn, arr_stn, dpt_dt, dpt_tm, num_trains_to_check=2, want_reserve=False, webhook_url=""):
        """
        :param dpt_stn: SRT 출발역
        :param arr_stn: SRT 도착역
        :param dpt_dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
        :param dpt_tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
        :param num_trains_to_check: 검색 결과 중 예약 가능 여부 확인할 기차의 수 ex) 2일 경우 상위 2개 확인
        :param want_reserve: 예약 대기가 가능할 경우 선택 여부
        """
        self.login_id = None
        self.login_psw = None

        self.dpt_stn = dpt_stn
        self.arr_stn = arr_stn
        self.dpt_dt = dpt_dt
        self.dpt_tm = dpt_tm

        self.num_trains_to_check = num_trains_to_check
        self.want_reserve = want_reserve
        self.driver = None

        self.is_booked = False  # 예약 완료 되었는지 확인용
        self.cnt_refresh = 0  # 새로고침 회수 기록

        self.webhook_url = webhook_url

        self.check_input()

    def send_message(self, msg):
        """디스코드 메세지 전송"""
        now = datetime.now()
        message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
        requests.post(self.webhook_url, data=message)
        print(message)

    def check_input(self):
        if self.dpt_stn not in station_list:
            raise InvalidStationNameError(f"⚠️출발역 오류. '{self.dpt_stn}' 은/는 목록에 없습니다.")
        if self.arr_stn not in station_list:
            raise InvalidStationNameError(f"⚠️도착역 오류. '{self.arr_stn}' 은/는 목록에 없습니다.")
        if not str(self.dpt_dt).isnumeric():
            raise InvalidDateFormatError("⚠️날짜는 숫자로만 이루어져야 합니다.")
        try:
            datetime.strptime(str(self.dpt_dt), '%Y%m%d')
        except ValueError:
            raise InvalidDateError("⚠️날짜가 잘못 되었습니다. YYYYMMDD 형식으로 입력해주세요.")

    def set_log_info(self, login_id, login_psw):
        self.login_id = login_id
        self.login_psw = login_psw

    def run_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-cache")
            self.driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))
            self.driver.delete_all_cookies()
        except WebDriverException:
            print("WebDriverException invoked!")
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    def login(self):
        """Log in to the Korail website."""
        for i in range(10):
            try:
                self.driver.get('https://www.letskorail.com/korail/com/login.do')
                self.driver.implicitly_wait(15)
                self.driver.find_element(By.ID, 'txtMember').send_keys(str(self.login_id))
                self.driver.find_element(By.ID, 'txtPwd').send_keys(str(self.login_psw))
                self.driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div/div[1]/div[2]/div[1]/div[1]/form[1]/fieldset/div[1]/ul/li[3]/a/img').click()
                self.driver.implicitly_wait(5)
                break
            except Exception as e:
                self.send_message(f"[에러발생] 로그인 재시도..{i+1}회")
                self.driver.implicitly_wait(5)
                time.sleep(5)
        return self.driver

    def go_search(self):
        # 기차 조회 페이지로 이동
        self.driver.get('https://www.letskorail.com/ebizprd/EbizPrdTicketpr21100W_pr21110.do')
        self.driver.implicitly_wait(5)

        # 출발지 입력
        elm_dpt_stn = self.driver.find_element(By.ID, 'start')
        elm_dpt_stn.clear()
        elm_dpt_stn.send_keys(self.dpt_stn)

        # 도착지 입력
        elm_arr_stn = self.driver.find_element(By.ID, 'get')
        elm_arr_stn.clear()
        elm_arr_stn.send_keys(self.arr_stn)

        t_date = str(self.dpt_dt)
        year = t_date[:4]
        month = t_date[4:6]
        day = t_date[6:]

        # 출발 날짜 입력
        elm_dpt_year = self.driver.find_element(By.ID, "s_year")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_year)
        Select(self.driver.find_element(By.ID, "s_year")).select_by_value(year)

        elm_dpt_month = self.driver.find_element(By.ID, "s_month")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_month)
        Select(self.driver.find_element(By.ID, "s_month")).select_by_value(month)

        elm_dpt_day = self.driver.find_element(By.ID, "s_day")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_day)
        Select(self.driver.find_element(By.ID, "s_day")).select_by_value(day)

        # 출발 시간 입력
        elm_dpt_tm = self.driver.find_element(By.ID, "s_hour")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_tm)
        Select(self.driver.find_element(By.ID, "s_hour")).select_by_value(self.dpt_tm)

        print("기차를 조회합니다")
        print(f"출발역:{self.dpt_stn} , 도착역:{self.arr_stn}\n날짜:{self.dpt_dt}, 시간: {self.dpt_tm}시 이후\n{self.num_trains_to_check}개의 기차 중 예약")
        print(f"예약 대기 사용: {self.want_reserve}")
        # self.send_message("====SRT 조회 시작====")
        # self.send_message("🚅🚃🚃🚃🚃🚃🚃🚃")

        self.driver.find_element(By.XPATH, "//img[@alt='조회하기']").click()
        self.driver.implicitly_wait(30)
        time.sleep(1)

    def book_ticket(self, standard_seat, i):
        # standard_seat는 일반석 검색 결과 텍스트
        
        if "매진" not in standard_seat:
            # info_a = self.driver.find_element(By.CSS_SELECTOR,
            #                              f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(3)").text.replace("\n", " ")
            # info_b = self.driver.find_element(By.CSS_SELECTOR,
            #                              f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(4)").text.replace("\n", " ")
            # info_c = self.driver.find_element(By.CSS_SELECTOR,
            #                              f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(5)").text.replace("\n", " ")
            # print(info_a)
            # print(info_b)
            # print(info_c)
            # self.send_message(info_a)
            # self.send_message(info_b)
            # self.send_message(info_c)
            # try:
            #     WebDriverWait(self.driver, 3).until(EC.alert_is_present(), "Check Alert Popup..")
            #     self.driver.switch_to.alert.accept()
            # except TimeoutException as err:
            #     print(err)
            #     print("팝업이 발생하지 않았습니다.")
            #     self.send_message("팝업이 발생하지 않았습니다.")
            # # Error handling in case that click does not work
            try:
                self.driver.find_element(By.CSS_SELECTOR,
                                         f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(6) > a:nth-child(1) > img").click()
            except ElementClickInterceptedException as err:
                print(err)
                self.driver.find_element(By.CSS_SELECTOR,
                                         f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(6) > a:nth-child(1) > img").send_keys(
                    Keys.ENTER)
            except NoSuchElementException as err:
                print(err)
                self.driver.back()
            except UnexpectedAlertPresentException as err:
                print(err)
                self.send_message("⚠️팝업 발생 에러!")
                try:
                    self.driver.switch_to.alert.accept()
                except Exception as error:
                    print(error)
                    self.driver.switch_to.alert.send_keys(Keys.ENTER)
            finally:
                self.driver.implicitly_wait(2)

            # try:
            #     WebDriverWait(self.driver, 1).until(EC.alert_is_present(), "Check Alert Popup..")
            #     self.driver.switch_to.alert.accept()
            # except TimeoutException as err:
            #     print(err)
            #     print("팝업이 발생하지 않았습니다.")
            #     self.send_message("팝업이 발생하지 않았습니다.")
            # 예약이 성공하면
            print("예약 가능 클릭🫵")
            self.send_message("예약 가능 클릭🫵")
            try:
                if self.driver.find_elements(By.ID, 'isFalseGotoMain'):
                    self.is_booked = True
                    print("예약 성공🎉")
                    self.send_message("예약 성공🎉")
                    self.printInfo()

                    return self.driver
                else:
                    print("잔여석 없음. 다시 검색")
                    self.send_message("잔여석 없음. 다시 검색")
                    self.driver.implicitly_wait(5)
            except UnexpectedAlertPresentException as err:
                print(err)
                self.send_message("팝업 발생 에러!")
                try:
                    self.driver.switch_to.alert.accept()
                except NoAlertPresentException as error:
                    print(error)
            except NoSuchElementException as err:
                print(err)
                self.driver.back()

    def refresh_result(self):
        isSent = False
        submit = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[3]/div/div[1]/form[1]/div/div[3]/p/a/img")
        self.driver.execute_script("arguments[0].click();", submit)
        self.cnt_refresh += 1
        print(f"새로고침 {self.cnt_refresh}회")
        if self.cnt_refresh <= 5 and not isSent:
            self.send_message(f"새로고침 {self.cnt_refresh}회")
        if self.cnt_refresh == 8 and not isSent:
            self.send_message("100회마다 알려드립니다💤")
        if self.cnt_refresh % 100 == 0 and not isSent:
            self.send_message(f"새로고침 {self.cnt_refresh}회")
        if self.cnt_refresh % 1000 == 0 and not isSent:
            self.send_message("안돼에~😭")
        isSent = True
        self.driver.implicitly_wait(10)
        time.sleep(0.5)

    def reserve_ticket(self, reservation, i):
        if "신청하기" in reservation:
            try:
                self.driver.find_element(By.CSS_SELECTOR,
                                        f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(10) > a > img").click()
                print("예약 대기 완료🎉")
                self.send_message("예약 대기 완료🎉")
                self.is_booked = True

                self.printInfo()
                return self.is_booked
            except Exception as e:
                print(e)
                self.send_message("⚠️에러발생..예약하기를 다시 입력해주세요")

    def check_result(self):
        retry_count = 0
        while True:
            # try:
            #     self.driver.implicitly_wait(1)
            #     self.driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
            # except NoSuchElementException as err:
            #     print(err)
            #     self.driver.back()
            for i in range(1, 1 + self.num_trains_to_check * 2, 2):
                print(f"i = {i}")
                try:
                    # 일반석 예약하기
                    standard_seat = self.driver.find_elements("css selector", f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(6) > a:nth-child(1) > img")
                    if not standard_seat:
                        standard_seat = self.driver.find_elements("css selector", f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(6) > img")
                    standard_seat = standard_seat[0].get_attribute('alt')
                    # 예약대기
                    reservation = self.driver.find_elements("css selector", f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(10) > a > img")
                    if not reservation:
                        reservation = self.driver.find_elements("css selector", f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(10) > img")
                    reservation = reservation[0].get_attribute('alt')
                    print(f"STD: {standard_seat} RESERVE: {reservation}")
                except StaleElementReferenceException:
                    standard_seat = "좌석매진"
                    reservation = "좌석매진"
                except NoSuchElementException:
                    for _ in range(5):
                        standard_seat = self.driver.find_elements("css selector", f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(6) > a:nth-child(1) > img")
                        if standard_seat:
                            standard_seat = standard_seat[0].get_attribute('alt')
                        reservation = self.driver.find_elements("css selector", f"#tableResult > tbody > tr:nth-child({i}) > td:nth-child(10) > a > img")
                        if reservation:
                            reservation = reservation[0].get_attribute('alt')
                    print("No Such Element")
                    self.driver.back()
                except UnexpectedAlertPresentException as err:
                    print(err)
                    self.send_message("⚠️팝업 발생 에러")
                    try:
                        self.driver.switch_to.alert.accept()
                    except NoAlertPresentException as error:
                        print(error)
                except WebDriverException as err:
                        print(err)
                        self.driver.back()
                if self.book_ticket(standard_seat, i):
                    return self.driver

                if self.want_reserve:
                    self.reserve_ticket(reservation, i)

            if self.is_booked:
                return self.driver

            else:
                time.sleep(randint(2, 4))
                self.refresh_result()

    def run(self, login_id, login_psw):
        self.printInfo()
        self.run_driver()
        self.set_log_info(login_id, login_psw)
        self.login()
        self.go_search()
        self.check_result()

    def printInfo(self):
        print("====INFO====")
        print(f"🚉출발역: {self.dpt_stn}")
        print(f"🚉도착역: {self.arr_stn}")
        print(f"📆출발 일자: {self.dpt_dt}")
        print(f"⏰출발 시간: {self.dpt_tm}")

        print(f"🚅체크할 열차 수: {self.num_trains_to_check}")
        print(f"😙예약 대기 여부: {self.want_reserve}")
        
        self.send_message(f"\n====INFO====\n🚉출발역: {self.dpt_stn}\n🚉도착역: {self.arr_stn}\n📆출발 일자: {self.dpt_dt}\n⏰출발 시간: {self.dpt_tm}\n🚅체크할 열차 수: {self.num_trains_to_check}\n😙예약 대기 여부: {self.want_reserve}\n")