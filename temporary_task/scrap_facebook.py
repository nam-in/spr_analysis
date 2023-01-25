import random
import re

import pandas as pd

from scraper.scraper_config import ScraperConfig
from utils.data_utils import DataUtils
from utils.date_utils import DateUtils
from utils.scrap_utils import ScrapUtils

# %%
cfg = ScraperConfig()
scrap = ScrapUtils()
# %%
links_df = DataUtils.read(cfg.data_dir / 'account_links.xlsx')
# %% Facebook
facebook_url = links_df.loc[0, 'Link']
# %%
scrap.go(facebook_url)
# %%
def get_creation_time_kst(ele):
    time_element = scrap.element("span.x4k7w5x a.x1i10hfl", parent=ele, waitable=False)
    if not time_element:
        raise Exception('Not Exists Time Element')

    scrap.move_to_element(time_element)
    ts = scrap.text("div.xu96u03", waitable=False)
    if ts == '':
        y_offset = scrap.execute_script("return window.pageYOffset")
        rand = random.randint(-100, 100)
        scrap.scroll_down(y_offset + rand)
        raise Exception('Failed to get date and time.')
    return to_date(ts)


def to_date(date_str):
    date_str = DataUtils.replace_tuples(date_str, (("오전", "AM"), ("오후", "PM")))
    date_str = re.sub(".요일 ", "", date_str)
    return DateUtils.str_to_time(date_str, '%Y년 %m월 %d일 %p %I:%M')


def scrap_row(ele, data_df):
    permalink = scrap.attr("span.x4k7w5x > a.x1i10hfl", 'href', parent=ele, waitable=False)
    if 'permalink' in data_df.columns and permalink in data_df['permalink']:
        return None

    scrap.move_to_element(ele)
    ts = scrap.tries(get_creation_time_kst, n=5, ele=ele)
    message = scrap.text("div[data-ad-preview='message']", parent=ele, waitable=False)
    likes = scrap.integer("div.x1n2onr6 div.x6s0dn4 span.xrbpyxo", parent=ele, waitable=False)
    comments = scrap.integer("div.x1n2onr6 > div.x6s0dn4 div.x9f619 div[aria-expanded] span.x193iq5w", parent=ele,
                             waitable=False)
    if comments:
        shares = scrap.integer(
            "div.x1n2onr6 > div.x6s0dn4 > div.x9f619 > div.x9f619:nth-of-type(2) span.x4k7w5x span.x193iq5w",
            parent=ele, waitable=False)
    else:
        shares = scrap.integer("div.x1n2onr6 > div.x6s0dn4 > div.x9f619 > div.x9f619 > span.x4k7w5x span.x193iq5w",
                               parent=ele, waitable=False)
    return dict(created_time_kst=ts, message=message, post_likes=likes, post_comments=comments, post_shares=shares,
                permalink=permalink)


def greater_than_start_date(start_time, created_time):
    start_time = DateUtils.str_to_time(start_time, '%Y-%m-%d %H:%M')
    return start_time <= created_time


def scrap_data(start_time, max_tries=5):
    data_df = pd.DataFrame()

    ended = False
    row = None
    fails = 0
    while True:
        try:
            all_elements = scrap.elements("div.x19h7ccj div[role='main'] > div.xh8yej3 > div.x1yztbdb")
            elements = all_elements[len(data_df.index):]
            for ele in elements:
                row = scrap_row(ele, data_df)
                if not row:
                    continue
                if not greater_than_start_date(start_time, row['created_time_kst']):
                    ended = True
                    break
                data_df = pd.concat([data_df, pd.DataFrame([row])], ignore_index=True)
                fails = 0
            if ended:
                break
        except Exception as e:
            fails += 1
            if fails > max_tries:
                break
            scrap.scroll_down()
            print(e)
            print(f"Fail Count: {fails}, Before Element: {row}")

    return data_df


# %%
result_df = scrap_data('2023-01-16 01:00')
print(result_df)

# %%
twitter_url = links_df.loc[2, 'Link']
scrap.go(twitter_url)
#%%
instagram_url = links_df.loc[1, 'Link']
scrap.go(instagram_url)


# %%
scrap.quit()
