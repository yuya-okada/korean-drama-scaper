# coding=utf-8
import json
import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os

from bs4 import BeautifulSoup
import urllib, urllib.request, urllib.error
from retry import retry
import time

KOREAN_DRAMAS_TOP = "https://filmarks.com/list-drama/country/147"
DRAMA_DETAIL = "https://filmarks.com/dramas/{}/{}"

driver = webdriver.Remote(
    command_executor='http://selenium-hub:4444/wd/hub',
    desired_capabilities=DesiredCapabilities.CHROME)

@retry(ValueError,tries=10, delay=10)
def get_reviews(drama_series_id, drama_season_id, page=1):
    time.sleep(2)
    print("Get Reviews: page=", page)

    driver.get(DRAMA_DETAIL.format(drama_series_id, drama_season_id) + "?page={}".format(page))
    time.sleep(2.0)
    soup = BeautifulSoup(driver.page_source.encode('utf-8'), features="html.parser")
    reviews_container = soup.find(class_="p-main-area")
    review_elems = reviews_container.find_all(class_="p-mark__review")
    reviews = [review_elem.get_text() for review_elem in review_elems]

    next_elem = reviews_container.find(class_="c-pagination__next")

    if next_elem and "is-hidden" not in next_elem.get("class"):
        reviews.extend(get_reviews(drama_series_id, drama_season_id, page + 1))  # 次のページの内容を追加

    return reviews


def get_detail(drama_series_id, drama_season_id):
    print("Get Detail:", drama_series_id, drama_season_id)

    driver.get(DRAMA_DETAIL.format(drama_series_id, drama_season_id))
    time.sleep(1.0)
    soup = BeautifulSoup(driver.page_source.encode('utf-8'), features="html.parser")
    detail_body = soup.find(class_="p-content-detail__body")

    # print(driver.find_element_by_class_name())
    # Title
    title = detail_body.find(class_="p-content-detail__title").find("span", recursive=False).get_text()
    print("Title=", title)

    # Detail
    detail = None
    details = detail_body.find_all(class_="p-content-detail__synopsis-desc")

    if details and len(details):
        detail = details[-1].get_text()  # [0]は，「続きを読む」クリック前の短いもの
        print("Detail=", detail)

    # Thumbnail
    thumbnail = detail_body.find(class_="c-content__jacket").find("img").get("src")
    print("Thumbnail=", thumbnail)

    # Stars
    stars = detail_body.find(class_="c-rating__score").get_text()
    print("Starts=", stars)

    # Year
    title_elem = detail_body.find(class_="p-content-detail__title")
    if title_elem and title_elem.find("a"):
        year = title_elem.find("a").get_text()
        print("Year=", year)

    # Casts
    casts = None
    cast_elem = detail_body.find(class_="p-content-detail__people-list-casts")
    if cast_elem:
        cast_elements = cast_elem.find_all("a")
        casts = [cast_element.get_text() for cast_element in cast_elements]
        print("Casts=", casts)

    # Movies
    vod = detail_body.find(class_="p-content-detail-related-info-content__vod")

    amazon_prime = ""
    netflix = ""
    if vod:
        movie_elements = detail_body.find(class_="p-content-detail-related-info-content__vod").find_all("a")
        movies = [movie_element.get("href") for movie_element in movie_elements]
        for movie in movies:
            if "amazon" in movie:  # Amazon Prime
                amazon_prime = movie

            elif "netflix" in movie:  # Netflix
                netflix = movie

        print("Amazon Prime=", amazon_prime)
        print("Netflix=", netflix)

    # Reviews
    reviews = get_reviews(drama_series_id, drama_season_id)

    return {
        "title": title,
        "detail": detail,
        "thumbnail": thumbnail,
        "stars": stars,
        "year": year,
        "casts": casts,
        "amazon_prime": amazon_prime,
        "netflix": netflix,
        "reviews": reviews
    }


def get_page(url, page_number=0):
    old_url = url
    if page_number:
        url += "?page={}".format(page_number)



    print("Get Page:", url)
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html, features="html.parser")

    dramas = soup.find(class_="p-movies-grid").find_all(recursive=False)

    is_first = True
    for i, drama in enumerate(dramas):
        if is_first:  # 最初の要素は違うやつなので無視
            is_first = False
            continue

        filename = "{}.json".format(i)
        if page_number:
            filename = str(page_number) + "_" + filename

        if os.path.exists("./results/{}".format(filename)):
            continue

        drama_data = json.loads(drama.attrs["data-drama-season-clip"])
        drama_series_id = drama_data["drama_series_id"]
        drama_season_id = drama_data["drama_season_id"]

        drama_data = get_detail(drama_series_id, drama_season_id)

        with open("./results/{}".format(filename), mode="a") as f:
            f.write(json.dumps(drama_data, ensure_ascii=False))

    if not page_number:
        page_number+=1
    get_page(old_url, page_number + 1)

# 韓国のドラマ一覧
get_page(KOREAN_DRAMAS_TOP)

driver.close()
driver.quit()
