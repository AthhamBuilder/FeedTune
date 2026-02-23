import json
import requests
from bs4 import BeautifulSoup
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
import os

class MainScreen(MDScreen):
    pass

class StarkFilter(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.topic_panel_open = True

        # Load keys3.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(base_dir, "keys3.json")
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f)
        return MainScreen()

    def toggle_topic_panel(self):
        """Slide topic panel in/out"""
        panel = self.root.ids.topic_panel
        if self.topic_panel_open:
            panel.size_hint_x = 0
        else:
            panel.size_hint_x = 0.25
        self.topic_panel_open = not self.topic_panel_open

    def search_topics(self, query):
        """Fetch topic cards using keys3.json URLs"""
        if not query.strip():
            return

        list_view = self.root.ids.list_view
        topic_list = self.root.ids.topic_list
        list_view.clear_widgets()   # keep reading panel clean
        topic_list.clear_widgets()  # clear previous topics

        keywords = [query.lower()]
        urls = self.settings.get("sources", [])

        topics_set = set()  # avoid duplicates

        for url in urls:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(response.text, "html.parser")
                headlines = soup.find_all(["h2", "h3"])

                for h in headlines:
                    a = h.find("a")
                    if not a:
                        continue
                    text = a.get_text().strip()
                    link = a.get("href")
                    if link and link.startswith("/"):
                        link = url.rstrip("/") + link

                    # Only add topic cards to left panel
                    if any(k in text.lower() for k in keywords):
                        if text not in topics_set:
                            topics_set.add(text)
                            topic_card = MDCard(
                                orientation="vertical",
                                size_hint_y=None,
                                height=dp(50),
                                padding=dp(6),
                                radius=[8],
                                md_bg_color=(0.2,0.2,0.2,1),
                                ripple_behavior=True
                            )
                            topic_card.add_widget(MDLabel(
                                text=text,
                                font_style="Body1",
                                size_hint_y=None,
                                height=dp(50),
                                valign="middle"
                            ))
                            topic_card.bind(on_release=lambda x, l=link: self.show_article(l))
                            topic_list.add_widget(topic_card)

            except Exception as e:
                list_view.add_widget(MDLabel(text=f"Error: {e}"))

    def show_article(self, link):
        """Display full article in reading panel"""
        list_view = self.root.ids.list_view
        list_view.clear_widgets()
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(link, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            article_text = "\n\n".join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40)

            if article_text:
                list_view.add_widget(MDLabel(
                    text=article_text,
                    markup=True,
                    size_hint_y=None,
                    adaptive_height=True,
                    theme_text_color="Primary"
                ))
            else:
                list_view.add_widget(MDLabel(text="No content found."))

        except Exception as e:
            list_view.add_widget(MDLabel(text=f"Error loading article: {e}"))

if __name__ == "__main__":
    StarkFilter().run()