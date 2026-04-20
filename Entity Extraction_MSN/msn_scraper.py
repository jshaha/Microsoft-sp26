import selenium # pyright: ignore[reportMissingImports]
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
import time
import pandas as pd
from selenium.webdriver.edge.service import Service # type: ignore
from selenium.webdriver.edge.options import Options # type: ignore
from selenium.common.exceptions import TimeoutException # type: ignore
from tqdm import tqdm # type: ignore

service = Service(executable_path="E:/msedgedriver.exe")
options = Options()
options.add_argument("--headless")  # Run in headless mode (without opening a browser window)
driver = webdriver.Edge(service=service, options=options)
link_to_text = {}
try:
    driver.get("https://www.msn.com/en-us/money/")
    time.sleep(10)
    financefeed_entrypoint = driver.find_element(By.CSS_SELECTOR, "div.financeFeedsNews-DS-EntryPoint1-1")
    article_grid = financefeed_entrypoint.find_element(By.CSS_SELECTOR, 'div[data-template-key="10601"]')
    first_row = article_grid.find_element(By.CSS_SELECTOR, "div[style='grid-area: 1 / 1 / span 2 / span 2;']")
    carousel_slide = article_grid.find_element(By.CSS_SELECTOR, "div[class^='carousel_slides-DS-card1-']")
    carousel = carousel_slide.find_element(By.CSS_SELECTOR, "div[class^='carousel_tabPanels-DS-card1-']")
    carousel_articles = carousel.find_elements(By.CSS_SELECTOR, "a")
    article_links = []
    for article in carousel_articles:
        link = article.get_attribute("href")
        if link[12] == "m" and link[8] != "a" and len(link.split("/")) > 6: #type: ignore
            article_links.append(link)
    # print(article_links)
    for link in tqdm(article_links, desc="Processing articles"):
        try:
            driver.get(link)
            ## INDIV ARTICLE SCRAPING
            time.sleep(1)
            fluent_design_system_provider = driver.find_element(By.CSS_SELECTOR, "fluent-design-system-provider")
            entry_point_views = fluent_design_system_provider.find_element(By.CSS_SELECTOR, "entry-point-views")
            desktop_article_content = entry_point_views.find_element(By.CSS_SELECTOR, "desktop-article-content")
            cp_article = desktop_article_content.find_element(By.CSS_SELECTOR, "cp-article")
            continue_reading_div = cp_article.find_element(By.CSS_SELECTOR, "div.continue-reading-slot")
            cont_read_btn = continue_reading_div.find_element(By.CSS_SELECTOR, "fluent-button")
            wait = WebDriverWait(driver, 10)

            cont_read_btn = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="continue-reading-button"]'))
            )

            driver.execute_script("""
                arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});
            """, cont_read_btn)

            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="continue-reading-button"]')))
            cont_read_btn.click()
            cp_article_shadow = cp_article.shadow_root
            try:
                article_div_fool_key_points = WebDriverWait(cp_article_shadow, 10).until( # type: ignore
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.fool-key-points")))
            except TimeoutException:
                print("Timed out waiting for the element to load.")
            #article_ul = cp_article_shadow.find_element(By.CSS_SELECTOR, "ul")
            #print(article_ul.find_elements(By.CSS_SELECTOR, "li"))
            paragraphs = cp_article_shadow.find_elements(By.CSS_SELECTOR, "p")
            link_to_text[link] = ""
            for para in paragraphs:
                link_to_text[link] += para.text + "\n"
        except Exception as e:
            print(f"Error processing article {link}: {e}")
finally:
    driver.quit()

df = pd.DataFrame(list(link_to_text.items()), columns=["Link", "Text"])
df.to_csv("msn_finance_articles.csv", index=False)