import os, json

with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('import argparse', 'import argparse\nimport json')

new_method = '''
    def _load_desktop_paths(self):
        try:
            if os.path.exists("config/desktop_paths.json"):
                with open("config/desktop_paths.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return None
'''

c = c.replace('class RedditSunoAgent:', 'class RedditSunoAgent:' + new_method)
c = c.replace('self.reddit_collector = None', 'self.desktop_paths = self._load_desktop_paths()\n        self.reddit_collector = None')

old_music = '''self.music_generator = MusicGenerator(
                    api_type="unofficial",
                    api_id=suno_config.get("api_id"),
                    token=suno_config.get("token")
                )'''

new_music = '''articles_dir = "output/articles"
            music_dir = "output/music"
            if self.desktop_paths:
                articles_dir = self.desktop_paths["articles_dir"]
                music_dir = self.desktop_paths["music_dir"]
                print("使用桌面输出目录")
            
            os.makedirs(articles_dir, exist_ok=True)
            os.makedirs(music_dir, exist_ok=True)
            
            self.music_generator = MusicGenerator(
                    api_type="unofficial",
                    api_id=suno_config.get("api_id"),
                    token=suno_config.get("token"),
                    output_dir=music_dir
                )'''

c = c.replace(old_music, new_music)
c = c.replace('self.article_generator = ArticleGenerator()', 'self.article_generator = ArticleGenerator(output_dir=articles_dir)')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("✅ main.py 已修改")
