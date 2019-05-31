import json
from typing import List, Set
from urllib.parse import urlencode

import browser_cookie3

import requests
from pymongo import MongoClient

import settings


class IgHelper(object):

    def __init__(self):
        settings.COOKIE_JAR = self.get_cookie_from_browser()
        self.followers: List = self.extract_followers()
        self.following: List = self.extract_following()

    @property
    def followers_set(self) -> Set:
        return set(x['node']['username'] for x in self.followers)

    @property
    def following_set(self) -> Set:
        return set(x['node']['username'] for x in self.following)

    @property
    def unfollowers(self) -> Set:
        return self.following_set - self.followers_set

    @property
    def unfollowing(self) -> Set:
        return self.followers_set - self.following_set
    
    def dump_to_mongo(self):
        """
        Dumps followers and following to MongoDB
        :return: 
        """
        client = MongoClient(host=settings.MONGO_HOST, port=settings.MONGO_PORT)
        db = client[settings.MONGO_DB]
        followers_col = db[f'{settings.TARGET_ID}_followers']
        following_col = db[f'{settings.TARGET_ID}_following']
        followers_col.insert_many(self.followers)
        following_col.insert_many(self.following)

    @staticmethod
    def extract_following() -> List[dict]:
        """
        Runs extraction of following doing paginated requests
        :return: list of nodes (dicts) containing the following accounts
        """
        query = {
            "query_hash": settings.FOLLOWING_QUERY_HASH,
            "variables": json.dumps({
                "id": settings.TARGET_ID,
                "include_reel": True,
                "first": 500
            })
        }

        # FOLLOWING
        ret = []
        querystring = urlencode(query)

        if (settings.COOKIE_JAR != None):
            resp = requests.get(settings.BASE_URL, params=querystring, cookies=settings.COOKIE_JAR)
        else:
            resp = requests.request("GET", settings.BASE_URL, params=querystring, headers=settings.HEADERS)
        data = json.loads(resp.content)
        page_info = data['data']['user']['edge_follow']['page_info']
        edges = data['data']['user']['edge_follow']['edges']

        while True:
            for edge in edges:
                edge["_id"] = edge['node']['id']
                ret.append(edge)
                print(f'FOLLOWING: {edge}')

            has_next_page = page_info['has_next_page']
            if has_next_page:
                new_query = {
                    "query_hash": settings.FOLLOWING_QUERY_HASH,
                    "variables": json.dumps({
                        "id": settings.TARGET_ID,
                        "include_reel": True,
                        "first": 500,
                        "after": page_info['end_cursor']
                    })
                }
                querystring = urlencode(new_query)

                if (settings.COOKIE_JAR != None):
                    resp = requests.get(settings.BASE_URL, params=querystring, cookies=settings.COOKIE_JAR)
                else:
                   resp = requests.request("GET", settings.BASE_URL, params=querystring, headers=settings.HEADERS)

                data = json.loads(resp.content)
                page_info = data['data']['user']['edge_follow']['page_info']
                edges = data['data']['user']['edge_follow']['edges']
            else:
                return ret

    @staticmethod
    def extract_followers() -> List[dict]:
        """
        Runs extraction of followers doing paginated requests
        :return: list of nodes (dicts) containing the followers
        """
        query = {
            "query_hash": settings.FOLLOWERS_QUERY_HASH,
            "variables": json.dumps({
                "id": settings.TARGET_ID,
                "include_reel": True,
                "first": 500
            })
        }

        # EXTRACT FOLLOWERS
        ret = []
        querystring = urlencode(query)

        if (settings.COOKIE_JAR != None):
            resp = requests.get(settings.BASE_URL, params=querystring, cookies=settings.COOKIE_JAR)
        else:
            resp = requests.request("GET", settings.BASE_URL, params=querystring, headers=settings.HEADERS)

        data = json.loads(resp.content)
        page_info = data['data']['user']['edge_followed_by']['page_info']
        edges = data['data']['user']['edge_followed_by']['edges']

        while True:
            for edge in edges:
                edge["_id"] = edge['node']['id']
                ret.append(edge)
                print(f'FOLLOWER: {edge}')

            has_next_page = page_info['has_next_page']
            if has_next_page:
                new_query = {
                    "query_hash": settings.FOLLOWERS_QUERY_HASH,
                    "variables": json.dumps({
                        "id": settings.TARGET_ID,
                        "include_reel": True,
                        "first": 500,
                        "after": page_info['end_cursor']
                    })
                }
                querystring = urlencode(new_query)

                if (settings.COOKIE_JAR != None):
                    resp = requests.get(settings.BASE_URL, params=querystring, cookies=settings.COOKIE_JAR)
                else:
                    resp = requests.request("GET", settings.BASE_URL, params=querystring, headers=settings.HEADERS)
                data = json.loads(resp.content)
                page_info = data['data']['user']['edge_followed_by']['page_info']
                edges = data['data']['user']['edge_followed_by']['edges']
            else:
                return ret

    @staticmethod
    def get_cookie_from_browser():
        print("Trying to get cookies from browser...")
        try:
            cj= browser_cookie3.chrome(domain_name='instagram.com')
            print("Found account in chrome!")
            return cj
        except:
            pass
        try:
            cj= browser_cookie3.firefox(domain_name='instagram.com')
            print("Found account in firefox!")
            return cj
        except:
            pass
        print("No cookies found. Specify manually in settings.py")
        return None



