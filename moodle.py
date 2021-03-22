from selenium import webdriver
import time
from dotenv import load_dotenv
load_dotenv()
import os
from calendar import month_name
import re
import dateutil.parser as dparser
import datetime

class MoodleScraper:
    def __init__(self):
        # Initialize the driver
        self.driver = webdriver.Chrome('./chromedriver')
        self.username = os.getenv("USERNAME")
        self.password = os.getenv("PASSWORD")

    def auth(self):
        self.driver.get("https://moodle.haverford.edu/my/")
        auth_button = self.driver.find_element_by_xpath("/html/body/div/div/div/div/div/ul/li[2]/div/div/div/a")
        auth_button.click()

        username_field = self.driver.find_element_by_xpath("/html/body/div/div/div/div[2]/form/div/div[1]/div[2]/input")
        password_field = self.driver.find_element_by_xpath("/html/body/div/div/div/div[2]/form/div/div[2]/div[2]/input")
        submit_button = self.driver.find_element_by_xpath("/html/body/div/div/div/div[2]/form/div/div[3]/button")

        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        submit_button.click()

        # time.sleep(5)

        # cancle_button = self.driver.find_element_by_xpath("/html/body/div/div/div[4]/div/div/div/button")
        # remember_me_button = self.driver.find_element_by_xpath("/html/body/div/div/div[1]/div/form/div[2]/div/label/span")

        # cancle_button.click()
        # remember_me_button.click()

    def get_classes(self):
        while self.driver.current_url != 'https://moodle.haverford.edu/my/':
            time.sleep(1)
        if self.driver.current_url == 'https://moodle.haverford.edu/my/':
            time.sleep(3)
            
            class_names = self.driver.find_elements_by_xpath('/html/body/div[3]/div[3]/div/div/section[1]/div/aside/section[3]/div/div/div[1]/div[2]/div/div/div[1]/div/div/*/div[1]/div/div[1]/a/span[3]')
            class_urls = self.driver.find_elements_by_xpath('/html/body/div[3]/div[3]/div/div/section[1]/div/aside/section[3]/div/div/div[1]/div[2]/div/div/div[1]/div/div/*/div[1]/div/div[1]/a')
            
            class_name_list =[]
            class_url_list = []

            for item in class_names:
                split_string = item.text.split("-", 1)
                class_name_list.append(split_string[0].strip())

            for item in class_urls:
                class_url_list.append(item.get_attribute('href'))

            self.class_info = zip(class_name_list, class_url_list)

    def get_class_homework(self):
        class_functions = {'CNSEH': self.course_chinese, 'MATHH': self.course_math, 'WRPRH': self.course_writing}
        for cur_class in self.class_info:
            class_name, class_url = cur_class

            num_start = None
            for index, letter in enumerate(class_name):
                if letter.isdigit():
                    num_start = index
                    break

            class_type = class_name[:index]

            print(class_functions[class_type](cur_class))

    def phrase_checker(self, phrase_list, to_check):
        for phrase in phrase_list:
            if phrase in to_check:
                return True
        return False

    def course_chinese(self, class_info):
        class_name, class_url = class_info
        self.driver.get(class_url)

        due_names = self.driver.find_elements_by_xpath('//*[contains(@class, "activity") and contains(@class, "assign") and contains(@class, "modtype_assign")]//div[1]/a/span')
        due_dates = self.driver.find_elements_by_xpath('//*[contains(@class, "activity") and contains(@class, "assign") and contains(@class, "modtype_assign")]//span[1]/a')
        
        due_names_list = []
        due_dates_list = []

        for date in due_names:
            due_names_list.append(date.text)

        for date in due_dates:
            due_dates_list.append(date.text)

        return zip(due_names_list, due_dates_list)

    def course_math(self, class_info):
        class_name, class_url = class_info
        self.driver.get(class_url)
        time.sleep(2)

        due_bullets = self.driver.find_elements_by_xpath('/html/body/div[4]/div[3]/div/div/section[1]/div/div/ul//ul//ul/li')

        due_names_list = []
        due_dates_list = []

        for bullet in due_bullets:
            if self.phrase_checker(['due', 'problem set'], bullet.text.lower()):
                try:
                    due_date = dparser.parse(bullet.text.lower(), fuzzy=True)
                    due_date = due_date.replace(year=datetime.datetime.now().year)
                    due_name = bullet.text

                    due_names_list.append(due_name)
                    due_dates_list.append(due_date.strftime("%d/%m/%Y %H:%M:%S"))
                except:
                    print("failed date with: "+bullet.text)

        return zip(due_names_list, due_dates_list)

    def course_writing(self, class_info):
        class_name, class_url = class_info
        self.driver.get(class_url)
        due_dates = self.driver.find_elements_by_xpath("//*[contains(text(), '(')]")

        months = {m.lower() for m in month_name[1:]}

        class_homework = []
        for date in due_dates:
            for word in date.text.split():
                word = re.sub(r'[^\w]', '', word)
                if word.lower() in months:
                    class_homework.append(date.text)
        
        due_names_list = []
        due_dates_list = []

        for work in class_homework:
            split = work.split('(')
            new_split = split[1].split(')')
            due_names_list.append(split[0].rstrip())
            due_dates_list.append(new_split[0])
            
        return zip(due_names_list, due_dates_list)


if __name__ == "__main__":
    test = MoodleScraper()
    test.auth()
    test.get_classes()
    test.get_class_homework()