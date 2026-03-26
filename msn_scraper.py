import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

service = Service(executable_path="E:/msedgedriver.exe")
options = Options()
# options.add_argument("--headless")  # Run in headless mode (without opening a browser window)
driver = webdriver.Edge(service=service, options=options)
try:
    driver.get("https://www.msn.com/en-us/money/savingandinvesting/nvidia-s-ceo-just-delivered-fantastic-news-for-investors-in-this-beaten-down-ai-stock/ar-AA1Zi5OT?ocid=finance-verthp-feeds&cvid=69c35bcf08fe40fda0377170a4ecdc50&ei=29")
    time.sleep(10)
    fluent_design_system_provider = driver.find_element(By.CSS_SELECTOR, "fluent-design-system-provider")
    entry_point_views = fluent_design_system_provider.find_element(By.CSS_SELECTOR, "entry-point-views")
    desktop_article_content = entry_point_views.find_element(By.CSS_SELECTOR, "desktop-article-content")
    cp_article = desktop_article_content.find_element(By.CSS_SELECTOR, "cp-article")
    cp_article_shadow = cp_article.shadow_root
    try:
        article_div_fool_key_points = WebDriverWait(cp_article_shadow, 10).until( # type: ignore
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.fool-key-points")))
    except selenium.common.exceptions.TimeoutException:
        print("Timed out waiting for the element to load.")
    #article_ul = cp_article_shadow.find_element(By.CSS_SELECTOR, "ul")
    #print(article_ul.find_elements(By.CSS_SELECTOR, "li"))
    paragraphs = cp_article_shadow.find_elements(By.CSS_SELECTOR, "p")
    for para in paragraphs:
        print(para.text)
finally:
    driver.quit()
time.sleep(15)