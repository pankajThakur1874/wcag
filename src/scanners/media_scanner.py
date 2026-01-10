"""Media accessibility scanner - checks video and audio accessibility."""

from typing import Optional
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MediaScanner(BaseScanner):
    """Scanner for video and audio accessibility issues."""

    name = "media"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check media accessibility.

        Args:
            url: URL to scan
            html_content: Ignored, needs live page

        Returns:
            List of violations
        """
        if self._browser_manager is None:
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

        try:
            async with self._browser_manager.get_page(url) as page:
                return await self._check_media(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_media(self, page: Page) -> list[Violation]:
        """Run media accessibility checks."""
        violations = []

        # This scanner checks 8 rules
        self._rules_checked = 8

        media_data = await page.evaluate("""
            () => {
                const results = {
                    videos: [],
                    audios: [],
                    iframes: [],
                    embeds: []
                };

                // Check video elements
                const videos = document.querySelectorAll('video');
                for (const video of videos) {
                    const tracks = video.querySelectorAll('track');
                    const hasCaptions = Array.from(tracks).some(t =>
                        t.kind === 'captions' || t.kind === 'subtitles'
                    );
                    const hasDescriptions = Array.from(tracks).some(t =>
                        t.kind === 'descriptions'
                    );

                    results.videos.push({
                        src: video.src || video.querySelector('source')?.src || '',
                        hasCaptions: hasCaptions,
                        hasDescriptions: hasDescriptions,
                        hasControls: video.hasAttribute('controls'),
                        autoplay: video.hasAttribute('autoplay'),
                        muted: video.hasAttribute('muted'),
                        loop: video.hasAttribute('loop'),
                        trackCount: tracks.length,
                        html: video.outerHTML.substring(0, 300),
                        selector: getSelector(video)
                    });
                }

                // Check audio elements
                const audios = document.querySelectorAll('audio');
                for (const audio of audios) {
                    results.audios.push({
                        src: audio.src || audio.querySelector('source')?.src || '',
                        hasControls: audio.hasAttribute('controls'),
                        autoplay: audio.hasAttribute('autoplay'),
                        loop: audio.hasAttribute('loop'),
                        html: audio.outerHTML.substring(0, 300),
                        selector: getSelector(audio)
                    });
                }

                // Check iframes (for embedded videos like YouTube, Vimeo)
                const iframes = document.querySelectorAll('iframe');
                for (const iframe of iframes) {
                    const src = iframe.src || '';
                    const isVideo = src.includes('youtube') ||
                                   src.includes('vimeo') ||
                                   src.includes('dailymotion') ||
                                   src.includes('wistia') ||
                                   src.includes('video');

                    if (isVideo) {
                        results.iframes.push({
                            src: src,
                            title: iframe.getAttribute('title') || '',
                            hasTitle: !!iframe.getAttribute('title'),
                            html: iframe.outerHTML.substring(0, 300),
                            selector: getSelector(iframe)
                        });
                    }
                }

                // Check embed/object elements
                const embeds = document.querySelectorAll('embed, object');
                for (const embed of embeds) {
                    const type = embed.getAttribute('type') || '';
                    const src = embed.getAttribute('src') || embed.getAttribute('data') || '';
                    if (type.includes('video') || type.includes('audio') ||
                        src.includes('video') || src.includes('.mp4') || src.includes('.mp3')) {
                        results.embeds.push({
                            src: src,
                            type: type,
                            html: embed.outerHTML.substring(0, 300),
                            selector: getSelector(embed)
                        });
                    }
                }

                return results;

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        return el.tagName.toLowerCase() + '.' + el.className.split(' ')[0];
                    }
                    return el.tagName.toLowerCase();
                }
            }
        """)

        rule_failures = set()

        # Check videos
        for video in media_data.get("videos", []):
            # Rule 1: Video without captions
            if not video["hasCaptions"]:
                rule_failures.add("video-no-captions")
                violations.append(Violation(
                    id=f"video-no-captions-{hash(video['selector']) % 10000}",
                    rule_id="video-captions",
                    wcag_criteria=["1.2.2", "1.2.4"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.CRITICAL,
                    description="Video does not have captions",
                    help_text="Add <track kind='captions'> element with synchronized captions for deaf/hard of hearing users.",
                    detected_by=["media"],
                    instances=[ViolationInstance(
                        html=video["html"],
                        selector=video["selector"],
                        fix_suggestion="Add <track kind='captions' src='captions.vtt' srclang='en' label='English'>"
                    )],
                    tags=["video", "captions", "wcag1.2.2"]
                ))

            # Rule 2: Video without audio descriptions
            if not video["hasDescriptions"]:
                rule_failures.add("video-no-descriptions")
                violations.append(Violation(
                    id=f"video-no-desc-{hash(video['selector']) % 10000}",
                    rule_id="video-descriptions",
                    wcag_criteria=["1.2.3", "1.2.5"],
                    wcag_level=WCAGLevel.AA,
                    impact=Impact.SERIOUS,
                    description="Video does not have audio descriptions",
                    help_text="Add <track kind='descriptions'> for blind users or provide a text alternative.",
                    detected_by=["media"],
                    instances=[ViolationInstance(
                        html=video["html"],
                        selector=video["selector"],
                        fix_suggestion="Add audio descriptions track or provide text transcript"
                    )],
                    tags=["video", "descriptions", "wcag1.2.5"]
                ))

            # Rule 3: Video without controls
            if not video["hasControls"]:
                rule_failures.add("video-no-controls")
                violations.append(Violation(
                    id=f"video-no-controls-{hash(video['selector']) % 10000}",
                    rule_id="video-controls",
                    wcag_criteria=["2.1.1", "2.2.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description="Video does not have visible controls",
                    help_text="Add controls attribute to allow users to pause, stop, and control volume.",
                    detected_by=["media"],
                    instances=[ViolationInstance(
                        html=video["html"],
                        selector=video["selector"],
                        fix_suggestion="Add 'controls' attribute to the video element"
                    )],
                    tags=["video", "controls", "wcag2.1.1"]
                ))

            # Rule 4: Autoplay without mute
            if video["autoplay"] and not video["muted"]:
                rule_failures.add("video-autoplay")
                violations.append(Violation(
                    id=f"video-autoplay-{hash(video['selector']) % 10000}",
                    rule_id="video-autoplay-audio",
                    wcag_criteria=["1.4.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description="Video autoplays with sound",
                    help_text="Autoplaying media with sound can be disorienting. Add 'muted' attribute or avoid autoplay.",
                    detected_by=["media"],
                    instances=[ViolationInstance(
                        html=video["html"],
                        selector=video["selector"],
                        fix_suggestion="Add 'muted' attribute or remove 'autoplay'"
                    )],
                    tags=["video", "autoplay", "wcag1.4.2"]
                ))

        # Check audio elements
        for audio in media_data.get("audios", []):
            # Rule 5: Audio without controls
            if not audio["hasControls"]:
                rule_failures.add("audio-no-controls")
                violations.append(Violation(
                    id=f"audio-no-controls-{hash(audio['selector']) % 10000}",
                    rule_id="audio-controls",
                    wcag_criteria=["2.1.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description="Audio element does not have visible controls",
                    help_text="Add controls attribute to allow users to pause, stop, and control volume.",
                    detected_by=["media"],
                    instances=[ViolationInstance(
                        html=audio["html"],
                        selector=audio["selector"],
                        fix_suggestion="Add 'controls' attribute to the audio element"
                    )],
                    tags=["audio", "controls", "wcag2.1.1"]
                ))

            # Rule 6: Audio autoplay
            if audio["autoplay"]:
                rule_failures.add("audio-autoplay")
                violations.append(Violation(
                    id=f"audio-autoplay-{hash(audio['selector']) % 10000}",
                    rule_id="audio-autoplay",
                    wcag_criteria=["1.4.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description="Audio autoplays automatically",
                    help_text="Autoplaying audio can interfere with screen readers. Remove autoplay attribute.",
                    detected_by=["media"],
                    instances=[ViolationInstance(
                        html=audio["html"],
                        selector=audio["selector"],
                        fix_suggestion="Remove 'autoplay' attribute"
                    )],
                    tags=["audio", "autoplay", "wcag1.4.2"]
                ))

        # Check embedded videos (iframes)
        for iframe in media_data.get("iframes", []):
            # Rule 7: Embedded video without title
            if not iframe["hasTitle"]:
                rule_failures.add("iframe-no-title")
                violations.append(Violation(
                    id=f"iframe-video-no-title-{hash(iframe['selector']) % 10000}",
                    rule_id="iframe-title",
                    wcag_criteria=["4.1.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description="Embedded video iframe missing title attribute",
                    help_text="Add a title attribute describing the video content.",
                    detected_by=["media"],
                    instances=[ViolationInstance(
                        html=iframe["html"],
                        selector=iframe["selector"],
                        fix_suggestion="Add title attribute describing the video (e.g., title='Product demo video')"
                    )],
                    tags=["iframe", "video", "wcag4.1.2"]
                ))

        # Check embed/object elements
        for embed in media_data.get("embeds", []):
            # Rule 8: Embed without accessible alternative
            rule_failures.add("embed-no-alt")
            violations.append(Violation(
                id=f"embed-no-alt-{hash(embed['selector']) % 10000}",
                rule_id="embed-alternative",
                wcag_criteria=["1.2.1"],
                wcag_level=WCAGLevel.A,
                impact=Impact.SERIOUS,
                description="Embedded media may lack accessible alternative",
                help_text="Provide a text alternative or accessible version of embedded media content.",
                detected_by=["media"],
                instances=[ViolationInstance(
                    html=embed["html"],
                    selector=embed["selector"],
                    fix_suggestion="Provide transcript or accessible alternative for embedded media"
                )],
                tags=["embed", "alternative", "wcag1.2.1"]
            ))

        self._rules_failed = len(rule_failures)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations
