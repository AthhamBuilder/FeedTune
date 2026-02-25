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
        self.topic_panel_open = False  # Start closed

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(base_dir, "keys3.json")

        with open(self.json_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f)

        screen = MainScreen()

        # Hide sidebar on startup
        Clock.schedule_once(lambda dt: self._init_layout(screen), 0)

        return screen

    def _init_layout(self, screen):
        screen.ids.topic_scroll.size_hint_x = 0
        screen.ids.main_scroll.size_hint_x = 1
        screen.ids.main_scroll.pos_hint = {"x": 0, "y": 0.05}

    # -----------------------------
    # Sidebar Controls
    # -----------------------------

    def open_sidebar(self):
        if not self.topic_panel_open:
            Animation(size_hint_x=0.22, duration=0.25).start(
                self.root.ids.topic_scroll
            )
            self.root.ids.main_scroll.size_hint_x = 0.78
            self.root.ids.main_scroll.pos_hint = {"x": 0.22, "y": 0.05}
            self.topic_panel_open = True

    def close_sidebar(self):
        if self.topic_panel_open:
            Animation(size_hint_x=0, duration=0.25).start(
                self.root.ids.topic_scroll
            )
            self.root.ids.main_scroll.size_hint_x = 1
            self.root.ids.main_scroll.pos_hint = {"x": 0, "y": 0.05}
            self.topic_panel_open = False

    # -----------------------------
    # Search Logic
    # -----------------------------

    def search_topics(self, query):
        if not query.strip():
            return

        self.open_sidebar()

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

                        # ---- Topic Card (Sidebar) ----
                        if text not in topics_set:
                            topics_set.add(text)

                            topic_card = MDCard(
                                orientation="vertical",
                                size_hint_y=None,
                                height=dp(60),
                                padding=dp(12),
                                radius=[12],
                                md_bg_color=(0.18, 0.18, 0.18, 1),
                                elevation=2,
                                ripple_behavior=True,
                            )

                            topic_card.add_widget(
                                MDLabel(
                                    text=text[:40] + "..." if len(text) > 40 else text,
                                    font_style="Body2",
                                    size_hint_y=None,
                                    height=dp(60),
                                    shorten=True,
                                    max_lines=1,
                                )
                            )

                            topic_card.bind(
                                on_release=lambda x, l=link: self.show_article(l)
                            )

                            topic_list.add_widget(topic_card)

                        # ---- Preview Card (Main Panel) ----
                        preview_card = MDCard(
                            orientation="vertical",
                            size_hint=(1, None),
                            height=dp(100),
                            radius=[16],
                            md_bg_color=(0.18, 0.18, 0.18, 1),
                            elevation=3,
                            padding=dp(14),
                            ripple_behavior=True,
                        )

                        preview_card.add_widget(
                            MDLabel(
                                text=text,
                                font_style="Body1",
                                adaptive_height=True,
                                max_lines=3,
                                shorten=True,
                            )
                        )

                        preview_card.bind(
                            on_release=lambda x, l=link: self.show_article(l)
                        )

                        list_view.add_widget(preview_card)

            except Exception as e:
                list_view.add_widget(
                    MDLabel(text=f"Error: {e}", size_hint_y=None, height=dp(40))
                )

    # -----------------------------
    # Article Display
    # -----------------------------

    def show_article(self, link):

        self.close_sidebar()

        list_view = self.root.ids.list_view
        list_view.clear_widgets()

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(link, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")

            article_text = "\n\n".join(
                p.get_text().strip()
                for p in paragraphs
                if len(p.get_text().strip()) > 40
            )

            if article_text:
                article_card = MDCard(
                    orientation="vertical",
                    size_hint=(1, None),
                    adaptive_height=True,
                    radius=[16],
                    md_bg_color=(0.18, 0.18, 0.18, 1),
                    elevation=2,
                    padding=dp(16),
                )

                article_card.add_widget(
                    MDLabel(
                        text=article_text,
                        adaptive_height=True,
                        theme_text_color="Primary",
                        font_style="Body1",
                    )
                )

                list_view.add_widget(article_card)

            else:
                list_view.add_widget(
                    MDLabel(
                        text="No content found.",
                        size_hint_y=None,
                        height=dp(40),
                    )
                )

        except Exception as e:
            list_view.add_widget(
                MDLabel(
                    text=f"Error loading article: {e}",
                    size_hint_y=None,
                    height=dp(40),
                )
            )


if __name__ == "__main__":
    StarkFilter().run()