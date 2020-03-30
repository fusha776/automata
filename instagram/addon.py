from time import sleep
from selenium.common.exceptions import NoSuchElementException
from appium.webdriver.extensions.android.nativekey import AndroidKey
from selenium.webdriver.common.by import By


class DriverEx():
    '''WebDriver の役割を一部改造するクラス
    '''
    msg_no_such_btn = 'An element could not be located on the page using the given search parameters.'

    def find_element_continually(self, by, id_, sec=30):
        '''sec 秒 を上限として、指定した要素が見つかるまで探し続ける
        '''
        sec = int(sec)
        for i in range(0, sec):
            el = self.driver.find_elements(by, id_)
            if el:
                return el[0]
            sleep(1)
        raise NoSuchElementException(self.msg_no_such_btn)

    def find_elements_continually(self, by, id_, sec=30):
        '''sec 秒 を上限として、指定した要素が見つかるまで探し続ける
        '''
        sec = int(sec)
        for i in range(0, sec):
            el = self.driver.find_elements(by, id_)
            if el:
                return el
            sleep(1)
        return None

    def find_elements_by_text_continually(self, text, sec=30):
        '''sec 秒 を上限として、指定した要素が見つかるまで探し続ける
        '''
        sec = int(sec)
        for i in range(0, sec):
            el = self.driver.find_elements(By.XPATH, f'//android.widget.TextView[@text="{text}"]')
            if el:
                return el
            sleep(1)
        return None

    def wait(self):
        '''画面がloadされるまで待つ。
        一定時間経ってもloadが完了しなかったらFalseを返す。
        '''
        for i in range(0, 30):
            has_loaded = self.driver.find_element_by_class_name('android.widget.FrameLayout')
            if has_loaded:
                return True
            sleep(1)
        return False

    def save_photo(self, fpath, output_fname=None):
        if output_fname is None:
            output_fname = fpath.split("\\")[-1]
        self.driver.push_file(f'{self.camera_storage}/{output_fname}',
                              source_path=fpath)
        self.reboot_instagram

    def switch_to_android_home(self):
        # self.driver.press_keycode(AndroidKey.HOME)
        self.driver.keyevent(AndroidKey.HOME)
