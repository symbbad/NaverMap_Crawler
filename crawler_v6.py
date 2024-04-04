import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
import tkinter as tk
from tkinter import messagebox

import time
import re


class CrawlingStopped(Exception):
    pass

class UserSetting:
    def __init__(self):
        self.query_word = ''
        self.finish_page = None
        self.cat = []
        self.url = ''
        self.region_keyword = ''

    def set_query(self):
        region = str(input("지역명 입력: "))
        keyword = str(input("검색어 입력: "))\
        
        while True:
            cat_input = input("카테고리 단어를 입력해주세요 (입력을 완료하면 \"F\"를 입력해주세요, 입력을 원하지 않으면 \"N\"을 입력해주세요): ").strip()
            if cat_input.upper() == 'F':
                if self.cat:
                    print("입력한 카테고리를 확인하세요: ")
                    for cat_word in self.cat:
                        print(cat_word)
                    confrim = input("입력한 카테고리 단어들이 맞습니까? (Y/N)")
                    if confrim.upper() == "Y":
                        break
                    elif confrim.upper() == "N":
                        continue
                    else:
                        print("잘못된 입력입니다. Y와 N 중에 입력해주세요")
                        continue

            elif cat_input.upper() == "N":
                confrim_no_cat = input("입력한 단어가 없습니다. 그대로 진행합니까? (Y/N)")
                if confrim_no_cat.upper() == "Y":
                    break
                elif confrim_no_cat.upper() == "N":
                    continue
                else:
                    print("잘못된 입력입니다. Y와 N 중에 입력해주세요")
                    continue

            else:
                self.cat.append(cat_input)

        self.finish_page = int(input("끝나는 페이지 입력: "))
        self.query_word = f"{region} {keyword}"
        self.region_keyword = region
        self.url = f'https://map.naver.com/p/search/{self.query_word}'

    def get_query(self):
        return self.query_word

    def get_url(self):
        return self.url

    def get_finish_page(self):
        return self.finish_page

    def get_cat(self):
        return self.cat

    def get_region_keyword(self):
        return self.region_keyword


def search_iframe():
    driver.switch_to.default_content()
    driver.switch_to.frame("searchIframe")


def entry_iframe():
    driver.switch_to.default_content()
    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]')))

    for _ in range(5):
        time.sleep(.5)
        try:
            driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="entryIframe"]'))
            break
        except:
            pass


def chk_names():
    search_iframe()
    elem = driver.find_elements(By.XPATH, '//*[@id="_pcmap_list_scroll_container"]/ul/li/div[1]/div/a[1]/div/div/span[1]')
    name_list = [e.text for e in elem]
    return elem, name_list


def crawling_main(elem):
    global naver_res
    global cat_setting
    global region_keyword

    for e in elem:
        driver.execute_script("arguments[0].click();", e)
        entry_iframe()

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'LDgIH')))
        try:
            # 가게 이름, 카테고리, 주소
            try:
                real_name_list = [soup.select('span.Fc1rA')[0].text]
                category_list = [soup.select('span.DJJvD')[0].text]
                addr_list = [soup.select('span.LDgIH')[0].text]

                if len(cat_setting) == 0:
                    pass

                if not set(category_list).intersection(set(cat_setting)):
                    pass

                if region_keyword not in addr_list[0]:
                    return CrawlingStopped(Exception)

                print(f" ---- {real_name_list[0]} ---- ")
            except IndexError:
                print(" ** Error : 가게 이름, 카테고리 부분 ** ")
                category_list = ["Error"]
                real_name_list = ["Error"]
                addr_list = [float('nan')]

            # 네이버 리뷰 수 추출
            try:
                review_texts = soup.select('span.PXMot:not([class*="LXIwF"])')  # class에 LXIwF를 포함하지 않는 span.PXMot 선택
                review_numbers = []

                for review_text in review_texts:
                    numbers = ''.join(re.findall(r'\d+', review_text.text))
                    review_numbers.append(numbers)

                last_two_numbers = review_numbers[-2:]
                combined_numbers = sum(int(num) for num in last_two_numbers)
                review_list = [combined_numbers]
            except:
                print("> 리뷰 수 에러")
                review_list = [000000]


            # 스마트스토어 링크 찾기
            try:
                result_url = None
                s8peq_elements = driver.find_elements(By.CSS_SELECTOR, '.S8peq a')
                
                for element in s8peq_elements:
                    href = element.get_attribute('href')
                    text = element.text

                    if '스마트스토어' in text:
                        result_url = href
                        break

                    elif '모두' in text and not result_url:
                        result_url = href

                    elif '홈페이지' in text and not result_url:
                        result_url = href

            except NoSuchElementException:
                print("> 링크 X")
            except Exception as e:
                print("Error! (링크) 예상치 못한 오류가 발생했습니다: ", str(e))
                result_url = None

            try:
                exclude_keywords = ['kakao', 'blog', 'instagram']
                jO09N_element = driver.find_element(By.CSS_SELECTOR, 'div.jO09N')
                a_element = jO09N_element.find_element(By.TAG_NAME, 'a')
                href = a_element.get_attribute('href')

                if 'smartstore' in href:
                    result_url = href
                elif not any(keyword in href for keyword in exclude_keywords) and result_url is None:
                    result_url = href

                print("> 링크는 존재하지만 추출에 포함 X")
            except NoSuchElementException:
                print("> 링크 X")
            except Exception as e:
                print("Error! (링크_2) 예상치 못한 오류가 발생했습니다:", str(e))
                result_url = None


            # 전화번호
            pnum = "-"
            try:
                pnum_element = driver.find_element(By.CLASS_NAME, 'vV_z_')

                if pnum_element:
                    pnum_ele = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.xlx7Q')))
                    pnum = pnum_ele.get_attribute('innerText')
                else:
                    print("> 전화번호 X")
            except NoSuchElementException:
                print("> 전화번호 X")
            except TimeoutException:
                print("> 전화번호 X")
            except Exception as e:
                print(f"Error! (전화번호) 예상치 못한 오류가 발생했습니다:", str(e))



            #요일과 영업시간
            day_time_list = []
            day_of_week = ['월', '화', '수', '목', '금', '토', '일']                    
            try:
                if len(driver.find_elements(By.CLASS_NAME, 'UCWzd'))>0:
                    print("> 영업시간 X")
                    for day in day_of_week:
                        day_time_list.append((day, "-"))
                else:
                    try:
                        operation_time_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, 'gKP9i.RMgN0')))
                        operation_time_button.click()
                        WebDriverWait(driver, 4).until(EC.visibility_of_element_located((By.CLASS_NAME, 'H3ua4')))

                        day_elements = driver.find_elements(By.CSS_SELECTOR, 'span.i8cJw')
                        time_elements = driver.find_elements(By.CSS_SELECTOR, 'div.H3ua4')
                        
                        if not day_elements or not time_elements:
                            print("요일 또는 영업시간 X")

                        else:
                            for i in range(len(day_elements)):
                                time_text = time_elements[i].get_attribute('innerText')
                                match = re.search(r'\d{1,2}:\d{2} - \d{1,2}:\d{2}', time_text)
                                if match:
                                    operation_time = match.group()
                                    day_time_list.append((day_elements[i].get_attribute('innerText'), operation_time))
                                else:
                                    day_time_list.append((day_elements[i].get_attribute('innerText'), time_text))
                        
                        if len(day_elements) == 1 and day_elements[0].get_attribute('innerText') == '매일':
                            day_time_list = [(day, day_time_list[0][1]) for day in day_of_week]
                        else:
                            day_time_list = [(day, time) for day, time in day_time_list if day in day_of_week]
                            day_time_list = sorted(day_time_list, key=lambda x: day_of_week.index(x[0]))

                    except TimeoutException:
                        u7pyf_element = driver.find_element(By.CLASS_NAME, 'U7pYf')
                        if u7pyf_element:

                            u7pyf_text = u7pyf_element.get_attribute('innerText')
                            time_match = re.search(r'\d{1,2}:\d{2} - \d{1,2}:\d{2}', u7pyf_text)
                            if time_match:
                                operation_time = time_match.group()
                                for day in ['월', '화', '수', '목', '금', '토', '일']:
                                    day_time_list.append((day, operation_time))
                            else:
                                print("--- 영업시간 직접 확인 필요(u7pyf_element은 발견 안됨) ---")
                        else:
                            print("--- 영업시간 직접 확인 필요(u7pyf_element은 발견 안됨) ---")

            except NoSuchElementException:
                print("Error! (영업시간) 필요한 요소를 찾을 수 없습니다.")
            except ElementClickInterceptedException:
                print("Error! (영업시간) 요소를 클릭하는 중 문제가 발생했습니다.")
            except TimeoutException:
                print("Error! (영업시간) 요소를 찾는 데 시간이 너무 오래 걸립니다.")
            except Exception as e:
                print(f"Error! (영업시간) 예상치 못한 오류가 발생했습니다 :{e}")


            # 가게 URL 추출
            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app-root"]/div/div/div/div[2]/div[3]/div/span[3]'))).click()
                shop_url_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a._spi_input_copyurl._spi_copyurl_txt.spi_copyurl_url')))
                shop_url = shop_url_element.get_attribute('innerText')
                driver.back()
                
            except TimeoutException:
                print("Error! (URL) 요소를 찾는 데 시간이 너무 오래 걸립니다.")
                shop_url = ""
            except NoSuchElementException:
                print("Error! (URL) 필요한 요소를 찾을 수 없습니다.")
                shop_url = ""
            except Exception as e:
                print(f"Error! (URL) 예상치 못한 오류가 발생했습니다 :{e}")
                shop_url = ""


            # 데이터프레임에 추가
            naver_temp = pd.DataFrame({'카테고리': category_list,
                                        '상호명': real_name_list,
                                        '주소': addr_list,
                                        '네이버 리뷰 수': review_list,
                                        '전화번호' : pnum,
                                        '가게 URL': [shop_url],
                                        '외부링크' : [result_url],
                                        '월': [day_time_list[0][1] if len(day_time_list) > 0 and day_time_list[0][1] else ''],
                                        '화': [day_time_list[1][1] if len(day_time_list) > 1 and day_time_list[1][1] else ''],
                                        '수': [day_time_list[2][1] if len(day_time_list) > 2 and day_time_list[2][1] else ''],
                                        '목': [day_time_list[3][1] if len(day_time_list) > 3 and day_time_list[3][1] else ''],
                                        '금': [day_time_list[4][1] if len(day_time_list) > 4 and day_time_list[4][1] else ''],
                                        '토': [day_time_list[5][1] if len(day_time_list) > 5 and day_time_list[5][1] else ''],
                                        '일': [day_time_list[6][1] if len(day_time_list) > 6 and day_time_list[6][1] else '']})
            naver_res = pd.concat([naver_res, naver_temp], ignore_index=True)
                
                
        except Exception as e:
            if isinstance(e, CrawlingStopped):
                print("크롤러가 종료됩니다.")
            else:
                print(f"Error! (시작부) 예상치 못한 오류가 발생했습니다 :{e}")
                continue

        print(f'> 정상 크롤링 완료')
        search_iframe()


def save_file():
    title = str(input("파일 이름: "))

    try:
        naver_res.to_excel(f'./{title}.xlsx')
    except:
        print("파일 저장 실패")


def main(finish_page):
    global last_name

    page_num = 1

    while page_num <= finish_page:

        print(f"> {page_num} p. 페이지 시작 <")
        time.sleep(.5)

        search_iframe()
        elem, name_list = chk_names()

        #오토 스크롤
        if last_name == name_list[-1]:
            pass

        while 1:
            action.move_to_element(elem[-1]).perform()
            elem, name_list = chk_names()
            
            if last_name == name_list[-1]:
                break
            else:
                last_name = name_list[-1]

        try:
            crawling_main(elem=elem)
        except CrawlingStopped as e:
            print(e)
            break

        try:
            next_page_button = driver.find_element(By.XPATH, '//*[@id="app-root"]/div/div[2]/div[2]/a[7]')
            next_page_button.click()
            time.sleep(1.5)
        except:
            print("페이지를 찾을 수 없습니다.")
            break

        page_num += 1
    save_file()


if __name__ == '__main__':

    # 로딩 메시지 표시
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("잠시만 기다려주세요", "프로그램을 로딩하는 중입니다...")
    root.destroy()
    time.sleep(3)  # 로딩이 얼마나 걸리는지 모르니까 3초 기다림

    user_setting = UserSetting()
    user_setting.set_query()
    cat_setting = user_setting.get_cat()
    region_keyword = user_setting.get_region_keyword()

    naver_res = pd.DataFrame(columns=['카테고리', '상호명', '주소', '월', '화', '수', '목', '금', '토', '일', '네이버 리뷰 수', '전화번호', '가게 URL', '외부링크'])
    last_name = ''

    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=options)
    driver.get(user_setting.get_url())
    action = ActionChains(driver)

    main(finish_page=user_setting.get_finish_page())

    driver.quit()