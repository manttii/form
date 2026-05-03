import scraper
import json

url = "https://docs.google.com/forms/d/e/1FAIpQLSfU5JphkKSSvlTjVmzVuYHDkdAsSYQorDvXsgaQGqAWUlct0A/viewform"
res = scraper.scrape_form(url)
print(json.dumps(res, indent=2))
