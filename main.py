try:
	import bs4
	import hashlib
	import html
	import json
	import os
	import random
	import re
	import requests
	import time
	import math
except:
	print("""Error
BeautifulSoup : pip install bs4
Requests : pip install requests
Timeout decorator : pip install timeout-decorator""")
	exit(1)



# ===[ 投稿取得に関する設定 ]===


# 何投稿取得するか (+1で指定)
getMsg = 81

# 接続インターバル (分)
sleepTime = 5

# 有効だと削除されたというだけの内容も通知する
dlMsgNotPass = False


# ===[ Discordに関する設定 ]===


# 更新通知用Webhook URL
webhook_url = "PASTE YOUR WEBHOOK LINK HERE"

# 更新通知用Webhook URL (コードのみ)
code_webhook = "PASTE YOUR WEBHOOK LINK HERE"

# 更新通知用のロールID
roleID = "PASTE YOUR ROLE ID"

# 更新通知用のロールID (コードのみ)
roleID = "PASTE YOUR ROLE ID"

# Webhookのアイコン
icon_url = "https://cdn.discordapp.com/attachments/767693748926677013/808266614356967434/InShot_20210208_182241382.jpg"


# ================


# 改造博物館から投稿を取得する関数
def getKaihaku(num=1, mail):
	ret = []
	r_headers= {"User-Agent": "You can contact me at {mail}"}
	r = requests.get("http://futtobecom.stars.ne.jp/3ds/Codes/", headers=r_headers)
	soup = bs4.BeautifulSoup(r.content, "html.parser")
	soupsA = soup.find_all("p")
	del soupsA[0], soupsA[0] # 余計な要素を削除
	for i in range(num):
		soups = soupsA[i] # i番目の投稿を取得
		replaceLink = [i.string for i in soups.find_all("a")] # 投稿内のhref属性を取得
		date = str(soups).split("\n")[0][-39:][:16] # 投稿日時
		name = str(soups).split("\n")[0].replace("<p>名前: ", "").replace(date, "")\
		[:-23].replace("\u3000", "") # 名前
		uID = str(soups).split("\n")[0][-18:][:8] # ユーザID
		game = html.unescape(str(soups).split("\n")[1].replace("<br/>", "")\
		.replace("<span class=\"delete\">", "")\
		.replace("</span>", "")) # 対応ゲーム
		content = html.unescape(str(soups.find("span")).replace("<br/>", "\n")\
		.replace("<span>", "").replace("</span>", "")\
		.replace("<span style=\"background-color:Yellow;\">", "")\
		.replace("<span style=\"background-color:Orange;\">", "")\
		.replace("<span style=\"color:red;\">", "")\
		.replace("<span style=\"background-color:orange;\">", "")\
		.replace("<span class=\"delete\">", ""))
		# href属性の処理
		for replaceWord in replaceLink:
			# hrefが画像・ファイル以外の処理 = リンク
			if not replaceWord.startswith("画像"):
				content = html.unescape(content).replace("<a href=\"", "", 1).replace(f"\">{replaceWord}</a>", "", 1)
			else: # hrefが画像・ファイルの時の処理
				content = html.unescape(content).replace("<a href=\"", "").replace(f"\">{replaceWord}</a>", "")\
				.replace("Log/upfile", "http://futtobecom.stars.ne.jp/3ds/Codes/Log/upfile")
		ret.append([html.unescape(name), uID, date, game, content])
	return ret


# Webhookでメッセージを送信する関数
def send(name, icon, message, url, embed):
	send_data = {'username': name, 'avatar_url': icon, 'content': message, 'embeds': embed }
	headers = {'Content-Type': 'application/json'}
	response = requests.post(url, json.dumps(send_data), headers=headers, verify=False)


# 投稿にコードが入っているかどうかを確認する関数
# 正規表現 by とるそなー
def CodeInText(text):
	check = re.search("[0-9, a-f, A-F]{4}", text)
	if check is None:
		return False
	else:
		return True


# 削除されたメッセージかどうかを確認する関数
def deletedMessage(text):
	check = re.match("この投稿は「.+」により削除されました。", text)
	if check is not None and len(text) == len(check.group())\
	or text == "この投稿は荒らしのため削除されました。":
		return True
	else:
		return False


# 2000文字を超えたときに分割する関数
def separate(msg):
	sepNum = math.ceil(len(msg)/2000)
	return [msg[2000*i:(i + 1)*2000] for i in range(sepNum)]


# ================

mail = input("Enter your mail address >> ")

# 接続回数を保持する変数
number = 0

# メインループ
while True:

	number += 1
	reverseList = [] # 送信用メッセージを一時記録する配列
	codeOnlyList = [] # 送信用メッセージを一時記録する配列 (コードのみ)

	# ================

	try:
		get = getKaihaku(getMsg, mail)
	except:
		print(f"{'-'*50}\nConnection Error ({number})\n{'-'*50}")
		time.sleep(60*sleepTime)
		continue

	# ================

	# ハッシュを記録するファイルがあればそれを確認する
	if os.path.isfile("hash.txt"):
		with open("hash.txt", mode="r", encoding="UTF-8") as fileH:
			lastMsgHash = [i.replace("\n", "") for i in fileH.readlines()]
	else:
		lastMsgHash = ["---", "---", "---"]

	# ================

	# 投稿の差分から新規に投稿された数を取得
	for i in range(getMsg):

		# 最後の投稿が削除されている場合ハッシュが変わって誤発するので
		# それを防止するための処理
		if get[i][4].startswith("この投稿は") and \
			hashlib.md5(get[i][1].encode()).hexdigest() == lastMsgHash[1] and \
			hashlib.md5(get[i][2].encode()).hexdigest() == lastMsgHash[2]:
			break

		# 上記の処理を通過したら投稿の比較による処理を開始する
		if hashlib.md5(get[i][4].encode()).hexdigest() == lastMsgHash[0] and \
			hashlib.md5(get[i][1].encode()).hexdigest() == lastMsgHash[1] and \
			hashlib.md5(get[i][2].encode()).hexdigest() == lastMsgHash[2]:
			break

		# 荒らしクリーナーが使用されたら最後のメッセージが無く、誤爆するので
		# それを防止するための処理 (かなりアバウト)
		# 最後まで止まらずに行ってしまったら i=0 にしてbreak
		# もしN分間にN個以上投稿されたら無視されることになる
		# なので何投稿取得するかを多めに設定しておく必要あり
		if get[i][4] == get[-1][4] and get[i][2] == get[i][2] and get[i][3] == get[i][3]:
			i = 0
			break

	# ================

	# 上記の処理に使った変数iの値だけメッセージを送信用配列に追加する
	for num in range(i):

		# 消されていない投稿のみを送信用配列に追加する
		# dlMsgNotPass = True ならば消された投稿も送信用配列に追加する
		if not deletedMessage(get[num][4]) or dlMsgNotPass:

			# 更新通知 (コードのみ)
			if CodeInText(get[num][4]):
				codeOnlyList.append([{
					"title": f"`{get[num][3]}`",
					"description": f"{get[num][4]}",
					"color": random.randint(0, 16777215),
					"footer": {"text": f"投稿日時 : {get[num][2]}"},
					"author": {"name": f"{get[num][0]} ({get[num][1]})"}}])

			# 更新通知 (通常)
			embed = [{
				"title": f"`{get[num][3]}`",
				"description": f"{get[num][4]}",
				"color": random.randint(0, 16777215),
				"footer": {"text": f"投稿日時 : {get[num][2]}"},
				"author": {"name": f"{get[num][0]} ({get[num][1]})"}}]

			# ログ用変数
			log = f"{'-'*50}\n\n{get[num][0]} ({get[num][1]}) | {get[num][2]}\n\n{get[num][3]}\n\n{get[num][4]}\n\n"

			reverseList.append([embed, log])

	# ================

	# 新しい順を古い順に変換
	reverseList.reverse()
	codeOnlyList.reverse()

	# ================

	# Webhookでの送信とログへの書き込み
	for embeds in reverseList:
		try:
			if len(embeds[0][0]["description"]) > 2000:
				for n, newDesc in enumerate(separate(embeds[0][0]["description"])):
					embeds[0][0]["description"] = newDesc
					send(f"改造博物館 通知BOT (分割モード : {n + 1})", icon_url, f"||<@&{roleID}>||", webhook_url, embeds[0])
				continue

			send("改造博物館 通知BOT", icon_url, f"||<@&{roleID}>||", webhook_url, embeds[0])
		except Exception as e:
			print(f"{'-'*50}\nSend Error ({number}){e}\n{'-'*50}")

		print(embeds[1])

		# ログへの書き込み
		with open("Kaihaku.log", mode="a", encoding="UTF-8") as file:
			file.write(embeds[1])

	# Webhookでの送信 (コードのみ)
	for embedss in codeOnlyList:
		try:
			if len(embedss[0]["description"]) > 2000:
				for n, newDesc in enumerate(separate(embedss[0]["description"])):
					embedss[0]["description"] = newDesc
					send(f"改造博物館 通知BOT (コードのみ) (分割モード : {n + 1})", icon_url, f"||<@&{roleID2}>||", code_webhook, embedss)
				continue

			send("改造博物館 通知BOT (コードのみ)", icon_url, f"||<@&{roleID2}>||", code_webhook, embedss)
		except Exception as e:
			print(f"{'-'*50}\nConnection Error ({number}){e}\n{'-'*50}")

	# ================

	# 投稿内容, ユーザID, 投稿日時をハッシュにして保存
	with open("hash.txt", mode="w+", encoding="UTF-8") as file2:
		file2.write(hashlib.md5(get[0][4].encode()).hexdigest() + "\n" + \
		hashlib.md5(get[0][1].encode()).hexdigest() + "\n" + \
		hashlib.md5(get[0][2].encode()).hexdigest())

	# ================

	print(f"{'-'*50}\nConnected futtobecom.stars.ne.jp ({number})\n{'-'*50}")

	time.sleep(60*sleepTime)






# (C) 2021 Hidegon
# Licences: MIT
# https://github.com/HidegonSan/KaihakuGetter
# Version 3.3.2 for Public
# Note: It was written a long time ago, so it is dirty and has some unnecessary processing.
