import json
from loguru import logger
from datetime import datetime
from utils.sql import NetflixSQL
from sqlalchemy.orm import Session
from requests.exceptions import RequestException
from utils.base_object import Service, NotificationMSG


class Netflix(Service):
    def __init__(self, _config):
        super().__init__(_config)
        self.result_hash = set()
        # these two list are used for deduplication
        self.notification_list = []
        self.db_list = []

    def get_details(self, page=1) -> dict:
        session = self.get_session()
        url = f"https://about.netflix.com/api/data/releases?language=zh_cn&page={page}&country=HK"
        try:
            res = session.get(url)
            data = res.json()
            return data
        except RequestException as e:
            logger.error(f"Failed to get data from {url}: {e}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Failed to decode json from {url}")
            return {}

    def get_all_details(self) -> dict:
        page = 1
        while True:
            details = self.get_details(page)
            if not details or 'data' not in details:
                break
            for detail in details.get('data', []):
                name = f"{detail.get('title1', '')} {detail.get('title2', '')}"
                if name in self.result_hash:
                    continue
                self.result_hash.add(name)
                for _n in self.notification_list:
                    detail[f'msg_{_n}_read'] = False
                for _db in self.db_list:
                    detail[f'sql_{_db}_read'] = False
                self.results.append(detail)
            # self.results.extend(details.get('data', []))
            if page >= details.get('totalPages', 1):
                break
            page += 1
        return {'totalItems': len(self.results), 'items': self.results}

    def request(self, *args, **kwargs):
        self.notification_list = kwargs.get("notification_list", [])
        self.db_list = kwargs.get("db_list", [])
        self.get_all_details()

    def deduplication(self, *args, **kwargs):
        ...

    def get_notification_msgs(self, *args, **kwargs) -> list[NotificationMSG]:
        msgs = []
        msg_format = kwargs.get("msg_format", "text")
        notification_obj = kwargs.get("notification_obj")
        for result in self.results:
            if result.get(f'msg_{hash(notification_obj.__class__.__name__)}_read', False):
                continue
            result[f'msg_{hash(notification_obj.__class__.__name__)}_read'] = True
            title1 = result.get('title1', '')
            title2 = result.get('title2', '')
            title_name = f"{title1} {title2}" if title1 != title2 else title1
            video_id = result.get('videoID', 0)
            country = result.get('country', '')
            start_time = result.get('startTime', 0)
            collection_id = result.get('collection', 0)
            image = result.get('image', '')
            genre_id = result.get('genre', 0)
            start_time_datetime = datetime.fromtimestamp(start_time/1000 if len(str(start_time)) == 13 else start_time)
            start_time_str = start_time_datetime.strftime(r'%Y-%m-%d %H:%M')
            msg_title = f"{self.__class__.__name__} New Release"
            if msg_format == "markdown":
                msg_body = (f"*Release Name:* {title_name}\n"
                            f"*video_id:* {video_id}\n"
                            f"*start_time:* {start_time_str}\n"
                            f"*image:* [Image]({image})\n"
                            f"*collection_id:* {collection_id}\n"
                            f"*genre_id:* {genre_id}\n"
                            f"*country:* {country}\n"
                            f"*url:* https://www.netflix.com/watch/{video_id}")
            elif msg_format == "html":
                msg_body = (f"<b>Release Name:</b> {title_name}<br>"
                            f"<b>video_id:</b> {video_id}<br>"
                            f"<b>start_time:</b> {start_time_str}<br>"
                            f"<b>image:</b> <a href='{image}'>Image</a><br>"
                            f"<b>collection_id:</b> {collection_id}<br>"
                            f"<b>genre_id:</b> {genre_id}<br>"
                            f"<b>country:</b> {country}<br>"
                            f"<b>url:</b> https://www.netflix.com/watch/{video_id}")
            else:
                msg_body = (f"Release Name: {title_name}\n"
                            f"video_id: {video_id}\n"
                            f"start_time: {start_time_str}\n"
                            f"image: {image}\n"
                            f"collection_id: {collection_id}\n"
                            f"genre_id: {genre_id}\n"
                            f"country: {country}\n"
                            f"url: https://www.netflix.com/watch/{video_id}")
            msgs.append(NotificationMSG(title=msg_title, body=msg_body, msg_format=msg_format, name=title_name,
                                        send_time=start_time_datetime))
        return msgs

    def get_sql_query(self, session: Session, /, *args, **kwargs) -> list[NetflixSQL]:
        queries = []
        if not session:
            logger.error("No session provided")
            return queries
        for result in self.results:
            if result.get(f'sql_{hash(session.bind.url)}_read', False):
                continue
            result[f'sql_{hash(session.bind.url)}_read'] = True
            title1 = result.get('title1', '')
            title2 = result.get('title2', '')
            title_name = f"{title1} {title2}" if title1 != title2 else title1
            # check title_name in db
            if session.query(NetflixSQL).filter(NetflixSQL.name).first():
                continue
            video_id = result.get('videoID', 0)
            country = result.get('country', '')
            start_time = result.get('startTime', 0)
            collection_id = result.get('collection', 0)
            image = result.get('image', '')
            genre_id = result.get('genre', 0)
            url = f"https://www.netflix.com/watch/{video_id}"
            start_time_datetime = datetime.fromtimestamp(start_time/1000 if len(str(start_time)) == 13 else start_time)
            query = NetflixSQL(name=title_name, video_id=video_id, country=country, release_time=start_time_datetime,
                               collection=collection_id, genre=genre_id, image=image, url=url)
            queries.append(query)
        return queries


if __name__ == '__main__':
    n = Netflix()
    print(json.dumps(n.get_all_details()))

