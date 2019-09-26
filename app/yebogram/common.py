import re
from igramscraper.instagram import Instagram
from app.yebogram.proxies import proxies

instagram_url_re = "(https?:\/\/(?:www\.)?instagram\.com\/p\/([^/?#&]+)).*"
cache_folder = '/home/romeo/tmp'
instagram = Instagram()
instagram.set_proxies(proxies)


#instagram.with_credentials('','',cache_folder)
#instagram.login()
#media.idenfitier


def get_media_code_from_url(url):
    return re.search(instagram_url_re, url).group(2)


def get_comments_by_media(shortcode, max=10):
    pass

def get_likes_and_comments_by_media(shortcode, max=20):
    likes = instagram.get_media_likes_by_code(shortcode, max)
    comments = instagram.get_media_comments_by_code(shortcode, max)
    return {'likes': likes['accounts'], 'comments': comments['comments']}

def contains_instagram_link(msg):    
    #0 return whole string
    #1 return only matched
    #2 return media code
    res = re.search(instagram_url_re, msg)
    #return re.search(se,msg).group(2)
    if res is not None:
        return True
    return False