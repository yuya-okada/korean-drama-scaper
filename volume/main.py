# coding=utf-8
import json
import time
from selenium import webdriver
from bs4 import BeautifulSoup
import urllib, urllib.request, urllib.error

KOREAN_DRAMAS_TOP = "https://filmarks.com/list-drama/country/147"
DRAMA_DETAIL = "https://filmarks.com/dramas/{}/{}"


def get_reviews(soup, page=1):
    reviews_container = soup.find(class_="p-main-area")
    review_elems = reviews_container.find_all(class_="p-mark__review")
    reviews = [review_elem.get_text() for review_elem in review_elems]

    if "is-hidden" not in reviews_container.find(class_="c-pagination__next").class_:
        reviews.extend(get_reviews(soup, page + 1))  # 次のページの内容を追加

    return reviews


def get_detail(drama_series_id, drama_season_id):
    html = urllib.request.urlopen(DRAMA_DETAIL.format(drama_series_id, drama_season_id))
    soup = BeautifulSoup(html)
    time.sleep(0.5)
    detail_body = soup.find("p-content-detail__body")

    # Title
    title = detail_body.find(class_="p-content-detail__title").find("span", recursive=False).get_text()

    # Detail
    details = detail_body.find_all(class_="p-content-detail__synopsis-desc")
    detail = details[1].get_text()  # [0]は，「続きを読む」クリック前の短いもの

    # Thumbnail
    thumbnail = detail_body.find(class_="c-content__jacket").find("img").src

    # Stars
    stars = detail_body.find("c-rating__score").get_text()

    # Year
    year = detail_body.find(class_="p-content-detail__title").find("a").get_text()

    # Casts
    cast_elems = detail_body.find_all(class_="p-content-detail__people-list-casts").find("a")
    casts = [cast_elem.get_text() for cast_elem in cast_elems]

    # Movies
    amazon_prime = ""
    netflix = ""
    movie_elems = detail_body.find_all(class_="p-content-detail-related-info-content__vod").find("a")
    movies = [movie_elem.href for movie_elem in movie_elems]
    for movie in movies:
        if "amazon" in movie:  # Amazon Prime
            amazon_prime = movie

        elif "netflix" in movie:  # Netflix
            netflix = movie

    # Reviews
    reviews = get_reviews(soup)

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


def get_page(url):
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html)

    dramas = soup.find(class_="p-movies-grid").find_all(recursive=False)

    is_first = True
    result = []
    for drama in dramas:
        if is_first:  # 最初の要素は違うやつなので無視
            is_first = False
            continue

        drama_data = json.loads(drama.attrs["data-drama-season-clip"])
        drama_series_id = drama_data["drama_series_id"]
        drama_season_id = drama_data["drama_season_id"]

        drama_data = get_detail(drama_series_id, drama_season_id)

        result.append(drama_data)
        break

    return result

# 韓国のドラマ一覧
print(get_page(KOREAN_DRAMAS_TOP))
