import json
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from newsletter_generator import NewsletterGenerator
from security_utils import SecureFileHandler
from website_scrapers import Article as ScraperArticle


class NewsletterGeneratorConfigTests(unittest.TestCase):
    def setUp(self):
        self.config_dir = Path("tmp_test_configs")
        self.config_dir.mkdir(exist_ok=True)
        
        self.env_patch = patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-" + "x" * 50,
            "EMAIL_FROM": "sender@example.com",
            "EMAIL_PASSWORD": "testpass123",
            "EMAIL_TO": "recipient@example.com",
        }, clear=False)
        self.env_patch.start()
        
        self.openai_patch = patch("newsletter_generator.openai.OpenAI", autospec=True)
        self.openai_patch.start()
    
    def tearDown(self):
        self.openai_patch.stop()
        self.env_patch.stop()
        if self.config_dir.exists():
            shutil.rmtree(self.config_dir)
    
    def _write_config(self, relative_path: str, payload: dict) -> Path:
        config_path = self.config_dir / relative_path
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(payload), encoding="utf-8")
        return config_path
    
    def test_load_config_from_subdirectory(self):
        config_path = self._write_config("variants/test_config.json", {"websites": ["healthcareitnews"]})
        generator = NewsletterGenerator(config_path=str(config_path))
        self.assertIn("healthcareitnews", generator.config["websites"])
        self.assertTrue(config_path.exists())
    
    def test_collect_articles_uses_scraper_manager(self):
        config_path = self._write_config("variants/scraper_config.json", {"websites": ["healthcareitnews"]})
        generator = NewsletterGenerator(config_path=str(config_path))
        generator.scrape_hospitalogy = MagicMock(return_value=[])
        sample = ScraperArticle(
            title="Payer's big win",
            url="https://www.healthcareitnews.com/sample",
            content="A detailed look at payer innovation efforts in healthcare." + (" more" * 20),
            published_date=None
        )
        generator.scraper_manager.scrape_website = MagicMock(return_value=[sample])
        
        articles = generator.collect_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Payer's big win")
        self.assertEqual(articles[0].url, "https://www.healthcareitnews.com/sample")
    
    def test_missing_config_raises_file_not_found(self):
        missing_path = self.config_dir / "does_not_exist.json"
        with self.assertRaises(FileNotFoundError):
            NewsletterGenerator(config_path=str(missing_path))
    
    def test_save_newsletter_preserves_plain_text(self):
        config_path = self._write_config("variants/save_config.json", {"websites": ["hospitalogy"]})
        generator = NewsletterGenerator(config_path=str(config_path))
        content = "Here's <b>bold</b> & more."
        with patch.object(SecureFileHandler, "safe_write_file", return_value="newsletters/test.md") as mock_write:
            generator.save_newsletter(content, filename="test_output.md")
            self.assertEqual(mock_write.call_args[0][1], content)


if __name__ == "__main__":
    unittest.main()
