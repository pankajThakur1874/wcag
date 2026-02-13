"""Media Accessibility Scanner - WCAG 1.2.1, 1.2.2 (Level A)

Enhanced scanner for audio/video media accessibility. Checks for:
- Captions for prerecorded video
- Transcripts for audio-only content
- Text alternatives for media
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import Page
import re

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MediaAccessibilityScanner(BaseScanner):
    """Scanner for media accessibility (enhanced)."""

    name = "media-accessibility"
    version = "2.0.0"

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
                return await self._check_media_accessibility(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_media_accessibility(self, page: Page) -> list[Violation]:
        """Run media accessibility checks."""
        violations = []

        # This scanner checks 5 rules
        self._rules_checked = 5

        issues = await page.evaluate("""
            () => {
                const issues = [];

                // Helper function
                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        return el.tagName.toLowerCase() + '.' + classes[0];
                    }
                    return el.tagName.toLowerCase();
                }

                // Helper: Check for nearby transcript link
                function hasTranscriptLink(element, radius = 3) {
                    let current = element;
                    let levelsUp = 0;

                    // Search up the DOM tree
                    while (current && levelsUp < radius) {
                        // Search within this level
                        const text = current.textContent?.toLowerCase() || '';
                        const links = current.querySelectorAll('a');

                        for (const link of links) {
                            const linkText = link.textContent.toLowerCase();
                            const href = link.href.toLowerCase();

                            if (linkText.includes('transcript') ||
                                linkText.includes('text version') ||
                                href.includes('transcript')) {
                                return { found: true, link: link.outerHTML.substring(0, 200) };
                            }
                        }

                        // Check for download/view links
                        for (const link of links) {
                            const href = link.href.toLowerCase();
                            if (href.endsWith('.txt') || href.endsWith('.pdf') ||
                                href.endsWith('.doc') || href.endsWith('.docx')) {
                                return { found: true, link: link.outerHTML.substring(0, 200), type: 'document' };
                            }
                        }

                        current = current.parentElement;
                        levelsUp++;
                    }

                    return { found: false };
                }

                // Helper: Check for caption controls
                function hasCaptionControls(element) {
                    // Check video element attributes
                    const tracks = element.querySelectorAll('track[kind="captions"], track[kind="subtitles"]');
                    if (tracks.length > 0) {
                        return { found: true, type: 'track-element', count: tracks.length };
                    }

                    // Check for caption button in controls
                    const parent = element.closest('div') || element.parentElement;
                    if (parent) {
                        const ccButtons = parent.querySelectorAll(
                            '[class*="caption"], [class*="subtitle"], [class*="cc"], ' +
                            '[aria-label*="caption"], [aria-label*="subtitle"]'
                        );

                        if (ccButtons.length > 0) {
                            return { found: true, type: 'caption-button', count: ccButtons.length };
                        }
                    }

                    return { found: false };
                }

                // 1. Check video elements for captions (1.2.2)
                const videos = document.querySelectorAll('video');

                for (const video of videos) {
                    const captionCheck = hasCaptionControls(video);
                    const transcriptCheck = hasTranscriptLink(video);

                    // Get video source info
                    const src = video.src || video.querySelector('source')?.src || '';
                    const isYouTube = src.includes('youtube') || src.includes('youtu.be');
                    const isVimeo = src.includes('vimeo');

                    // YouTube and Vimeo often have built-in captions
                    if (isYouTube || isVimeo) {
                        // Check if embed has captions enabled
                        const hasCCParam = src.includes('cc_load_policy=1') || src.includes('cc=1');

                        if (!hasCCParam && !captionCheck.found) {
                            issues.push({
                                type: 'video-embedded-no-captions-param',
                                element: video.outerHTML.substring(0, 300),
                                selector: getSelector(video),
                                src: src.substring(0, 200),
                                platform: isYouTube ? 'YouTube' : 'Vimeo',
                                wcag: '1.2.2'
                            });
                        }
                    } else {
                        // Self-hosted or other video
                        if (!captionCheck.found) {
                            // No captions detected
                            if (!transcriptCheck.found) {
                                // No captions AND no transcript
                                issues.push({
                                    type: 'video-no-captions-or-transcript',
                                    element: video.outerHTML.substring(0, 300),
                                    selector: getSelector(video),
                                    src: src.substring(0, 200),
                                    wcag: '1.2.2'
                                });
                            } else {
                                // Has transcript but no captions
                                issues.push({
                                    type: 'video-no-captions-has-transcript',
                                    element: video.outerHTML.substring(0, 300),
                                    selector: getSelector(video),
                                    src: src.substring(0, 200),
                                    transcript: transcriptCheck.link,
                                    wcag: '1.2.2'
                                });
                            }
                        }
                    }

                    // Check for audio description (visual info)
                    const hasAudioDescTrack = video.querySelector('track[kind="descriptions"]');
                    if (!hasAudioDescTrack && !transcriptCheck.found) {
                        // Note: This is 1.2.3 (Level A) but we'll flag as informational
                        issues.push({
                            type: 'video-no-audio-description',
                            element: video.outerHTML.substring(0, 300),
                            selector: getSelector(video),
                            severity: 'informational',
                            wcag: '1.2.3'
                        });
                    }
                }

                // 2. Check audio elements for transcripts (1.2.1)
                const audios = document.querySelectorAll('audio');

                for (const audio of audios) {
                    const transcriptCheck = hasTranscriptLink(audio);

                    if (!transcriptCheck.found) {
                        const src = audio.src || audio.querySelector('source')?.src || '';

                        issues.push({
                            type: 'audio-no-transcript',
                            element: audio.outerHTML.substring(0, 300),
                            selector: getSelector(audio),
                            src: src.substring(0, 200),
                            wcag: '1.2.1'
                        });
                    }
                }

                // 3. Check embedded media (iframe)
                const iframes = document.querySelectorAll('iframe[src*="youtube"], iframe[src*="vimeo"], iframe[src*="dailymotion"]');

                for (const iframe of iframes) {
                    const src = iframe.src;
                    const transcriptCheck = hasTranscriptLink(iframe);

                    // Check if captions are enabled in embed URL
                    const hasCCParam = src.includes('cc_load_policy=1') ||
                                      src.includes('cc=1') ||
                                      src.includes('captions=1');

                    if (!hasCCParam) {
                        issues.push({
                            type: 'iframe-video-no-caption-param',
                            element: iframe.outerHTML.substring(0, 300),
                            selector: getSelector(iframe),
                            src: src.substring(0, 200),
                            hasTranscript: transcriptCheck.found,
                            wcag: '1.2.2'
                        });
                    }
                }

                // 4. Check for media controls accessibility
                for (const video of videos) {
                    const controls = video.hasAttribute('controls');
                    const customControls = video.parentElement?.querySelector('[class*="control"]');

                    if (!controls && !customControls) {
                        issues.push({
                            type: 'video-no-controls',
                            element: video.outerHTML.substring(0, 300),
                            selector: getSelector(video),
                            wcag: '2.1.1',  // Keyboard accessible
                            severity: 'moderate'
                        });
                    } else if (customControls) {
                        // Check if custom controls are keyboard accessible
                        const buttons = customControls.querySelectorAll('button, [role="button"]');
                        let inaccessibleControls = 0;

                        for (const btn of buttons) {
                            if (!btn.hasAttribute('tabindex') && btn.tabIndex === -1) {
                                inaccessibleControls++;
                            }
                        }

                        if (inaccessibleControls > 0) {
                            issues.push({
                                type: 'video-controls-not-keyboard-accessible',
                                element: customControls.outerHTML.substring(0, 300),
                                selector: getSelector(customControls),
                                inaccessibleCount: inaccessibleControls,
                                wcag: '2.1.1'
                            });
                        }
                    }
                }

                // 5. Check for autoplay (should have controls to pause - 1.4.2)
                const autoplayVideos = document.querySelectorAll('video[autoplay], audio[autoplay]');

                for (const media of autoplayVideos) {
                    const hasControls = media.hasAttribute('controls');
                    const duration = media.duration;

                    // If autoplay and longer than 3 seconds, must have controls
                    if (!hasControls && (duration > 3 || isNaN(duration))) {
                        issues.push({
                            type: 'autoplay-no-controls',
                            element: media.outerHTML.substring(0, 300),
                            selector: getSelector(media),
                            tagName: media.tagName.toLowerCase(),
                            wcag: '1.4.2'
                        });
                    }
                }

                return issues;
            }
        """)

        # Convert issues to violations
        rule_types_failed = set()
        for issue in issues:
            # Skip informational issues
            if issue.get("severity") == "informational":
                continue

            violation = self._create_violation(issue)
            if violation:
                violations.append(violation)
                rule_types_failed.add(issue.get("wcag"))

        # Update rules failed count
        self._rules_failed = len(rule_types_failed)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    def _create_violation(self, issue: dict) -> Optional[Violation]:
        """Create violation from issue data."""
        issue_type = issue.get("type")

        violation_configs = {
            "video-no-captions-or-transcript": {
                "id": "media-video-no-captions",
                "rule_id": "captions-prerecorded",
                "wcag": ["1.2.2"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": "Video has no captions or transcript for deaf/hard-of-hearing users",
                "help": "Add <track kind='captions'> element or provide link to transcript. WebVTT format recommended."
            },
            "video-no-captions-has-transcript": {
                "id": "media-video-no-captions-alt",
                "rule_id": "captions-prerecorded",
                "wcag": ["1.2.2"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Video has transcript but no synchronized captions",
                "help": "While transcript exists, synchronized captions are preferred. Add <track kind='captions'> for better UX."
            },
            "video-embedded-no-captions-param": {
                "id": "media-embed-no-cc",
                "rule_id": "captions-prerecorded",
                "wcag": ["1.2.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"{issue.get('platform')} embed without captions parameter enabled",
                "help": "Add cc_load_policy=1 to YouTube URLs or enable captions in embed settings"
            },
            "audio-no-transcript": {
                "id": "media-audio-no-transcript",
                "rule_id": "audio-only-prerecorded",
                "wcag": ["1.2.1"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": "Audio content has no text transcript",
                "help": "Provide link to text transcript near audio element. Include speaker identification and important sounds."
            },
            "iframe-video-no-caption-param": {
                "id": "media-iframe-no-cc",
                "rule_id": "captions-prerecorded",
                "wcag": ["1.2.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS if not issue.get("hasTranscript") else Impact.MODERATE,
                "description": "Embedded video iframe without caption parameter enabled",
                "help": "Enable captions in embed URL (e.g., add cc_load_policy=1 for YouTube)"
            },
            "video-no-controls": {
                "id": "media-no-controls",
                "rule_id": "keyboard-accessible",
                "wcag": ["2.1.1"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Video has no controls, making it inaccessible to keyboard users",
                "help": "Add controls attribute to video element, or provide accessible custom controls"
            },
            "video-controls-not-keyboard-accessible": {
                "id": "media-controls-not-keyboard",
                "rule_id": "keyboard-accessible",
                "wcag": ["2.1.1"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Video has custom controls with {issue.get('inaccessibleCount')} inaccessible buttons",
                "help": "Ensure all custom control buttons are keyboard accessible with proper tabindex and key handlers"
            },
            "autoplay-no-controls": {
                "id": "media-autoplay-no-pause",
                "rule_id": "audio-control",
                "wcag": ["1.4.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Autoplaying {issue.get('tagName')} without controls to pause",
                "help": "Add controls attribute or provide mechanism to pause/stop autoplay media"
            },
            "video-no-audio-description": {
                "id": "media-no-audio-desc",
                "rule_id": "audio-description-prerecorded",
                "wcag": ["1.2.3"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Video may need audio description for visual content",
                "help": "Add <track kind='descriptions'> for visual info not in audio, or provide transcript describing visual elements"
            }
        }

        config = violation_configs.get(issue_type)
        if not config:
            return None

        # Build detailed help text
        help_text = config["help"]
        if issue.get("src"):
            help_text += f" (Source: {issue.get('src')[:100]})"

        return Violation(
            id=f"{config['id']}-{hash(issue.get('selector', '')) % 10000}",
            rule_id=config["rule_id"],
            wcag_criteria=config["wcag"],
            wcag_level=config["level"],
            impact=config["impact"],
            description=config["description"],
            help_text=help_text,
            help_url=f"https://www.w3.org/WAI/WCAG22/Understanding/{config['wcag'][0].replace('.', '')}.html",
            detected_by=["media-accessibility"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["media", "captions", "audio", "video", f"wcag{config['wcag'][0].replace('.', '')}"]
        )
