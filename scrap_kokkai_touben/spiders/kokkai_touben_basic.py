import scrapy
from scrapy.http.response import Response
from scrap_kokkai_touben.items import ScrapKokkaiToubenItem
from w3lib.html import remove_tags

import scrapy


class KokkaiToubenBasicSpider(scrapy.Spider):
    name = "kokkai_touben_basic"
    allowed_domains = ["www.shugiin.go.jp"]

    def start_requests(self):
        self.letter = "a"
        self.big_number = 1
        self.small_number = 1
        self.error_count = 0
        self.base_path = "itdb_shitsumona.nsf"
        yield scrapy.Request(self.construct_url(), callback=self.parse, errback=self.handle_error)

    def construct_url(self):
        return f"https://www.shugiin.go.jp/Internet/{self.base_path}/html/shitsumon/{self.letter}{self.big_number:03d}{self.small_number:03d}.htm"

    def parse(self, response):
        self.log(f"Successfully scraped {response.url}")

        # スクレイピングのロジックをここに実装
        title_html = response.xpath("/html/body/div[2]/p")
        if len(title_html) != 0:
            title = remove_tags(title_html.extract_first()).strip()

            content = [selector.get() for selector in response.xpath("/html/body/div[2]/text()") if selector.get().strip()]
            content_str = "".join(content)

            # items に定義した Post のオブジェクトを生成して次の処理へ渡す
            yield ScrapKokkaiToubenItem(id=f"{self.letter}{self.big_number:03d}{self.small_number:03d}", title=title, content=content_str)

        # URLの次の部分を準備
        if self.letter == "b":
            self.letter = "a"
            self.small_number += 1
        else:
            self.letter = "b"

        self.error_count = 0
        yield scrapy.Request(self.construct_url(), callback=self.parse, errback=self.handle_error)

    def handle_error(self, failure):
        print(f"Error occurred: {failure.value}")
        self.error_count += 1
        if self.error_count >= 5:
            self.log("5 consecutive errors occurred. Stopping the spider.", level=scrapy.log.ERROR)
            return

        if self.letter == "b":
            self.letter = "a"
            self.small_number += 1

        elif self.small_number != 1 and self.letter == "a":
            self.big_number += 1
            self.small_number = 1

        elif self.small_number == 1:
            self.big_number += 1

        if self.big_number >= 148:
            self.base_path = "itdb_shitsumon.nsf"

        yield scrapy.Request(self.construct_url(), callback=self.parse, errback=self.handle_error)
