"""Detailed fix guides for common accessibility issues."""

from typing import Dict, Optional


# Rule type categorization
RULE_CATEGORIES = {
    # Images
    "image-alt": "Images & Media",
    "image-redundant-alt": "Images & Media",
    "object-alt": "Images & Media",
    "input-image-alt": "Images & Media",

    # Color & Contrast
    "color-contrast": "Color & Contrast",
    "color-contrast-enhanced": "Color & Contrast",
    "link-in-text-block": "Color & Contrast",

    # Forms
    "label": "Forms",
    "label-title-only": "Forms",
    "form-field-multiple-labels": "Forms",
    "input-button-name": "Forms",
    "select-name": "Forms",
    "aria-input-field-name": "Forms",

    # Headings
    "empty-heading": "Headings",
    "heading-order": "Headings",
    "p-as-heading": "Headings",

    # Links
    "link-name": "Links",
    "link-in-text-block": "Links",
    "identical-links-same-purpose": "Links",

    # ARIA
    "aria-allowed-attr": "ARIA",
    "aria-required-attr": "ARIA",
    "aria-valid-attr": "ARIA",
    "aria-valid-attr-value": "ARIA",
    "button-name": "ARIA",
    "aria-hidden-focus": "ARIA",

    # HTML Structure
    "html-has-lang": "HTML Structure",
    "html-lang-valid": "HTML Structure",
    "landmark-one-main": "HTML Structure",
    "region": "HTML Structure",
    "document-title": "HTML Structure",

    # Tables
    "table-duplicate-name": "Tables",
    "td-headers-attr": "Tables",
    "th-has-data-cells": "Tables",
    "table-fake-caption": "Tables",

    # Keyboard
    "tabindex": "Keyboard Navigation",
    "accesskeys": "Keyboard Navigation",
    "focus-order-semantics": "Keyboard Navigation",
}


def get_rule_category(rule_id: str) -> str:
    """Get category for a rule ID."""
    return RULE_CATEGORIES.get(rule_id, "Other")


# Detailed fix guides with code examples
FIX_GUIDES = {
    "image-alt": {
        "title": "Images must have alternate text",
        "why": "Screen readers need alt text to describe images to visually impaired users.",
        "how_to_fix": "Add an `alt` attribute to all `<img>` elements",
        "code_example": {
            "before": '<img src="logo.png">',
            "after": '<img src="logo.png" alt="Company Logo">',
        },
        "steps": [
            "Identify all images without alt attributes",
            "For decorative images, use `alt=\"\"`",
            "For informative images, describe what the image conveys",
            "For functional images (buttons), describe the action",
            "Keep alt text concise (under 150 characters)"
        ],
        "good_examples": [
            {
                "context": "Decorative image",
                "code": '<img src="divider.png" alt="">'
            },
            {
                "context": "Informative image",
                "code": '<img src="chart.png" alt="Sales increased 25% in Q4">'
            },
            {
                "context": "Linked image",
                "code": '<a href="/home"><img src="logo.png" alt="Go to homepage"></a>'
            }
        ]
    },

    "color-contrast": {
        "title": "Elements must have sufficient color contrast",
        "why": "Low contrast text is difficult to read for users with low vision or color blindness.",
        "how_to_fix": "Ensure text has a contrast ratio of at least 4.5:1 (AA) or 7:1 (AAA)",
        "code_example": {
            "before": '/* Text color #767676 on white background (2.9:1 ratio) */\n.low-contrast {\n  color: #767676;\n  background: #ffffff;\n}',
            "after": '/* Text color #595959 on white background (7:1 ratio) */\n.high-contrast {\n  color: #595959;\n  background: #ffffff;\n}',
        },
        "steps": [
            "Use a contrast checker tool (WebAIM, Chrome DevTools)",
            "Aim for 4.5:1 ratio for normal text (WCAG AA)",
            "Aim for 3:1 ratio for large text (18pt+ or 14pt+ bold)",
            "Darken text color or lighten background",
            "Test with actual users if possible"
        ],
        "tools": [
            "Chrome DevTools (Inspect > Accessibility panel)",
            "WebAIM Contrast Checker",
            "Axe DevTools browser extension"
        ]
    },

    "label": {
        "title": "Form elements must have labels",
        "why": "Screen readers need labels to tell users what information to enter in form fields.",
        "how_to_fix": "Associate every form input with a `<label>` element",
        "code_example": {
            "before": '<input type="text" name="email">',
            "after": '<label for="email">Email Address:</label>\n<input type="text" id="email" name="email">',
        },
        "steps": [
            "Add a unique `id` attribute to the input",
            "Create a `<label>` element with `for` attribute matching the input's id",
            "Ensure label text clearly describes the input's purpose",
            "Place label before or above the input (UX best practice)",
            "For hidden labels, use `aria-label` attribute"
        ],
        "good_examples": [
            {
                "context": "Text input",
                "code": '<label for="username">Username:</label>\n<input type="text" id="username" name="username">'
            },
            {
                "context": "Checkbox",
                "code": '<input type="checkbox" id="terms" name="terms">\n<label for="terms">I agree to the terms</label>'
            },
            {
                "context": "Hidden label (icon button)",
                "code": '<button aria-label="Search">\n  <svg>...</svg>\n</button>'
            }
        ]
    },

    "heading-order": {
        "title": "Heading levels should only increase by one",
        "why": "Skipping heading levels confuses screen reader users about content hierarchy.",
        "how_to_fix": "Use headings in sequential order: h1 → h2 → h3, don't skip levels",
        "code_example": {
            "before": '<h1>Page Title</h1>\n<h3>Skipped h2</h3>  <!-- Bad: skipped h2 -->',
            "after": '<h1>Page Title</h1>\n<h2>Section Title</h2>\n<h3>Subsection</h3>  <!-- Good: sequential -->',
        },
        "steps": [
            "Start with one h1 per page (usually the page title)",
            "Use h2 for main sections",
            "Use h3 for subsections within h2",
            "Never skip levels (h1 to h3)",
            "You can go backwards (h3 to h2 to start new section)"
        ]
    },

    "link-name": {
        "title": "Links must have discernible text",
        "why": "Screen readers need link text to tell users where the link goes.",
        "how_to_fix": "Ensure every link has visible or aria-labeled text",
        "code_example": {
            "before": '<a href="/next"><img src="arrow.png"></a>  <!-- No text -->',
            "after": '<a href="/next">\n  <img src="arrow.png" alt="Next page">\n</a>  <!-- Alt text provides link name -->',
        },
        "steps": [
            "Add visible text inside the link",
            "Or add alt text to images inside links",
            "Or use aria-label for icon-only links",
            "Avoid generic text like 'Click here' or 'Read more'",
            "Make link text describe the destination"
        ],
        "good_examples": [
            {
                "context": "Text link",
                "code": '<a href="/about">Learn about our company</a>'
            },
            {
                "context": "Image link",
                "code": '<a href="/profile">\n  <img src="avatar.png" alt="View your profile">\n</a>'
            },
            {
                "context": "Icon link",
                "code": '<a href="https://twitter.com" aria-label="Follow us on Twitter">\n  <svg>...</svg>\n</a>'
            }
        ]
    },

    "html-has-lang": {
        "title": "HTML element must have a lang attribute",
        "why": "Screen readers need to know the page language to pronounce content correctly.",
        "how_to_fix": "Add a lang attribute to the <html> element",
        "code_example": {
            "before": '<!DOCTYPE html>\n<html>\n  <head>...',
            "after": '<!DOCTYPE html>\n<html lang="en">\n  <head>...',
        },
        "steps": [
            "Add lang=\"en\" for English pages",
            "Use ISO 639-1 codes (en, es, fr, de, etc.)",
            "For regional variants, use lang=\"en-US\" or lang=\"en-GB\"",
            "For multilingual pages, use lang on specific sections"
        ]
    },

    "button-name": {
        "title": "Buttons must have discernible text",
        "why": "Screen readers need button text to tell users what the button does.",
        "how_to_fix": "Ensure every button has visible text or an aria-label",
        "code_example": {
            "before": '<button><svg>...</svg></button>  <!-- Icon only, no text -->',
            "after": '<button aria-label="Close dialog">\n  <svg>...</svg>\n</button>  <!-- Has aria-label -->',
        },
        "steps": [
            "Add visible text inside the button (preferred)",
            "Or add aria-label for icon-only buttons",
            "Make button text describe the action",
            "Avoid generic text like 'Submit' or 'Click'",
            "Use specific, actionable text like 'Save Changes' or 'Delete Account'"
        ]
    },

    "aria-required-attr": {
        "title": "ARIA role is missing required attributes",
        "why": "ARIA roles have required attributes that assistive technologies depend on.",
        "how_to_fix": "Add all required attributes for the ARIA role being used",
        "code_example": {
            "before": '<div role="checkbox">...</div>  <!-- Missing aria-checked -->',
            "after": '<div role="checkbox" aria-checked="false">...</div>  <!-- Has required attribute -->',
        },
        "steps": [
            "Check ARIA specification for required attributes",
            "Common examples:",
            "  - role='checkbox' requires aria-checked",
            "  - role='slider' requires aria-valuenow",
            "  - role='tab' requires aria-controls",
            "Use native HTML elements when possible (they have built-in semantics)"
        ]
    },

    "empty-heading": {
        "title": "Headings must not be empty",
        "why": "Empty headings provide no information and confuse screen reader users.",
        "how_to_fix": "Remove empty headings or add meaningful text",
        "code_example": {
            "before": '<h2></h2>  <!-- Empty heading -->',
            "after": '<h2>Products</h2>  <!-- Has meaningful text -->',
        },
        "steps": [
            "Remove the heading if it's not needed",
            "Add descriptive text that explains the section",
            "Don't use headings for styling (use CSS classes instead)",
            "If using an icon in the heading, add aria-label"
        ]
    },

    "document-title": {
        "title": "Documents must have a title element",
        "why": "Page titles help users understand what page they're on and appear in browser tabs and bookmarks.",
        "how_to_fix": "Add a descriptive <title> element in the <head>",
        "code_example": {
            "before": '<head>\n  <!-- No title -->\n</head>',
            "after": '<head>\n  <title>Products - Acme Corp</title>\n</head>',
        },
        "steps": [
            "Add <title> element inside <head>",
            "Use format: 'Page Name - Site Name'",
            "Make title descriptive and unique per page",
            "Keep under 60 characters for good display",
            "Update title when page content changes (SPAs)"
        ]
    }
}


def get_fix_guide(rule_id: str) -> Optional[Dict]:
    """Get detailed fix guide for a rule ID."""
    return FIX_GUIDES.get(rule_id)


def get_category_icon(category: str) -> str:
    """Get emoji icon for category."""
    icons = {
        "Images & Media": "🖼️",
        "Color & Contrast": "🎨",
        "Forms": "📝",
        "Headings": "📑",
        "Links": "🔗",
        "ARIA": "♿",
        "HTML Structure": "🏗️",
        "Tables": "📊",
        "Keyboard Navigation": "⌨️",
        "Other": "🔧"
    }
    return icons.get(category, "🔧")
