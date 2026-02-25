import json
import requests
from bs4 import BeautifulSoup
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
import os

class MainScreen(MDScreen):
    pass

class StarkFilter(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.topic_panel_open = True

        # Load keys3.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(base_dir, "keys3.json")
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f)
        return MainScreen()

    def toggle_topic_panel(self):
        """Slide topic panel smoothly"""
        panel = self.root.ids.topic_panel
        target_width = 0.25 if not self.topic_panel_open else 0
        anim = Animation(size_hint_x=target_width, duration=0.25)
        anim.start(panel)
        self.topic_panel_open = not self.topic_panel_open

    def search_topics(self, query):
        """Fetch topic cards and search result previews"""
        if not query.strip():
            return

        list_view = self.root.ids.list_view
        topic_list = self.root.ids.topic_list
        list_view.clear_widgets()
        topic_list.clear_widgets()

        keywords = [query.lower()]
        urls = self.settings.get("sources", [])

        topics_set = set()

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

                    if any(k in text.lower() for k in keywords):
                        # --- Topic panel card ---
                        if text not in topics_set:
                            topics_set.add(text)
                            topic_card = MDCard(
                                orientation="vertical",
                                size_hint_y=None,
                                height=dp(60),
                                padding=dp(12),
                                spacing=dp(4),
                                radius=[12],
                                md_bg_color=(0.18, 0.18, 0.18, 1),
                                elevation=2,
                                ripple_behavior=True
                            )
                            topic_card.add_widget(MDLabel(
                                text=text[:40] + "..." if len(text) > 40 else text,
                                font_style="Body2",
                                size_hint_y=None,
                                height=dp(60),
                                valign="middle",
                                shorten=True,
                                max_lines=1
                            ))
                            topic_card.bind(on_release=lambda x, l=link: self.show_article(l))
                            topic_list.add_widget(topic_card)

                        # --- Search result preview in reading panel ---
                        preview_card = MDCard(
                            orientation="vertical",
                            size_hint=(1, None),
                            height=dp(100),
                            radius=[16],
                            md_bg_color=(0.18, 0.18, 0.18, 1),
                            elevation=3,
                            ripple_behavior=True,
                            padding=dp(14),
                            spacing=dp(8)
                        )
                        preview_card.add_widget(MDLabel(
                            text=text,
                            font_style="Body1",
                            size_hint_y=None,
                            adaptive_height=True,
                            max_lines=3,
                            shorten=True,
                            valign="top",
                            theme_text_color="Primary"
                        ))
                        preview_card.bind(on_release=lambda x, l=link: self.show_article(l))
                        # Add preview cards with a tiny delay to make smooth rendering
                        Clock.schedule_once(lambda dt, c=preview_card: list_view.add_widget(c), 0)

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
                # Create article container card
                article_card = MDCard(
                    orientation="vertical",
                    size_hint=(1, None),
                    adaptive_height=True,
                    radius=[16],
                    md_bg_color=(0.18, 0.18, 0.18, 1),
                    elevation=2,
                    padding=dp(16),
                    spacing=dp(12)
                )
                
                article_card.add_widget(MDLabel(
                    text=article_text,
                    markup=True,
                    size_hint_y=None,
                    adaptive_height=True,
                    theme_text_color="Primary",
                    font_style="Body1"
                ))
                list_view.add_widget(article_card)
            else:
                list_view.add_widget(MDLabel(
                    text="No content found.",
                    size_hint_y=None,
                    height=dp(60),
                    valign="center"
                ))

        except Exception as e:
            list_view.add_widget(MDLabel(
                text=f"Error loading article: {e}",
                size_hint_y=None,
                height=dp(60),
                valign="center"
            ))

if __name__ == "__main__":
    StarkFilter().run()