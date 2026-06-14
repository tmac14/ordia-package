# UI / UX implementation checklist

**Task:** {{TASK_ID}} · **Intent:** {{INTENT_ID}}

## Objective

{{OBJECTIVE}}

## UI scope

- Components and layout only unless task packet explicitly allows logic changes
- Match design tokens / existing component library
- Responsive breakpoints: mobile, tablet, desktop

## Accessibility

- Keyboard navigation and focus order
- Color contrast (WCAG AA minimum)
- Screen reader labels for interactive controls
- Meaningful alt text for non-decorative images

## UX quality

- Empty, loading, and error states
- Copy clarity and action labels
- No dead-end flows without recovery path

## Validation

{{BODY_HINT}}

Run mandatory visual/behavioral checks from task packet. Prefer `ordia prompt emit --intent qa --task {{TASK_ID}}` before closure.

## Deliverable

{{DELIVERABLE}}
