# !wget https://chromedriver.storage.googleapis.com/87.0.4280.88/chromedriver_win32.zip
# !unzip chromedriver_win32.zip

# 카카오 id, 멜론 id 선택할 수 있도록
# 이미 들어있는 곡을 넣은 경우 예외처리
# 통합이 아니라 곡검색만 진행하도록 수정

# TitleBasedPlyGenerator를 통해 얻은 곡 리스트를 이용한다.

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm # or import tqdm
from selenium.webdriver.common.alert import Alert

class MelonPlyBuilder:
    def __init__(self):
        self.driver = webdriver.Chrome('./chromedriver.exe')
        self.driver.implicitly_wait(2)
        self.driver.get('https://www.melon.com/index.htm')
        self.login_status = False
        self.play_list_generated = False

    def login(self,uid,password):
        # 로그인창 접속
        home_login_xpath = '//*[@id="gnbLoginDiv"]/div/button/span'
        melon_login_xpath = '//*[@id="conts_section"]/div/div/div[3]/button/span'  # 홈에서 login버튼, 카카오 아이디/멜론 아이디 선택 창에서 멜론 id를 선택하는 경우
        self.driver.find_element_by_xpath(home_login_xpath).click()
        self.driver.find_element_by_xpath(melon_login_xpath).click()

        # 로그인
        self.driver.find_element_by_id('id').send_keys(uid)
        self.driver.find_element_by_id('pwd').send_keys(password)
        self.driver.find_element_by_xpath('//*[@id="btnLogin"]/span').click()

        self.login_status = True

    def logout(self):
        pass

    def wait_and_swith(self,total_pages, target_page):
        # 새로운 페이지 뜰때까지 대기
        WebDriverWait(driver = self.driver, timeout = 5).until(lambda x: len(x.window_handles) == total_pages)
        # 두번째 창으로 이동
        self.driver.switch_to.window(self.driver.window_handles[target_page])

    def switch_search_mode(self):
        # 곡 검색 모드로 전환
        pass

    def send_query(self,query, init = False):
        home_search_button = '//*[@id="gnb"]/fieldset/button[2]/span'
        search_button = '//*[@id="header_wrap"]/div[2]/fieldset/button[2]/span'

        # 이전 검색 결과 삭제
        self.driver.find_element_by_id('top_search').clear()
        # 새로운 query 전송
        self.driver.find_element_by_id('top_search').send_keys(query)
        # 검색
        self.driver.find_element_by_xpath(search_button if not init else home_search_button).click()

    def click_check_box(self):
        self.driver.find_element_by_xpath('//*[@id="frm_songList"]/div/table/tbody/tr/td[1]/div/input').click()

    def click_add_botton(self):
        self.driver.find_element_by_xpath('//*[@id="frm_songList"]/div/div/button[4]/span').click()

    def generate_new_playlist(self,title):
        # 플레이 리스트 생성 버튼 클릭
        self.driver.find_element_by_xpath('/html/body/div/div/div[2]/button/span').click()

        # 창 전환 대기 후 제목 입력
        self.wait_and_swith(total_pages=2, target_page=1)
        self.driver.find_element_by_id('plylstTitle').send_keys(title)
        # 확인 클릭
        self.driver.find_element_by_xpath('/html/body/div/div/div[2]/button[1]/span/span').click()
        self.play_list_generated = True

    def activate_and_select_playlist(self):
        # 버튼이 보이도록 wrapper에 접근하여 att 수정
        element = self.driver.find_element_by_xpath('//*[@id="plylstList"]/div/table/tbody/tr[1]/td[1]/div/span')
        self.driver.execute_script("arguments[0].setAttribute('style','display:block;')", element)

        # 버튼에 접근한 후 클릭
        self.driver.find_element_by_xpath('//*[@id="plylstList"]/div/table/tbody/tr[1]/td[1]/div/span/button').click()

    def catch_alert(self):
        try:
            alert = Alert(self.driver)
            alert.accept()
            return True
        except:
            return False

    def run(self, play_list):
        assert self.login_status
        title = play_list.pop(0)

        self.send_query('Welcome', init=True) # Home에서의 검색 버튼과 재검색시 검색 버튼의 xpath가 다르므로 아무거나 검색한 후 시작한다.

        self.play_list_generated = False
        for song_singer in tqdm(play_list):

            self.send_query(song_singer) # 노래 검색
            self.click_check_box() # 첫번째 체크박스 클릭
            self.click_add_botton() # 담기 버튼 클릭

            warning = self.catch_alert() # 곡이 없어 alert 발생하는 경우 True return

            if warning:
                continue
            self.wait_and_swith(total_pages = 2, target_page = 1) # 페이지 전환까지 대기

            if self.play_list_generated:
                self.activate_and_select_playlist() # 첫번째 플레이 리스트 버튼 활성화 후 클릭
            else:
                self.generate_new_playlist(title)

            # 창 전환 대기 후 곡담기 완료에 대한 확인 클릭
            self.wait_and_swith(total_pages=2, target_page=1)
            self.driver.find_element_by_xpath('/html/body/div/div/div[2]/button/span/span').click()

            # 새로운 검색을 위해 창 전환
            self.wait_and_swith(total_pages=1, target_page=0)

        print("DONE : )")

    def quit(self):
        self.driver.close()

if __name__ == '__main__':
    title, play_list = ['selfish Jeremy Zucker', 'Good Daze (Feat. Shanin Blake) Jazzinuf']
    ply_generator = MelonPlyBuilder()
    ply_generator.login()
    ply_generator.run(play_list)
    ply_generator.quit()