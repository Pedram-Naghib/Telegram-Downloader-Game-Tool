# ------------------------this code is not mine, it's from Evil0ctal github------------------------------------
# Link: https://github.com/Evil0ctal/Douyin_TikTok_Download_API/blob/main/scraper.py
import re
import os
import aiohttp
import platform
import asyncio
import traceback
import configparser
from tenacity import *
from typing import Union


class Scraper:
    """
    简介/Introduction
    Scraper.get_url(text: str) -> Union[str, None]
    用于检索出文本中的链接并返回/Used to retrieve the link in the text and return it.
    Scraper.convert_share_urls(self, url: str) -> Union[str, None]\n
    用于转换分享链接为原始链接/Convert share links to original links
    Scraper.get_douyin_video_id(self, original_url: str) -> Union[str, None]\n
    用于获取抖音视频ID/Get Douyin video ID
    Scraper.get_douyin_video_data(self, video_id: str) -> Union[dict, None]\n
    用于获取抖音视频数据/Get Douyin video data
    Scraper.get_douyin_live_video_data(self, original_url: str) -> Union[str, None]\n
    用于获取抖音直播视频数据/Get Douyin live video data
    Scraper.get_tiktok_video_id(self, original_url: str) -> Union[str, None]\n
    用于获取TikTok视频ID/Get TikTok video ID
    Scraper.get_tiktok_video_data(self, video_id: str) -> Union[dict, None]\n
    用于获取TikTok视频数据/Get TikTok video data
    Scraper.hybrid_parsing(self, video_url: str) -> dict\n
    用于混合解析/ Hybrid parsing
    Scraper.hybrid_parsing_minimal(data: dict) -> dict\n
    用于混合解析最小化/Hybrid parsing minimal
    """

    """__________________________________________⬇️initialization(初始化)⬇️______________________________________"""

    # 初始化/initialization
    def __init__(self):
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
        }
        self.tiktok_api_headers = {
            'User-Agent': 'com.ss.android.ugc.trill/494+Mozilla/5.0+(Linux;+Android+12;+2112123G+Build/SKQ1.211006.001;+wv)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Version/4.0+Chrome/107.0.5304.105+Mobile+Safari/537.36'
        }
        # 判断配置文件是否存在/Check if the configuration file exists
        if os.path.exists('config.ini'):
            self.config = configparser.ConfigParser()
            self.config.read('config.ini', encoding='utf-8')
            # 判断是否使用代理
            if self.config['Scraper']['Proxy_switch'] == 'True':
                # 判断是否区别协议选择代理
                if self.config['Scraper']['Use_different_protocols'] == 'False':
                    self.proxies = {
                        'all': self.config['Scraper']['All']
                    }
                else:
                    self.proxies = {
                        'http': self.config['Scraper']['Http_proxy'],
                        'https': self.config['Scraper']['Https_proxy'],
                    }
            else:
                self.proxies = None
        # 配置文件不存在则不使用代理/If the configuration file does not exist, do not use the proxy
        else:
            self.proxies = None
        # 针对Windows系统的异步事件规则/Asynchronous event rules for Windows systems
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    """__________________________________________⬇️utils(实用程序)⬇️______________________________________"""

    # 检索字符串中的链接
    @staticmethod
    def get_url(text: str) -> Union[str, None]:
        try:
            # 从输入文字中提取索引链接存入列表/Extract index links from input text and store in list
            url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            # 判断是否有链接/Check if there is a link
            if len(url) > 0:
                return url[0]
        except Exception as e:
            print('Error in get_url:', e)
            return None

    # 转换链接/convert url
    @retry(stop=stop_after_attempt(4), wait=wait_fixed(7))
    async def convert_share_urls(self, url: str) -> Union[str, None]:
        """
        用于将分享链接(短链接)转换为原始链接/Convert share links (short links) to original links
        :return: 原始链接/Original link
        """
        # 检索字符串中的链接/Retrieve links from string
        url = self.get_url(url)
        # 判断是否有链接/Check if there is a link
        if url is None:
            print('无法检索到链接/Unable to retrieve link')
            return None
        # 判断是否为TikTok分享链接/TikTok share link
        if '@' in url:
            print('该链接为原始链接,无需转换,原始链接为: {}'.format(url))
            return url
        else:
            print('正在通过TikTok分享链接获取原始链接...')
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self.headers, proxy=self.proxies, allow_redirects=False,
                                            timeout=10) as response:
                        if response.status == 301:
                            url = response.headers['Location'].split('?')[0] if '?' in response.headers[
                                'Location'] else \
                                response.headers['Location']
                            print('获取原始链接成功, 原始链接为: {}'.format(url))
                            return url
            except Exception as e:
                print('获取原始链接失败！')
                print(e)
                return None

    """__________________________________________⬇️TikTok methods(TikTok方法)⬇️______________________________________"""

    # 获取TikTok视频ID/Get TikTok video ID
    async def get_tiktok_video_id(self, original_url: str) -> Union[str, None]:
        """
        获取视频id
        :param original_url: 视频链接
        :return: 视频id
        """
        try:
            # 转换链接/Convert link
            original_url = await self.convert_share_urls(original_url)
            # 获取视频ID/Get video ID
            if '/video/' in original_url:
                video_id = re.findall('/video/(\d+)', original_url)[0]
            elif '/v/' in original_url:
                video_id = re.findall('/v/(\d+)', original_url)[0]
            print('获取到的TikTok视频ID是{}'.format(video_id))
            # 返回视频ID/Return video ID
            return video_id
        except Exception as e:
            print('获取TikTok视频ID出错了:{}'.format(e))
            return None

    @retry(stop=stop_after_attempt(4), wait=wait_fixed(7))
    async def get_tiktok_video_data(self, video_id: str) -> Union[dict, None]:
        """
        获取单个视频信息
        :param video_id: 视频id
        :return: 视频信息
        """
        print('正在获取TikTok视频数据...')
        try:
            # 构造访问链接/Construct the access link
            api_url = f'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={video_id}'
            print("正在获取视频数据API: {}".format(api_url))
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.tiktok_api_headers, proxy=self.proxies,
                                       timeout=10) as response:
                    response = await response.json()
                    video_data = response['aweme_list'][0]
                    print('获取视频信息成功！')
                    return video_data
        except Exception as e:
            print('获取视频信息失败！原因:{}'.format(e))
            # return None
            raise e

    @retry(stop=stop_after_attempt(4), wait=wait_fixed(7))
    async def get_tiktok_user_profile_videos(self, tiktok_video_url: str, tikhub_token: str) -> Union[dict, None]:
        try:
            api_url = f"https://api.tikhub.io/tiktok_profile_videos/?tiktok_video_url={tiktok_video_url}&cursor=0&count=20"
            _headers = {"Authorization": f"Bearer {tikhub_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=_headers, proxy=self.proxies, timeout=10) as response:
                    response = await response.json()
                    return response
        except Exception as e:
            print('获取抖音视频数据失败！原因:{}'.format(e))
            # return None
            raise e

    @retry(stop=stop_after_attempt(4), wait=wait_fixed(7))
    async def get_tiktok_user_profile_liked_videos(self, tiktok_video_url: str, tikhub_token: str) -> Union[dict, None]:
        try:
            api_url = f"https://api.tikhub.io/tiktok_profile_liked_videos/?tiktok_video_url={tiktok_video_url}&cursor=0&count=20"
            _headers = {"Authorization": f"Bearer {tikhub_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=_headers, proxy=self.proxies, timeout=10) as response:
                    response = await response.json()
                    return response
        except Exception as e:
            print('获取抖音视频数据失败！原因:{}'.format(e))
            # return None
            raise e

    """__________________________________________⬇️Hybrid methods(混合方法)⬇️______________________________________"""

    # 自定义获取数据/Custom data acquisition
    async def hybrid_parsing(self, video_url: str) -> dict:
        # URL平台判断/Judge URL platform
        url_platform = 'douyin' if 'douyin' in video_url else 'tiktok'
        print('当前链接平台为:{}'.format(url_platform))
        # 获取视频ID/Get video ID
        print("正在获取视频ID...")
        video_id = await self.get_douyin_video_id(
            video_url) if url_platform == 'douyin' else await self.get_tiktok_video_id(
            video_url)
        if video_id:
            print("获取视频ID成功,视频ID为:{}".format(video_id))
            # 获取视频数据/Get video data
            print("正在获取视频数据...")
            data = await self.get_douyin_video_data(
                video_id) if url_platform == 'douyin' else await self.get_tiktok_video_data(
                video_id)
            if data:
                print("获取视频数据成功，正在判断数据类型...")
                url_type_code = data['aweme_type']
                """以下为抖音/TikTok类型代码/Type code for Douyin/TikTok"""
                url_type_code_dict = {
                    # 抖音/Douyin
                    2: 'image',
                    4: 'video',
                    68: 'image',
                    # TikTok
                    0: 'video',
                    51: 'video',
                    55: 'video',
                    58: 'video',
                    61: 'video',
                    150: 'image'
                }
                # 获取视频类型/Get video type
                # 如果类型代码不存在,则默认为视频类型/If the type code does not exist, it is assumed to be a video type
                print("数据类型代码: {}".format(url_type_code))
                # 判断链接类型/Judge link type
                url_type = url_type_code_dict.get(url_type_code, 'video')
                print("数据类型: {}".format(url_type))
                print("准备开始判断并处理数据...")

                """
                以下为(视频||图片)数据处理的四个方法,如果你需要自定义数据处理请在这里修改.
                The following are four methods of (video || image) data processing. 
                If you need to customize data processing, please modify it here.
                """

                """
                创建已知数据字典(索引相同)，稍后使用.update()方法更新数据
                Create a known data dictionary (index the same), 
                and then use the .update() method to update the data
                """

                result_data = {
                    'status': 'success',
                    'message': "更多接口请查看(More API see): https://api.tikhub.io/docs",
                    'type': url_type,
                    'platform': url_platform,
                    'aweme_id': video_id,
                    'official_api_url':
                        {
                            "User-Agent": self.headers["User-Agent"],
                            "api_url": f"https://www.iesdouyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}&aid=1128&version_name=23.5.0&device_platform=android&os_version=2333&Github=Evil0ctal&words=FXXK_U_ByteDance"
                        } if url_platform == 'douyin'
                        else
                        {
                            "User-Agent": self.tiktok_api_headers["User-Agent"],
                            "api_url": f'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={video_id}'
                        },
                    'desc': data.get("desc"),
                    'create_time': data.get("create_time"),
                    'author': data.get("author"),
                    'music': data.get("music"),
                    'statistics': data.get("statistics"),
                    'cover_data': {
                        'cover': data.get("video").get("cover"),
                        'origin_cover': data.get("video").get("origin_cover"),
                        'dynamic_cover': data.get("video").get("dynamic_cover")
                    },
                    'hashtags': data.get('text_extra'),
                }
                # 创建一个空变量，稍后使用.update()方法更新数据/Create an empty variable and use the .update() method to update the data
                api_data = None
                # 判断链接类型并处理数据/Judge link type and process data
                try:
                    # 抖音数据处理/Douyin data processing
                    if url_platform == 'douyin':
                        # 抖音视频数据处理/Douyin video data processing
                        if url_type == 'video':
                            print("正在处理抖音视频数据...")
                            # 将信息储存在字典中/Store information in a dictionary
                            uri = data['video']['play_addr']['uri']
                            wm_video_url = data['video']['play_addr']['url_list'][0]
                            wm_video_url_HQ = f"https://aweme.snssdk.com/aweme/v1/playwm/?video_id={uri}&radio=1080p&line=0"
                            nwm_video_url = wm_video_url.replace('playwm', 'play')
                            nwm_video_url_HQ = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&ratio=1080p&line=0"
                            api_data = {
                                'video_data':
                                    {
                                        'wm_video_url': wm_video_url,
                                        'wm_video_url_HQ': wm_video_url_HQ,
                                        'nwm_video_url': nwm_video_url,
                                        'nwm_video_url_HQ': nwm_video_url_HQ
                                    }
                            }
                        # 抖音图片数据处理/Douyin image data processing
                        elif url_type == 'image':
                            print("正在处理抖音图片数据...")
                            # 无水印图片列表/No watermark image list
                            no_watermark_image_list = []
                            # 有水印图片列表/With watermark image list
                            watermark_image_list = []
                            # 遍历图片列表/Traverse image list
                            for i in data['images']:
                                no_watermark_image_list.append(i['url_list'][0])
                                watermark_image_list.append(i['download_url_list'][0])
                            api_data = {
                                'image_data':
                                    {
                                        'no_watermark_image_list': no_watermark_image_list,
                                        'watermark_image_list': watermark_image_list
                                    }
                            }
                    # TikTok数据处理/TikTok data processing
                    elif url_platform == 'tiktok':
                        # TikTok视频数据处理/TikTok video data processing
                        if url_type == 'video':
                            print("正在处理TikTok视频数据...")
                            # 将信息储存在字典中/Store information in a dictionary
                            wm_video = data['video']['download_addr']['url_list'][0]
                            api_data = {
                                'video_data':
                                    {
                                        'wm_video_url': wm_video,
                                        'wm_video_url_HQ': wm_video,
                                        'nwm_video_url': data['video']['play_addr']['url_list'][0],
                                        'nwm_video_url_HQ': data['video']['bit_rate'][0]['play_addr']['url_list'][0]
                                    }
                            }
                        # TikTok图片数据处理/TikTok image data processing
                        elif url_type == 'image':
                            print("正在处理TikTok图片数据...")
                            # 无水印图片列表/No watermark image list
                            no_watermark_image_list = []
                            # 有水印图片列表/With watermark image list
                            watermark_image_list = []
                            for i in data['image_post_info']['images']:
                                no_watermark_image_list.append(i['display_image']['url_list'][0])
                                watermark_image_list.append(i['owner_watermark_image']['url_list'][0])
                            api_data = {
                                'image_data':
                                    {
                                        'no_watermark_image_list': no_watermark_image_list,
                                        'watermark_image_list': watermark_image_list
                                    }
                            }
                    # 更新数据/Update data
                    result_data.update(api_data)
                    # print("数据处理完成，最终数据: \n{}".format(result_data))
                    # 返回数据/Return data
                    return result_data
                except Exception as e:
                    traceback.print_exc()
                    print("数据处理失败！")
                    return {'status': 'failed', 'message': '数据处理失败！/Data processing failed!'}
            else:
                print("[抖音|TikTok方法]返回数据为空，无法处理！")
                return {'status': 'failed',
                        'message': '返回数据为空，无法处理！/Return data is empty and cannot be processed!'}
        else:
            print('获取视频ID失败！')
            return {'status': 'failed', 'message': '获取视频ID失败！/Failed to get video ID!'}

    # 处理数据方便快捷指令使用/Process data for easy-to-use shortcuts
    @staticmethod
    def hybrid_parsing_minimal(data: dict) -> dict:
        # 如果数据获取成功/If the data is successfully obtained
        if data['status'] == 'success':
            result = {
                'status': 'success',
                'message': data.get('message'),
                'platform': data.get('platform'),
                'type': data.get('type'),
                'desc': data.get('desc'),
                'wm_video_url': data['video_data']['wm_video_url'] if data['type'] == 'video' else None,
                'wm_video_url_HQ': data['video_data']['wm_video_url_HQ'] if data['type'] == 'video' else None,
                'nwm_video_url': data['video_data']['nwm_video_url'] if data['type'] == 'video' else None,
                'nwm_video_url_HQ': data['video_data']['nwm_video_url_HQ'] if data['type'] == 'video' else None,
                'no_watermark_image_list': data['image_data']['no_watermark_image_list'] if data[
                                                                                                'type'] == 'image' else None,
                'watermark_image_list': data['image_data']['watermark_image_list'] if data['type'] == 'image' else None
            }
            return result
        else:
            return data


# ------------------------end of the code borrowed from Evil0ctal github------------------------------------
# Rest of the code was written by me

async def get_data(url: str) -> dict:
    api = Scraper()
    # 运行测试
    # tiktok_url = 'https://vt.tiktok.com/ZSRwWXtdr/'
    tiktok_hybrid_data = await api.hybrid_parsing(url)
    return tiktok_hybrid_data
    # asyncio.run(async_test(tiktok_url=tiktok_url))
    

from src.constants import(
    IsAdmin,
    clean_folder,
    proc_keys
)
import telebot
from telebot import formatting, types
import urllib.request
from src import responses, media_tools, bot

    
@ bot.message_handler(regexp=r'https://[a-zA-Z]+\.tiktok\.com')
def direct(msg):

    data = asyncio.run(get_data(msg.text.strip()))
    vidid = data["aweme_id"]
    usr = data['author']
    usrcap = formatting.hlink(usr['unique_id'], f"https://www.tiktok.com/@{usr['unique_id']}", escape = True)
    if data['type'] == 'video':
        thumb = data['cover_data']['origin_cover']
        try:
            with open(f'media/{vidid}.mp4', 'wb') as video:
                video.write(urllib.request.urlopen(data['video_data']['nwm_video_url']).read())
            with open(f'media/{vidid}.jpg', 'wb') as thumbb:
                thumbb.write(urllib.request.urlopen(thumb['url_list'][0]).read())
        except Exception as e:
            bot.send_message(msg.chat.id, f"Invalid video URL!")
            bot.send_message(media_tools.ME, f"{msg.text}\n\n{e}")
        
        video_data = responses.read_media(f'media/{vidid}.mp4')
        thumb_data = responses.read_media(f'media/{vidid}.jpg')
        
        wait = bot.send_message(msg.chat.id, 'Please wait...')
        bot.send_chat_action(msg.chat.id, 'upload_video')
        cap = f'{telebot.formatting.escape_html(data["desc"])}\n\n👤{usrcap}\n\n@HumbanBot'
        vid = bot.send_video(msg.chat.id, video_data, None, 576, 1048, thumb_data,
                             cap, 'html', reply_to_message_id=msg.message_id)
        bot.delete_message(msg.chat.id, wait.message_id)

        try:
            if IsAdmin.check(msg):
                proc_keys(msg.chat.id, vidid, vid.message_id)
            else:
                clean_folder(vidid)
        except telebot.apihelper.ApiTelegramException as e:
            print(e)
        
    else:
        try:
            caption = f'{data["desc"]}\n\n👤 {usrcap}\n\n@HumbanBot'
            imgs = data['image_data']['no_watermark_image_list']
            photos = [types.InputMediaPhoto(img) for img in imgs[1:]]
            first = imgs[0]
            photos.insert(0, types.InputMediaPhoto(first, caption, parse_mode='html'))
            if len(photos) < 11:
                return bot.send_media_group(msg.chat.id, photos)
            for _ in range((len(photos) // 10) + 1):
                bot.send_media_group(msg.chat.id, photos[:10])
                photos = photos[10:]
        except Exception as exception: # Fix me: broad-except
            bot.reply_to(msg, f'ERROR: {exception}')
