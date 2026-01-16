# Detailed Violation Display - Feature Documentation

## Overview

Completely redesigned HTML report violation display to show **comprehensive, actionable details** for each accessibility issue, matching professional accessibility audit report standards.

---

## What's New

### Before: Basic Violation Cards
```
Issue Card:
- Title + Impact badge
- Basic details
- Collapsible instances
- Generic fix guide
```

### After: Detailed Violation Display
```
🚨 Detailed Violations

rule-id IMPACT
Occurrences: X
Issue: [Description]
Solution: [Help text]

📍 Affected Elements (showing first Y of X):

Element 1:
  CSS Selector: [selector]
  HTML: [code snippet]
  ⚠ What's Wrong: [specific failure explanation]
  📋 Violation Details: [raw data - colors, ratios, etc.]

Element 2:
  [...]

📚 View Detailed Fix Guide (collapsible)
  - Why this matters
  - How to fix
  - Before/After examples
  - Step-by-step guide

WCAG info | Detected by | Category
```

---

## Key Features

### 1. **Clean Violation Header**
- Rule ID and Impact on same line (e.g., "aria-allowed-role MINOR")
- Immediate visibility of issue severity
- Monospace font for rule IDs

### 2. **Occurrence Count**
- Shows total number of affected elements
- Helps prioritize fixes by scale

### 3. **Clear Issue & Solution**
- Issue: What's wrong
- Solution: How to fix (high-level)
- Both highlighted in gray boxes for easy scanning

### 4. **Numbered Affected Elements**
- "Element 1", "Element 2", etc.
- Shows first 5 by default
- Each element in its own container with left border

### 5. **CSS Selector Display**
- Dark background for selector (like dev tools)
- Easy copy-paste for finding elements

### 6. **HTML Code Snippet**
- Syntax highlighted code block
- Shows actual HTML causing the issue
- Overflow scroll for long code

### 7. **What's Wrong Section** ⚠
- Red-tinted background (warning)
- Specific failure explanation for THIS element
- Shows Axe's detailed check messages

### 8. **Violation Details** 📋
- Yellow-tinted background (info)
- Raw data in JSON-like format
- Includes contrast ratios, colors, font sizes, etc.
- Especially useful for color-contrast issues

### 9. **Collapsible Fix Guide** 📚
- Detailed fix guide hidden by default
- Expandable for in-depth instructions
- Includes before/after code examples
- Step-by-step guide

### 10. **Footer Info**
- Category with icon (e.g., "🖼️ Images & Media")
- WCAG criteria badges (small)
- Detected by scanner name

---

## Visual Structure

```
┌─────────────────────────────────────────────────────┐
│ violation-card                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ aria-allowed-role        [MINOR]                │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ Occurrences: 2                                      │
│                                                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Issue: Ensure role attribute has...             │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Solution: ARIA role should be...                │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ ─────────────────────────────────────────────────── │
│                                                      │
│ 📍 Affected Elements (showing first 2 of 2):        │
│                                                      │
│ ┌───────────────────────────────────────────────┐   │
│ │ ▌ Element 1:                                  │   │
│ │ ▌                                             │   │
│ │ ▌ CSS Selector: .owl-prev                    │   │
│ │ ▌                                             │   │
│ │ ▌ HTML:                                       │   │
│ │ ▌ <button type="button" ...></button>        │   │
│ │ ▌                                             │   │
│ │ ▌ ⚠ What's Wrong:                            │   │
│ │ ▌ Fix any of the following:                  │   │
│ │ ▌ - ARIA role presentation is not...         │   │
│ └───────────────────────────────────────────────┘   │
│                                                      │
│ [Element 2...]                                       │
│                                                      │
│ ▼ 📚 View Detailed Fix Guide                        │
│                                                      │
│ ─────────────────────────────────────────────────── │
│ 🖼️ Images & Media │ WCAG 4.1.2 │ Detected by: axe  │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. **Backend Changes**

#### `scanner_v2/database/models.py`
Added new fields to `IssueInstance`:

```python
class IssueInstance(BaseModel):
    """Single instance of an issue."""

    selector: str
    html: Optional[str] = None
    screenshot_path: Optional[str] = None
    context: Optional[str] = None
    failure_summary: Optional[str] = None  # ← NEW: What's wrong
    data: Optional[str] = None             # ← NEW: Raw violation data
```

#### `scanner_v2/services/scanner_service.py`
Enhanced instance conversion to extract additional data:

```python
# Convert instances
instances = []
for instance in violation.instances:
    # Try to extract additional data if available
    instance_data = None
    if hasattr(instance, '__dict__'):
        # Extract non-standard fields as data
        extra_data = {}
        for key, value in instance.__dict__.items():
            if key not in ['html', 'selector', 'xpath', 'fix_suggestion'] and value is not None:
                extra_data[key] = str(value)

        if extra_data:
            import json
            instance_data = json.dumps(extra_data, indent=2)

    instances.append({
        "selector": instance.selector or "",
        "html": instance.html or "",
        "failure_summary": instance.fix_suggestion or "",
        "data": instance_data
    })
```

**What this does:**
- Extracts `fix_suggestion` → `failure_summary`
- Captures any extra fields (like contrast data) → `data` as JSON
- Handles Axe scanner's detailed node information

---

### 2. **Template Changes**

#### `scanner_v2/report_templates/html_report.jinja2`

**Replaced entire violation display section (lines 120-295):**

Key changes:
- Changed `<h2>Issues by Impact Level</h2>` → `<h2>🚨 Detailed Violations</h2>`
- Changed `.issue-card` → `.violation-card`
- Split display into clear sections:
  - violation-title (Rule ID + Impact badge)
  - violation-meta (Occurrences)
  - violation-issue (Issue description)
  - violation-solution (Solution)
  - affected-elements-header (Section header)
  - element-details (Each element)
    - element-number (Element 1, 2, etc.)
    - element-selector (CSS selector)
    - element-html (HTML code)
    - element-wrong (What's wrong section)
    - violation-details-data (Raw data)
  - fix-guide-collapsible (Expandable fix guide)
  - violation-footer (Category, WCAG, detected by)

**Template structure:**
```jinja2
{% for enhanced_issue in impact_issues %}
    <div class="violation-card">
        <!-- Title: rule_id + impact badge -->
        <div class="violation-title">
            <strong>{{ issue.rule_id }}</strong>
            <span class="impact-badge-inline">{{ issue.impact }}</span>
        </div>

        <!-- Meta: Occurrences -->
        <div class="violation-meta">
            <p><strong>Occurrences:</strong> {{ issue.instances|length }}</p>
        </div>

        <!-- Issue & Solution -->
        <div class="violation-issue">...</div>
        <div class="violation-solution">...</div>

        <!-- Affected Elements -->
        <div class="affected-elements-header">...</div>

        {% for instance in issue.instances[:5] %}
            <div class="element-details">
                <div class="element-number">Element {{ loop.index }}:</div>
                <div class="element-selector">...</div>
                <div class="element-html">...</div>

                {% if instance.failure_summary %}
                <div class="element-wrong">
                    <p>⚠ What's Wrong:</p>
                    <div class="wrong-details">{{ instance.failure_summary }}</div>
                </div>
                {% endif %}

                {% if instance.data %}
                <div class="violation-details-data">
                    <p>📋 Violation Details:</p>
                    <pre><code>{{ instance.data }}</code></pre>
                </div>
                {% endif %}
            </div>
        {% endfor %}

        <!-- Collapsible Fix Guide -->
        <details class="fix-guide-collapsible">...</details>

        <!-- Footer -->
        <div class="violation-footer">...</div>
    </div>
{% endfor %}
```

---

### 3. **CSS Changes**

#### `scanner_v2/report_templates/styles.css`

**Added 300+ lines of new styles (lines 1111-1428):**

Key CSS classes:

```css
/* Violation Card Container */
.violation-card {
    background: #ffffff;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-sm);
}

/* Violation Title (Rule ID + Impact) */
.violation-title {
    display: flex;
    align-items: center;
    gap: 1rem;
    border-bottom: 2px solid var(--color-border);
}

.violation-title strong {
    font-size: 1.25rem;
    font-weight: 700;
    font-family: var(--font-mono);
}

/* Impact Badge Inline */
.impact-badge-inline {
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
}

/* Impact Colors */
.impact-badge-inline.impact-critical { background: #fee2e2; color: #dc2626; }
.impact-badge-inline.impact-serious  { background: #ffedd5; color: #f97316; }
.impact-badge-inline.impact-moderate { background: #fef3c7; color: #d97706; }
.impact-badge-inline.impact-minor    { background: #dbeafe; color: #2563eb; }

/* Element Details Container */
.element-details {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid var(--color-primary);
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 1.25rem;
}

/* What's Wrong Section (Red warning) */
.element-wrong {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    padding: 0.75rem;
}

/* Violation Details Data (Yellow info) */
.violation-details-data {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 6px;
    padding: 0.75rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .violation-title { flex-direction: column; }
    .violation-footer { flex-direction: column; }
}
```

**Color Scheme:**
- **Headers**: Blue border (primary color)
- **Issue/Solution boxes**: Light gray background
- **Element containers**: Light blue-gray with blue left border
- **What's Wrong**: Red tinted (warning)
- **Violation Details**: Yellow tinted (info)
- **Fix Guide**: Light gray with border

---

## Example Output

### Color Contrast Violation

```
color-contrast-enhanced SERIOUS

Occurrences: 36

Issue: Ensure the contrast between foreground and background colors meets
       WCAG 2 AAA enhanced contrast ratio thresholds

Solution: Elements must meet enhanced color contrast ratio thresholds

📍 Affected Elements (showing first 5 of 36):

Element 1:
CSS Selector: .gifts-icon-header.gifts-buy-button[aria-label="Air India Gift Cards"] > p

HTML:
<p style="margin: 0px 0px 0px 0px;">Gift Cards</p>

⚠ What's Wrong:
Fix any of the following:
Element has insufficient color contrast of 4.84 (foreground color: #da0e29,
background color: #f7f8f8, font size: 9.0pt (12px), font weight: normal).
Expected contrast ratio of 7:1

📋 Violation Details:
{
  "fgColor": "#da0e29",
  "bgColor": "#f7f8f8",
  "contrastRatio": "4.84",
  "fontSize": "9.0pt (12px)",
  "fontWeight": "normal",
  "expectedContrastRatio": "7:1"
}

Element 2:
[...]

📚 View Detailed Fix Guide
```

---

## Benefits

### For Developers
✅ **Faster debugging** - See exact selector and HTML
✅ **Clear failures** - "What's Wrong" explains the specific issue
✅ **Raw data** - Contrast ratios, colors, sizes visible at a glance
✅ **Copy-paste ready** - Selectors easy to copy for browser DevTools

### For QA/Testers
✅ **Numbered elements** - Easy reference in bug reports
✅ **Occurrence counts** - Quick assessment of scale
✅ **Clear solutions** - Know what to verify after fix

### For Project Managers
✅ **Professional format** - Matches industry audit reports
✅ **Visual hierarchy** - Easy to scan and understand
✅ **Detailed but organized** - Comprehensive without overwhelming

### For Clients
✅ **Transparency** - See exactly what's wrong
✅ **Actionable** - Clear path to compliance
✅ **Professional** - Audit-quality reports

---

## Testing Checklist

### Visual Testing
- [ ] Rule ID and impact badge on same line
- [ ] Occurrence count displays correctly
- [ ] Issue and Solution in gray boxes
- [ ] Elements numbered 1, 2, 3...
- [ ] CSS selector has dark background
- [ ] HTML code is syntax highlighted
- [ ] "What's Wrong" has red background
- [ ] "Violation Details" has yellow background
- [ ] Fix guide is collapsible (closed by default)
- [ ] Footer shows category, WCAG, detected by

### Content Testing
- [ ] failure_summary displays in "What's Wrong"
- [ ] data displays in "Violation Details" (when available)
- [ ] Shows max 5 elements per violation
- [ ] Occurrence count matches actual instances
- [ ] Contrast violations show colors and ratios
- [ ] ARIA violations show specific failure messages

### Responsive Testing
- [ ] Layout works on mobile (< 768px)
- [ ] Code blocks scroll horizontally
- [ ] Violation title stacks on mobile
- [ ] Footer stacks on mobile

---

## Known Issues & Limitations

### 1. **Data Field Availability**
**Issue:** Not all scanners provide detailed data
**Impact:** "Violation Details" section may be empty for some issues
**Solution:** Axe scanner provides the most detailed data; use Axe for comprehensive reports

### 2. **First 5 Elements Only**
**Issue:** Only shows first 5 affected elements
**Impact:** Large-scale issues may hide many instances
**Workaround:** Occurrence count shows total; fix first 5 and re-scan

### 3. **Long Selectors**
**Issue:** Very long CSS selectors may overflow
**Solution:** CSS has overflow-x: auto for horizontal scroll

### 4. **HTML Escaping**
**Issue:** HTML snippets must be properly escaped
**Solution:** Jinja2 auto-escapes by default, but verify for XSS

---

## Future Enhancements

### 1. **Interactive Elements**
- Copy button for selectors
- "Show in page" link to highlight element
- Expand/collapse all fix guides

### 2. **Severity Indicators**
- Visual severity scale (1-5 stars)
- Priority sorting by impact + occurrence count
- Estimated fix time per violation

### 3. **Fix Status Tracking**
- Checkbox to mark as fixed
- Comment field for notes
- Progress bar for total fixes

### 4. **Enhanced Data Display**
- Color swatches for contrast violations
- Visual contrast ratio gauge
- Font size comparison charts

### 5. **Export Options**
- Export specific violations to CSV
- Generate Jira/GitHub issues
- PDF export with violation details

---

## Files Modified

| File | Lines Changed | Purpose |
|------|--------------|---------|
| `scanner_v2/database/models.py` | 228-236 | Added failure_summary and data fields |
| `scanner_v2/services/scanner_service.py` | 332-353 | Enhanced instance data extraction |
| `scanner_v2/report_templates/html_report.jinja2` | 120-295 | Complete violation display redesign |
| `scanner_v2/report_templates/styles.css` | 1111-1428 | Added 300+ lines of new styles |

**Total:** 4 files, ~400 lines changed

---

## Conclusion

The detailed violation display transforms the HTML report from a basic issue list into a **professional, audit-quality accessibility report**. Each violation now provides:

1. ✅ Clear identification (Rule ID + Impact)
2. ✅ Scale understanding (Occurrence count)
3. ✅ Issue explanation (What's wrong)
4. ✅ Solution guidance (How to fix)
5. ✅ Specific examples (Numbered elements)
6. ✅ Debug information (Selector + HTML)
7. ✅ Failure details (What's wrong section)
8. ✅ Raw data (Contrast ratios, colors, etc.)
9. ✅ In-depth guide (Collapsible fix guide)
10. ✅ Context (Category, WCAG, scanner)

This level of detail matches industry-leading accessibility audit reports from firms like Deque, Level Access, and TPGi.

---

**Feature Status:** ✅ Complete
**Report Generated:** 2026-01-16
**Files Modified:** 4
**Lines Added:** ~400
**Testing Status:** Pending user validation
