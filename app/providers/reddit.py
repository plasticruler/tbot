from . import BaseContentItemCreator, BaseContentProvider
from app import db, log
from app.main.models import ContentItem, ContentTag
from app.redditwrapper import reddit

class RedditContentItemCreator(BaseContentItemCreator):
    def __init__(self):
        super().__init__("Reddit", 1)
    
    def IsImage(url):
        return url.endswith('.jpg') or url.endswith('.jpeg') or url.endswith('.png')

    def GetContent(self, **kwargs):
        super().__init__(kwargs)
        props = {}        
        subname = kwargs['subname']
        limit = kwargs['limit']
        srs = reddit.subreddit(subname).hot(limit=limit)
        j = 0
        for item in srs:
            j = j+1
            if item.stickied or item.pinned:
                continue            
            tags_to_add = [subname]
            props['id'] = item.id
            url = getattr(item, 'url', None)
            props['original_url'] = url
            self.contentItem.title = item.title
            props['text'] = getattr(item, 'selftext', None)
            if url or not 'https://www.reddit.com/r/' in url or not 'wikipedia' in url:
                if getattr(item, 'media', False):
                    if 'reddit_video' in item.media:
                        url = item.media['reddit_video']['fallback_url']
                        props["is_video"] = True  # can send as gif
                    if 'oembed' in item.media:
                        props['oembed'] = item.media['oembed']
                        if 'thumbnail_url' in item.media['oembed']:
                            url = item.media['oembed']['thumbnail_url']
                        if 'type' in item.media['oembed'] and item.media['oembed']['type'] == 'youtube.com':
                            self.contentItem.title = "{} - {}".format(
                                self.contentItem.title, item.media['oembed']['title'])
                # if photo only then s.preview[enabled] = True
                if hasattr(item, 'preview'):
                    if 'reddit_video_preview' in item.preview:
                        if 'fallback_url' in item.preview['reddit_video_preview']:
                            url = item.preview['reddit_video_preview']['fallback_url']
                            props["is_video"] = True  # can send as gif
                    if 'reddit_video' in item.preview:
                        if 'fallback_url' in item.preview['reddit_video']:
                            url = item.preview['reddit_video']['fallback_url']
                            props["is_video"] = True  # can send as gif

            props['url'] = url
            if self.IsImage(url):
                props['is_photo'] = True
            if item.over_18:
                tags_to_add.append('_over_18')
                props["over_18"] = True
            if item.gilded:
                tags_to_add.append('_gilded')
                props["gilded"] = True
            props['total_awards_received'] = item.total_awards_received
            # set tags
            self.SetContentTags(*tags_to_add)
            props['id'] = item.id
            props['shortlink'] = item.shortlink
            props['ups'] = item.ups
            props['downs'] = item.downs
            # we'll also save the top 5 top-level comments
            comments = {}
            self.contentTag.comment_sort = 'best'
            for i in range(5):
                if len(item.comments) > i:
                    comments[i] = item.comments[i].body
            props['comments'] = comments
            self.contentItem.content_hash = get_md5(item.shortlink)
            self.contentItem.data = json.dumps(props)
            try:
                self.contentItem.save_to_db()
                log.info(
                    '{} Processed item with reddit id {} - {} - {}'.format(j, item.id, item.title, item.shortlink))
            except InvalidRequestError as e:
                log.error(e)
                db.session.session.rollback()
            except IntegrityError as e:
                db.session.rollback()
                pass
        

class RedditContentProvider(BaseContentProvider):
    def __init__(self, name):
        super().__init__(name)        
    pass

    def getRandomItem(self, **kwargs):
        super(**kwargs)
        pass
    
    def execute(self, **kwargs):        
        pass
