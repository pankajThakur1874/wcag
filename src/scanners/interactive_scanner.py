"""
Interactive Element Scanner

Discovers and tests interactive elements like:
- Tabs
- Accordions
- Modals/Dialogs
- Dropdown menus
- Expandable sections
"""

import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import Page, ElementHandle

from src.scanners.base import BaseScanner
from src.models import Violation, Impact, WCAGLevel, ViolationInstance
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InteractiveScanner(BaseScanner):
    """Scanner for interactive UI elements."""
    
    name = "interactive"
    description = "Tests tabs, modals, accordions, and other interactive elements"
    
    async def scan(self, page: Page, url: str) -> List[Violation]:
        """Scan interactive elements on the page."""
        violations = []
        
        try:
            # Discover interactive elements
            interactive_elements = await self._discover_interactive_elements(page)
            
            logger.info(f"Found {len(interactive_elements)} interactive elements")
            
            # Test each type of interactive element
            violations.extend(await self._test_tabs(page, interactive_elements.get('tabs', [])))
            violations.extend(await self._test_accordions(page, interactive_elements.get('accordions', [])))
            violations.extend(await self._test_modals(page, interactive_elements.get('modals', [])))
            violations.extend(await self._test_dropdowns(page, interactive_elements.get('dropdowns', [])))
            
        except Exception as e:
            logger.error(f"Interactive scanner error: {e}")
        
        return violations
    
    async def _discover_interactive_elements(self, page: Page) -> Dict[str, List[Dict]]:
        """Discover all interactive elements on the page."""
        
        elements = {
            'tabs': [],
            'accordions': [],
            'modals': [],
            'dropdowns': []
        }
        
        # Find tabs (role=tab, role=tablist)
        tabs = await page.locator('[role="tab"], .tab, [data-tab]').all()
        for tab in tabs:
            try:
                element_info = await self._get_element_info(tab)
                if element_info:
                    elements['tabs'].append(element_info)
            except:
                continue
        
        # Find accordions (role=button with aria-expanded)
        accordions = await page.locator('[role="button"][aria-expanded], .accordion-button, [data-accordion]').all()
        for accordion in accordions:
            try:
                element_info = await self._get_element_info(accordion)
                if element_info:
                    elements['accordions'].append(element_info)
            except:
                continue
        
        # Find modal triggers (data-modal, data-toggle="modal", etc.)
        modals = await page.locator('[data-modal], [data-toggle="modal"], [data-bs-toggle="modal"]').all()
        for modal in modals:
            try:
                element_info = await self._get_element_info(modal)
                if element_info:
                    elements['modals'].append(element_info)
            except:
                continue
        
        # Find dropdowns
        dropdowns = await page.locator('[role="button"][aria-haspopup], .dropdown-toggle, select').all()
        for dropdown in dropdowns:
            try:
                element_info = await self._get_element_info(dropdown)
                if element_info:
                    elements['dropdowns'].append(element_info)
            except:
                continue
        
        return elements
    
    async def _get_element_info(self, element: ElementHandle) -> Optional[Dict]:
        """Extract information about an element."""
        try:
            return await element.evaluate('''
                (el) => {
                    return {
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        classes: el.className || null,
                        role: el.getAttribute('role') || null,
                        ariaLabel: el.getAttribute('aria-label') || null,
                        ariaExpanded: el.getAttribute('aria-expanded') || null,
                        ariaControls: el.getAttribute('aria-controls') || null,
                        ariaHaspopup: el.getAttribute('aria-haspopup') || null,
                        text: el.textContent?.trim().substring(0, 50) || null,
                        selector: el.id ? `#${el.id}` : `.${el.className.split(' ')[0]}`
                    };
                }
            ''')
        except:
            return None
    
    async def _test_tabs(self, page: Page, tabs: List[Dict]) -> List[Violation]:
        """Test tab accessibility."""
        violations = []
        
        for tab in tabs:
            issues = []
            
            # Check for proper ARIA attributes
            if not tab.get('role') == 'tab':
                issues.append("Missing role='tab'")
            
            if not tab.get('ariaControls'):
                issues.append("Missing aria-controls attribute")
            
            if tab.get('ariaExpanded') is None and tab.get('role') == 'tab':
                issues.append("Missing aria-selected attribute (should indicate if tab is selected)")
            
            # Try to interact with the tab
            try:
                selector = tab['selector']
                element = page.locator(selector).first
                
                if await element.is_visible():
                    # Check if keyboard accessible
                    tabindex = await element.get_attribute('tabindex')
                    if tabindex and int(tabindex) < 0:
                        issues.append("Tab is not keyboard accessible (negative tabindex)")
                    
                    # Try clicking and check if panel appears
                    await element.click(timeout=2000)
                    await asyncio.sleep(0.3)
                    
                    # Check if associated panel is visible
                    controls_id = tab.get('ariaControls')
                    if controls_id:
                        panel = page.locator(f"#{controls_id}")
                        if not await panel.is_visible():
                            issues.append(f"Clicking tab does not show associated panel #{controls_id}")
            
            except Exception as e:
                logger.debug(f"Could not test tab interaction: {e}")
            
            if issues:
                violations.append(Violation(
                    id=f"interactive-tab-{tab['selector']}",
                    rule_id="interactive-tabs",
                    wcag_criteria=["4.1.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description=f"Tab '{tab.get('text', 'Unknown')}' has accessibility issues",
                    help_text="; ".join(issues),
                    help_url="https://www.w3.org/WAI/ARIA/apg/patterns/tabs/",
                    detected_by=[self.name],
                    instances=[ViolationInstance(
                        html=f"<{tab['tag']} id='{tab.get('id', '')}' class='{tab.get('classes', '')}'>",
                        selector=tab['selector'],
                        message="; ".join(issues)
                    )]
                ))
        
        return violations
    
    async def _test_accordions(self, page: Page, accordions: List[Dict]) -> List[Violation]:
        """Test accordion accessibility."""
        violations = []
        
        for accordion in accordions:
            issues = []
            
            # Check ARIA attributes
            if accordion.get('ariaExpanded') is None:
                issues.append("Missing aria-expanded attribute")
            
            if not accordion.get('ariaControls'):
                issues.append("Missing aria-controls attribute")
            
            # Try to interact
            try:
                selector = accordion['selector']
                element = page.locator(selector).first
                
                if await element.is_visible():
                    # Get initial state
                    initial_expanded = await element.get_attribute('aria-expanded')
                    
                    # Click to toggle
                    await element.click(timeout=2000)
                    await asyncio.sleep(0.3)
                    
                    # Check if state changed
                    new_expanded = await element.get_attribute('aria-expanded')
                    if initial_expanded == new_expanded:
                        issues.append("aria-expanded does not toggle on click")
            
            except Exception as e:
                logger.debug(f"Could not test accordion interaction: {e}")
            
            if issues:
                violations.append(Violation(
                    id=f"interactive-accordion-{accordion['selector']}",
                    rule_id="interactive-accordions",
                    wcag_criteria=["4.1.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description=f"Accordion '{accordion.get('text', 'Unknown')}' has accessibility issues",
                    help_text="; ".join(issues),
                    help_url="https://www.w3.org/WAI/ARIA/apg/patterns/accordion/",
                    detected_by=[self.name],
                    instances=[ViolationInstance(
                        html=f"<{accordion['tag']}>",
                        selector=accordion['selector'],
                        message="; ".join(issues)
                    )]
                ))
        
        return violations
    
    async def _test_modals(self, page: Page, modals: List[Dict]) -> List[Violation]:
        """Test modal/dialog accessibility."""
        violations = []
        
        for modal in modals:
            issues = []
            
            # Try to open modal
            try:
                selector = modal['selector']
                trigger = page.locator(selector).first
                
                if await trigger.is_visible():
                    await trigger.click(timeout=2000)
                    await asyncio.sleep(0.5)
                    
                    # Check for modal with role=dialog
                    dialog = page.locator('[role="dialog"], [role="alertdialog"], .modal.show').first
                    
                    if await dialog.is_visible(timeout=1000):
                        # Check for aria-modal
                        aria_modal = await dialog.get_attribute('aria-modal')
                        if aria_modal != 'true':
                            issues.append("Modal missing aria-modal='true'")
                        
                        # Check for aria-labelledby or aria-label
                        aria_label = await dialog.get_attribute('aria-label')
                        aria_labelledby = await dialog.get_attribute('aria-labelledby')
                        if not aria_label and not aria_labelledby:
                            issues.append("Modal missing accessible name (aria-label or aria-labelledby)")
                        
                        # Check for close button
                        close_button = dialog.locator('button:has-text("Close"), button[aria-label*="close" i], .close').first
                        if not await close_button.count() > 0:
                            issues.append("Modal missing visible close button")
                        
                        # Close modal (try Escape key)
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(0.3)
            
            except Exception as e:
                logger.debug(f"Could not test modal interaction: {e}")
            
            if issues:
                violations.append(Violation(
                    id=f"interactive-modal-{modal['selector']}",
                    rule_id="interactive-modals",
                    wcag_criteria=["2.1.2", "4.1.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description=f"Modal trigger '{modal.get('text', 'Unknown')}' has accessibility issues",
                    help_text="; ".join(issues),
                    help_url="https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/",
                    detected_by=[self.name],
                    instances=[ViolationInstance(
                        html=f"<{modal['tag']}>",
                        selector=modal['selector'],
                        message="; ".join(issues)
                    )]
                ))
        
        return violations
    
    async def _test_dropdowns(self, page: Page, dropdowns: List[Dict]) -> List[Violation]:
        """Test dropdown menu accessibility."""
        violations = []
        
        for dropdown in dropdowns:
            issues = []
            
            # Check ARIA attributes
            if dropdown.get('tag') != 'select':  # Native select is fine
                if not dropdown.get('ariaHaspopup'):
                    issues.append("Custom dropdown missing aria-haspopup attribute")
                
                if dropdown.get('ariaExpanded') is None:
                    issues.append("Custom dropdown missing aria-expanded attribute")
            
            if issues:
                violations.append(Violation(
                    id=f"interactive-dropdown-{dropdown['selector']}",
                    rule_id="interactive-dropdowns",
                    wcag_criteria=["4.1.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description=f"Dropdown '{dropdown.get('text', 'Unknown')}' has accessibility issues",
                    help_text="; ".join(issues),
                    help_url="https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/",
                    detected_by=[self.name],
                    instances=[ViolationInstance(
                        html=f"<{dropdown['tag']}>",
                        selector=dropdown['selector'],
                        message="; ".join(issues)
                    )]
                ))
        
        return violations
