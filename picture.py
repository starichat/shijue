import requests
import os
from multiprocessing import Pool
from hashlib import md5
from urllib.parse import urlencode

from pymongo import MongoClient

'''
	作者：星星
	时间:2018.7.13
	内容: 分析爬取视觉中国设计师社区网站，利用ajax爬取结果
'''

# 爬取网站内容,获取 ajax 的 json 数据

client = MongoClient()
db = client['picture']
collection = db['picture']
max_page = 10

def get_content(page):
	parameters = {
		'key':'世界杯',
		'type':'json',
		'page':page,
		'size':'20',
		'license':-1,
		'orderby':'rating',
	}
	
	# 用urlencode() 方法构造请求的GET参数，然后用requests请求这个链接，如果返回状态码为200，则调用response的json格式返回
	url = 'http://www.shijue.me/community/search?' + urlencode(parameters)
	print(url)
	try:
		response = requests.get(url)
		if response.status_code == 200:
			return response.json()
	except requests.ConnectionError:
		return None
	
'''
	实现一个保存图片的方法 save_image(), 其中item就是前面返回的一个字典,根据item的title创建文件夹，然后请求这个图片的二进制数据，
	以二进制的形式写入文件，图片的名称可以使用其内容的MD5值，这样可以去重复，
'''
def save_image(item):
	if not os.path.exists(item.get('title')):
		os.mkdir(item.get('title'))
	try:
		response = requests.get(item.get('image'))
		if response.status_code == 200:
			file_path = '{0}/{1}.{2}'.format(item.get('title'), md5(response.content).hexdigest(), 'jpg')
			if not os.path.exists(file_path):
				with open(file_path, 'wb') as f:
					f.write(response.content)
			else:
				print('Already Downloaded', file_path)
	except requests.ConnectionError:
		print('Failed to save Image')


	
def get_monmgodb(json):
	# 解析json数据 并获取 author，createDate，title， image 作为存入 mongodb的结果集
	if json.get('dataArray'):
		# 循环获取图片相关信息
		for item in json.get('dataArray'):
			author = item.get('uploaderName')
			title = item.get('title')
			image = item.get('url')
			createDate = item.get('createDate')
			# 将结果构造成一个字典形式并返回一个生成器
			yield {
				'author':author,
				'title':title,
				'image':image,
				'createDate':createDate
			}
def save_mongdb(result):
	collection.insert(result)
	print(" 保存到mongodb成功 ")

def main(page):
	json = get_content(page)
	print(json)
	for result in get_monmgodb(json):
		try :
			save_mongdb(result)
			save_image(result)
		except :
			pass
		continue
GROUP_START = 1
GROUP_END = 2 # 暂时以爬取 20 页为例
if __name__ == '__main__':
	pool = Pool()
	groups = ([x * 2for x in range(GROUP_START,GROUP_END + 1)])
	pool.map(main,groups)
	pool.close()
	pool.join()

	
