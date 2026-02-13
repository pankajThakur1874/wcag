"""Readability scanner - checks content reading level and complexity."""

import re
from typing import Optional
from bs4 import BeautifulSoup

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReadabilityScanner(BaseScanner):
    """Scanner for content readability issues."""

    name = "readability"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check content readability.

        Args:
            url: URL to scan
            html_content: Pre-fetched HTML content

        Returns:
            List of violations
        """
        if html_content is None:
            if self._browser_manager is None:
                self._browser_manager = BrowserManager()
                await self._browser_manager.start()

            try:
                html_content = await self._browser_manager.get_page_content(url)
            finally:
                if self._owns_browser and self._browser_manager:
                    await self._browser_manager.stop()
                    self._browser_manager = None

        return self._analyze_readability(html_content)

    def _analyze_readability(self, html_content: str) -> list[Violation]:
        """Analyze content readability."""
        violations = []

        # This scanner checks 6 rules
        self._rules_checked = 6

        soup = BeautifulSoup(html_content, "lxml")

        # Extract main content text (skip nav, footer, etc.)
        # Remove script, style, nav, footer, header elements
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # Get main content
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if not main:
            return violations

        text = main.get_text(separator=' ', strip=True)

        # Clean text
        text = re.sub(r'\s+', ' ', text)

        if len(text) < 100:
            # Not enough content to analyze
            self._rules_passed = self._rules_checked
            return violations

        rule_failures = set()

        # Calculate readability metrics
        sentences = self._count_sentences(text)
        words = self._count_words(text)
        syllables = self._count_syllables(text)
        complex_words = self._count_complex_words(text)

        if sentences == 0 or words == 0:
            self._rules_passed = self._rules_checked
            return violations

        # Calculate Flesch-Kincaid Grade Level
        # FK = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        avg_words_per_sentence = words / sentences
        avg_syllables_per_word = syllables / words
        fk_grade = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59

        # Calculate Flesch Reading Ease
        # FRE = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        fre_score = 206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_syllables_per_word

        # Calculate percentage of complex words
        complex_word_pct = (complex_words / words) * 100 if words > 0 else 0

        # Rule 1: Check Flesch-Kincaid Grade Level (WCAG recommends lower secondary education ~8th grade)
        if fk_grade > 12:
            rule_failures.add("reading-level-high")
            violations.append(Violation(
                id="readability-grade-level",
                rule_id="reading-level",
                wcag_criteria=["3.1.5"],
                wcag_level=WCAGLevel.AAA,
                impact=Impact.MODERATE,
                description=f"Content reading level is grade {fk_grade:.1f} (recommended: grade 8 or lower)",
                help_text="Simplify language for broader accessibility. WCAG recommends content readable at lower secondary education level.",
                detected_by=["readability"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion="Use shorter sentences, simpler words, and avoid jargon"
                )],
                tags=["readability", "wcag3.1.5"]
            ))
        elif fk_grade > 9:
            rule_failures.add("reading-level-moderate")
            violations.append(Violation(
                id="readability-grade-moderate",
                rule_id="reading-level",
                wcag_criteria=["3.1.5"],
                wcag_level=WCAGLevel.AAA,
                impact=Impact.MINOR,
                description=f"Content reading level is grade {fk_grade:.1f} (recommended: grade 8 or lower)",
                help_text="Consider simplifying language for better accessibility.",
                detected_by=["readability"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion="Consider using simpler vocabulary and shorter sentences"
                )],
                tags=["readability", "wcag3.1.5"]
            ))

        # Rule 2: Check for very long sentences
        long_sentences = self._find_long_sentences(text)
        if long_sentences:
            rule_failures.add("long-sentences")
            violations.append(Violation(
                id="readability-long-sentences",
                rule_id="sentence-length",
                wcag_criteria=["3.1.5"],
                wcag_level=WCAGLevel.AAA,
                impact=Impact.MINOR,
                description=f"Found {len(long_sentences)} sentences with more than 25 words",
                help_text="Long sentences are harder to understand. Break them into shorter sentences.",
                detected_by=["readability"],
                instances=[ViolationInstance(
                    html=f"<p>{long_sentences[0][:200]}...</p>" if long_sentences else "",
                    selector="body",
                    fix_suggestion="Break long sentences into multiple shorter sentences"
                )],
                tags=["readability", "wcag3.1.5"]
            ))

        # Rule 3: Check for high percentage of complex words
        if complex_word_pct > 20:
            rule_failures.add("complex-words")
            violations.append(Violation(
                id="readability-complex-words",
                rule_id="word-complexity",
                wcag_criteria=["3.1.5"],
                wcag_level=WCAGLevel.AAA,
                impact=Impact.MINOR,
                description=f"{complex_word_pct:.1f}% of words are complex (3+ syllables)",
                help_text="Use simpler words where possible to improve readability.",
                detected_by=["readability"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion="Replace complex words with simpler alternatives"
                )],
                tags=["readability", "wcag3.1.5"]
            ))

        # Rule 4: Check for passive voice (simplified check)
        passive_count = self._count_passive_voice(text)
        passive_pct = (passive_count / sentences) * 100 if sentences > 0 else 0
        if passive_pct > 30:
            rule_failures.add("passive-voice")
            violations.append(Violation(
                id="readability-passive-voice",
                rule_id="passive-voice",
                wcag_criteria=["3.1.5"],
                wcag_level=WCAGLevel.AAA,
                impact=Impact.MINOR,
                description=f"High use of passive voice ({passive_pct:.1f}% of sentences)",
                help_text="Active voice is generally easier to understand than passive voice.",
                detected_by=["readability"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion="Rewrite passive sentences in active voice"
                )],
                tags=["readability", "wcag3.1.5"]
            ))

        # Rule 5: Check for jargon and abbreviations without definitions
        undefined_abbrs = self._find_undefined_abbreviations(soup)
        if undefined_abbrs:
            rule_failures.add("undefined-abbreviations")
            violations.append(Violation(
                id="readability-abbreviations",
                rule_id="abbreviation-expansion",
                wcag_criteria=["3.1.4"],
                wcag_level=WCAGLevel.AAA,
                impact=Impact.MODERATE,
                description=f"Found {len(undefined_abbrs)} abbreviations without definitions: {', '.join(undefined_abbrs[:5])}",
                help_text="Define abbreviations on first use using <abbr> tag with title attribute.",
                detected_by=["readability"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion=f"Add <abbr title='...'>ABBR</abbr> for: {', '.join(undefined_abbrs[:3])}"
                )],
                tags=["readability", "wcag3.1.4"]
            ))

        # Rule 6: Check paragraph length
        long_paragraphs = soup.find_all('p', string=lambda t: t and len(t.split()) > 150)
        if long_paragraphs:
            rule_failures.add("long-paragraphs")
            violations.append(Violation(
                id="readability-long-paragraphs",
                rule_id="paragraph-length",
                wcag_criteria=["3.1.5"],
                wcag_level=WCAGLevel.AAA,
                impact=Impact.MINOR,
                description=f"Found {len(long_paragraphs)} paragraphs with more than 150 words",
                help_text="Break long paragraphs into shorter ones for better readability.",
                detected_by=["readability"],
                instances=[ViolationInstance(
                    html=str(long_paragraphs[0])[:200] + "..." if long_paragraphs else "",
                    selector="p",
                    fix_suggestion="Break into multiple paragraphs"
                )],
                tags=["readability", "wcag3.1.5"]
            ))

        self._rules_failed = len(rule_failures)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        return len(words)

    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        total = 0
        for word in words:
            total += self._syllables_in_word(word)
        return total

    def _syllables_in_word(self, word: str) -> int:
        """Estimate syllables in a word."""
        word = word.lower()
        if len(word) <= 3:
            return 1

        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Adjust for silent e
        if word.endswith('e'):
            count -= 1

        # Adjust for -le endings
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1

        return max(1, count)

    def _count_complex_words(self, text: str) -> int:
        """Count words with 3+ syllables."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return sum(1 for w in words if self._syllables_in_word(w) >= 3)

    def _find_long_sentences(self, text: str, max_words: int = 25) -> list[str]:
        """Find sentences with more than max_words words."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences
                if s.strip() and len(s.split()) > max_words]

    def _count_passive_voice(self, text: str) -> int:
        """Estimate passive voice usage (simplified)."""
        # Look for common passive patterns: "was/were/is/are/been + past participle"
        passive_patterns = [
            r'\b(was|were|is|are|been|being)\s+\w+ed\b',
            r'\b(was|were|is|are|been|being)\s+\w+en\b',
        ]
        count = 0
        for pattern in passive_patterns:
            count += len(re.findall(pattern, text.lower()))
        return count

    def _find_undefined_abbreviations(self, soup: BeautifulSoup) -> list[str]:
        """Find abbreviations that aren't defined with <abbr> tag."""
        text = soup.get_text()

        # Find all caps abbreviations (2-5 letters)
        abbreviations = set(re.findall(r'\b[A-Z]{2,5}\b', text))

        # Common abbreviations that don't need definitions
        common = {'USA', 'UK', 'EU', 'CEO', 'FAQ', 'PDF', 'HTML', 'CSS', 'URL', 'API'}
        abbreviations -= common

        # Find defined abbreviations
        defined = set()
        for abbr in soup.find_all('abbr'):
            if abbr.get('title'):
                defined.add(abbr.get_text().upper())

        # Return undefined abbreviations
        return list(abbreviations - defined)[:10]
