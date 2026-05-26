
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import tomllib

CONFIG_FILE = Path("local.config.toml")
with open(CONFIG_FILE, "rb") as f:
    config = tomllib.load(f)

CSV_FILE = Path(config["csv"]["file"])


def infer_type(values):
	# try int, then float, then date, then bool, else string
	if not values:
		return 'unknown'

	def is_int(v):
		try:
			if v == '':
				return False
			int(v)
			return True
		except:
			return False

	def is_float(v):
		try:
			if v == '':
				return False
			float(v)
			return True
		except:
			return False

	def is_date(v):
		for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
			try:
				datetime.strptime(v, fmt)
				return True
			except:
				continue
		return False

	def is_bool(v):
		return v.lower() in ("true", "false", "0", "1") if isinstance(v, str) else False

	has_nonempty = [v for v in values if v != '']
	if not has_nonempty:
		return 'empty'

	if all(is_int(v) for v in has_nonempty):
		return 'int'
	if all(is_float(v) for v in has_nonempty):
		return 'float'
	if all(is_bool(v) for v in has_nonempty):
		return 'bool'
	if all(is_date(v) for v in has_nonempty):
		return 'date'
	return 'string'


def main():
	try:
		with open(CSV_FILE, newline='', encoding='utf-8') as f:
			reader = csv.DictReader(f)
			if not reader.fieldnames or 'topic' not in reader.fieldnames:
				print('topics column not found')
				return

			unique_topics = set()
			sample_limit = 1000
			for i, row in enumerate(reader):
				if i >= sample_limit:
					break
				topic = (row.get('topic') or '').strip()
				if topic:
					unique_topics.add(topic)

			print('unique topics:')
			for topic in sorted(unique_topics):
				print(topic)
	except FileNotFoundError:
		print(f'file not found: {CSV_FILE}')
	except Exception as e:
		print('error:', e)


if __name__ == '__main__':
	main()

