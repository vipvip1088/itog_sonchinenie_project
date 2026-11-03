import unittest
from criteria import count_words, basic_audit
from library import LiteratureLibrary
from themes import ThemeBank
from ai.llama_backend import clean_model_output


class CoreTests(unittest.TestCase):
    def test_word_count(self):
        self.assertEqual(count_words("Раз, два три! Это текст."), 5)

    def test_minimum_volume_warning(self):
        report = basic_audit("слово " * 100)
        self.assertIn("менее 250 слов", report)

    def test_recommended_volume(self):
        report = basic_audit("слово " * 360)
        self.assertIn("350+", report)

    def test_theme_bank(self):
        bank = ThemeBank()
        self.assertEqual(len(bank.sections()), 3)
        topic = bank.random_topic(bank.sections()[0])
        self.assertTrue(topic["text"])

    def test_literature_lookup(self):
        library = LiteratureLibrary()
        results = library.search("совесть Раскольников")
        self.assertTrue(results)
        self.assertEqual(results[0]["title"], "Преступление и наказание")

    def test_private_think_channel_is_not_shown(self):
        output = clean_model_output("<think>скрытый черновой анализ</think>\nОтвет ученику.<|im_end|>")
        self.assertEqual(output, "Ответ ученику.")


if __name__ == "__main__":
    unittest.main()
