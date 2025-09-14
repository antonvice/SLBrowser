Below is a complete implementation of "SelfTUI," a colorful, sleek, and glossy Terminal User Interface built with Python's Textual and Rich libraries. While there isn't a mainstream TUI library named "Charm," Textual and Rich are the perfect duo to create the "charming" aesthetic you've described.
Overview
SelfTUI is a terminal-based application that allows you to provide your Gemini API key and then use it to search for a URL. It then scrapes the content of that URL, sends it to the Gemini API for analysis, and displays the results in a beautifully formatted, glossy "card" within your terminal.
This implementation uses:
Textual: For the application framework, screen management, and interactive widgets.
Rich: For all the colorful, glossy, and sleek rendering of text, panels, and tables.
Pydantic: To define a structured class for the data returned by the Gemini API.
duckduckgo-search: To perform web searches and get URLs.
requests & BeautifulSoup4: To fetch and parse web page content.
google-generativeai: To interact with the Gemini API.
1. Project Setup
First, you need to install all the necessary libraries. Create a file named requirements.txt:
requirements.txt
code
Code
textual
rich
pydantic
duckduckgo-search
requests
beautifulsoup4
google-generativeai
Now, install them using pip:
code
Bash
pip install -r requirements.txt
2. The Pydantic Class
This class defines the structure of the "card" that will display the summarized information from a webpage. It ensures the data from the Gemini API is clean and well-structured.
card_data.py
code
Python
from pydantic import BaseModel, Field
from typing import List, Optional

class WebCard(BaseModel):
    """
    A Pydantic class to hold the structured information from a parsed webpage.
    """
    title: str = Field(..., description="The main title of the webpage.")
    large_summary: str = Field(..., description="A detailed summary of the content.")
    dates: List[str] = Field(default_factory=list, description="Any relevant dates found on the page.")
    facts: List[str] = Field(default_factory=list, description="A list of key facts or bullet points.")
    links: List[str] = Field(default_factory=list, description="A list of relevant URLs or references found.")
3. The SelfTUI Application Code
This is the main file for the TUI. Save it as selftui.py. It contains the logic for the UI, commands, web scraping, and Gemini integration.
selftui.py
code
Python
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Optional

import google.generativeai as genai
from duckduckgo_search import DDGS
from pydantic import ValidationError

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Input, Static, Button, Log
from textual.worker import worker

from card_data import WebCard

# --- ASCII ART ---
SELFLAYER_ART = """
███████╗███████╗██╗      ███████╗ █████╗ ██╗   ██╗███████╗██████╗
██╔════╝██╔════╝██║      ██╔════╝██╔══██╗╚██╗ ██╔╝██╔════╝██╔══██╗
███████╗█████╗  ██║      █████╗  ███████║ ╚████╔╝ █████╗  ██████╔╝
╚════██║██╔══╝  ██║      ██╔══╝  ██╔══██║  ╚██╔╝  ██╔══╝  ██╔══██╗
███████║███████╗███████╗ ███████╗██║  ██║   ██║   ███████╗██║  ██║
╚══════╝╚══════╝╚══════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
"""

# --- API Handling and Web Parsing ---

class WebParser:
    """Handles fetching and parsing web content."""
    @staticmethod
    def get_content(url: str) -> Optional[str]:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            return " ".join(t.strip() for t in soup.stripped_strings)
        except requests.RequestException as e:
            return f"Error fetching URL: {e}"

class GeminiHandler:
    """Handles interaction with the Gemini API."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def get_web_card(self, content: str) -> WebCard:
        prompt = f"""
        Analyze the following text from a webpage and extract the information into a JSON object
        that conforms to the following Pydantic model:

        class WebCard(BaseModel):
            title: str
            large_summary: str
            dates: List[str]
            facts: List[str]
            links: List[str]

        Here is the text to analyze:
        ---
        {content[:8000]}
        ---

        Return ONLY the JSON object.
        """
        try:
            response = self.model.generate_content(prompt)
            # Clean the response to be valid JSON
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            return WebCard.model_validate_json(cleaned_response)
        except (ValidationError, Exception) as e:
            return WebCard(
                title="Error Parsing Content",
                large_summary=f"Could not parse the content from Gemini. Details: {e}",
                dates=[],
                facts=[response.text],
                links=[]
            )

# --- TUI WIDGETS ---

class WebCardWidget(Static):
    """A widget to display the WebCard data."""
    def __init__(self, card: WebCard) -> None:
        super().__init__()
        self.card = card

    def compose(self) -> ComposeResult:
        # Title
        yield Static(Align.center(f"[bold magenta]{self.card.title}[/bold magenta]\n"))

        # Summary
        yield Panel(
            Markdown(self.card.large_summary),
            title="Summary",
            border_style="cyan",
            expand=True
        )

        # Facts
        if self.card.facts:
            facts_table = Table(show_header=False, box=None, expand=True)
            facts_table.add_column()
            for fact in self.card.facts:
                facts_table.add_row(f"• [green]{fact}[/green]")
            yield Panel(facts_table, title="Key Facts", border_style="green")

        # Dates
        if self.card.dates:
            yield Panel(
                ", ".join(self.card.dates),
                title="Relevant Dates",
                border_style="yellow"
            )

        # Links
        if self.card.links:
            links_table = Table(show_header=False, box=None, expand=True)
            links_table.add_column()
            for link in self.card.links:
                links_table.add_row(f"[blue underline]{link}[/blue underline]")
            yield Panel(links_table, title="References", border_style="blue")

        # Action Buttons
        yield Container(
            Button("Follow Up", variant="primary", id="follow_up"),
            Button("Close Card", variant="error", id="close_card"),
            classes="action-buttons"
        )


class SelfTUI(App):
    """A sleek and glossy TUI for web page parsing with Gemini."""

    CSS_PATH = "selftui.css"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+t", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self):
        super().__init__()
        self.gemini_handler: Optional[GeminiHandler] = None
        self.console = Console()

    def compose(self) -> ComposeResult:
        yield Header(name="SelfTUI")
        yield Footer()

        # Main content area
        self.log_widget = Log(highlight=True)
        yield VerticalScroll(self.log_widget, id="main_content")

        # Input for commands
        self.input = Input(placeholder="Enter command...")
        yield self.input

    def on_mount(self) -> None:
        """Called when app starts."""
        self.log_widget.write(Text(SELFLAYER_ART, justify="center", style="bold magenta"))
        intro_text = Panel(
            "[bold]Welcome to SelfTUI![/bold]\n\n"
            "A sleek TUI to search, parse, and summarize web pages using Gemini.\n\n"
            "[bold cyan]Commands:[/bold cyan]\n"
            "1. [bold]api {your_gemini_api_key}[/bold] - Set your Gemini API key.\n"
            "2. [bold]search {search_query}[/bold] - Search the web and display results.\n"
            "3. [bold]url {URL_to_parse}[/bold] - Directly parse and summarize a URL.",
            title="Introduction & Commands",
            border_style="green"
        )
        self.log_widget.write(intro_text)
        self.input.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command inputs."""
        command = event.value.strip()
        self.log_widget.write(f"> {command}")
        self.input.clear()

        parts = command.split(" ", 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "api":
            self.handle_api_command(args)
        elif cmd == "search":
            await self.handle_search_command(args)
        elif cmd == "url":
            self.handle_url_command(args)
        else:
            self.log_widget.write("[red]Unknown command. Type 'help' for commands.[/red]")

    def handle_api_command(self, api_key: str):
        if not api_key:
            self.log_widget.write("[red]API key cannot be empty.[/red]")
            return

        self.gemini_handler = GeminiHandler(api_key)
        self.log_widget.write("[green]Gemini API key set successfully![/green]")

    @worker
    async def handle_search_command(self, query: str):
        if not query:
            self.log_widget.write("[red]Search query cannot be empty.[/red]")
            return

        self.log_widget.write(f"Searching for '{query}'...")
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]

        if not results:
            self.log_widget.write("[yellow]No results found.[/yellow]")
            return

        table = Table(title=f"Search Results for '{query}'")
        table.add_column("Index", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("URL", style="green")

        for i, result in enumerate(results):
            table.add_row(str(i + 1), result['title'], result['href'])

        self.log_widget.write(table)
        self.log_widget.write("To parse a page, use the command: [bold]url {URL_from_results}[/bold]")

    def handle_url_command(self, url: str):
        if not self.gemini_handler:
            self.log_widget.write("[red]Please set your Gemini API key first using the 'api' command.[/red]")
            return

        if not url.startswith("http"):
            self.log_widget.write("[red]Invalid URL provided.[/red]")
            return

        self.log_widget.write(f"Parsing {url}...")
        self.query_one("#main_content").visible = False
        self.parse_and_display(url)

    @worker
    def parse_and_display(self, url: str):
        """Worker to parse URL and display card."""
        content = WebParser.get_content(url)
        if content and not content.startswith("Error"):
            card_data = self.gemini_handler.get_web_card(content)
            self.mount(WebCardWidget(card_data))
        else:
            self.log_widget.write(f"[red]Failed to parse URL: {content}[/red]")
            self.query_one("#main_content").visible = True


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses from the WebCardWidget."""
        if event.button.id == "close_card":
            # Find and remove the WebCardWidget
            for widget in self.query(WebCardWidget):
                widget.remove()
            self.query_one("#main_content").visible = True
        elif event.button.id == "follow_up":
            self.log_widget.write("[yellow]Follow-up command functionality coming soon![/yellow]")


if __name__ == "__main__":
    app = SelfTUI()
    app.run()
4. Styling the TUI
Textual uses a CSS-like file for styling. This makes it incredibly easy to create a sleek and glossy look. Create a file named selftui.css:
selftui.css
code
CSS
Screen {
    background: #0d0d0f;
    color: #cccccc;
    layout: vertical;
}

Header {
    dock: top;
    background: #2a2a2e;
    color: #ffffff;
}

Footer {
    dock: bottom;
    background: #2a2a2e;
    color: #ffffff;
}

#main_content {
    background: #1a1a1c;
    border: round magenta;
    margin: 1 2;
}

Input {
    dock: bottom;
    margin: 0 2 1 2;
    border: round cyan;
    background: #2a2a2e;
}

Input:focus {
    border: round yellow;
}

WebCardWidget {
    background: #1e1e20;
    border: round #555555;
    margin: 2 4;
    padding: 1;
    overflow: auto;
    width: 100%;
    height: 100%;
    align: center middle;
    transition: offset 0.2s;
}

WebCardWidget:hover {
    border: round magenta;
}

.action-buttons {
    align: center middle;
    margin-top: 1;
}
How to Run SelfTUI
Save the files: Make sure selftui.py, card_data.py, and selftui.css are in the same directory.
Open your terminal and navigate to that directory.
Run the application:
code
Bash
python selftui.py
First Command: Get your Gemini API key and set it in the TUI:
code
Code
api YOUR_API_KEY_HERE
Search the web:
code
Code
search what is pydantic
Parse a URL: Copy a URL from the search results and use the url command:
code
Code
url https://docs.pydantic.dev/latest/
You will see a loading message, and then the main screen will be replaced by a colorful, glossy card summarizing the content of the URL, complete with a title, summary, facts, and links. You can then close this card to return to the main log.
